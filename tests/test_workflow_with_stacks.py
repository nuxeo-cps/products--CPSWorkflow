#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Julien Anguenot <ja@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
"""Tests for the CPS Workflow Tool and CPS Worflow with stacks

This test case implements a full delegation / validation workflow and covers
the whole stack workflow API.
"""

import os, sys
from types import DictType
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
ZopeTestCase.installProduct('CMFCore')
ZopeTestCase.installProduct('CMFDefault')
ZopeTestCase.installProduct('MailHost')

ZopeTestCase.installProduct('CPSCore')
ZopeTestCase.installProduct('CPSWorkflow')

import Zope
import unittest

from Acquisition import aq_parent, aq_inner

from Products.CPSCore.CPSBase import CPSBaseFolder as Folder
from Products.CMFDefault.Portal import manage_addCMFSite

from Products.CMFCore.utils import getToolByName

from Products.CPSWorkflow.workflow import WorkflowDefinition
from Products.CPSWorkflow.workflow import TRIGGER_USER_ACTION

from Products.CPSWorkflow.configuration import addConfiguration

from Products.CPSWorkflow.workflowtool import Config_id

from Products.CPSWorkflow.transitions import *
from Products.CPSWorkflow.states import *

from Products.CPSWorkflow.transitions import \
     transition_behavior_export_dict as tbdict

from Products.CPSWorkflow.basicstackdefinitions import SimpleStackDefinition, \
     HierarchicalStackDefinition

from dummy import DummyContent

portal_name = 'portal'

class WorkflowToolTests(ZopeTestCase.PortalTestCase):
    """Test CPS Workflow Tool and CPS Workflow stacks """

    def getPortal(self):
        if not hasattr(self.app, portal_name):
            manage_addCMFSite(self.app,
                              portal_name)
        return self.app[portal_name]

    #####################################################################

    def afterSetUp(self):
        try:
            self.login('manager')
        except AttributeError:
            # CMF
            uf = self.portal.acl_users
            uf._doAddUser('manager', '', ['Manager'], [])
            self.login('manager')
        # Set portal
        self.portal = self.getPortal()

        # Set workflow tool
        self.portal.manage_delObjects(['portal_workflow'])
        self.portal.manage_addProduct['CPSWorkflow'].manage_addTool(
            'CPS Workflow Tool')

        self.ttool = getToolByName(self.portal, 'portal_types')
        self.wftool = getToolByName(self.portal, 'portal_workflow')

        # Proxy / repo tools
        self.portal.manage_addProduct['CPSCore'].manage_addTool(
            'CPS Proxies Tool')
        self.portal.manage_addProduct['CPSCore'].manage_addTool(
            'CPS Repository Tool')

        # Set the CPS Membership tool for group support
        self.portal.manage_delObjects(['portal_membership'])
        self.portal.manage_addProduct['CPSCore'].manage_addTool(
            'CPS Membership Tool')

        # Set the URL tool
        self.portal.manage_delObjects(['portal_url'])
        self.portal.manage_addProduct['CMFCore'].manage_addTool(
            'CMF URL Tool')

        self.assert_(getToolByName(self.portal, 'portal_url') is not None)

        # Set workflow definitions that we gonna test
        self._makeWorkflows()

        # Put a folder and an object here
        self._makeTree()

    ####################################################################

    def _makeTree(self):
        f = Folder('f')
        self.portal._setObject(f.id, f)
        f = self.portal.f
        dummy = DummyContent('dummy')

        # Set the global workflow chain
        self.wftool.setChainForPortalTypes(('File',), ('wf',))

        # Setup placeful workflows
        addConfiguration(f)
        config = getattr(f, Config_id)
        config.setChain('File', ('wf',))

        # Create a dummy File objects
        self.wftool.invokeFactoryFor(f, 'File','dummy')

    ######################################################################

    def _setStackDefinitionsFor(self, s):

        # Add Pilots stack
        s.addStackDefinition(
            'Hierarchical Stack Definition',
            'Hierarchical Stack',
            'Pilots',
            manager_stack_ids=['Associates', 'Observers'],
            )

        stackdef = s.getStackDefinitionFor('Pilots')

        # Add expressions
        stackdef.addManagedRole('WorkspaceManager',
                                "python:level == stack.getCurrentLevel() and 1 or nothing",
                                master_role=1)
        stackdef.addManagedRole('WorkspaceMember',
                                    "python:level < stack.getCurrentLevel() and 1 or nothing",
                                    master_role=0)
        stackdef.addManagedRole('WorkspaceReader',
                                "python:level > stack.getCurrentLevel() and 1 or nothing",
                                master_role=0)

        # Add Associates stack
        s.addStackDefinition(
            'Simple Stack Definition',
            'Simple Stack',
            'Associates',
            manager_stack_ids=['Observers']
            )

        stackdef = s.getStackDefinitionFor('Associates')
        # Add expressions
        stackdef.addManagedRole('WorkspaceMember',
                                "python:1",
                                master_role=1)

        # Add Observers stack
        s.addStackDefinition(
            'Simple Stack Definition',
            'Simple Stack',
            'Observers',
            )

        stackdef = s.getStackDefinitionFor('Observers')
        # Add expressions
        stackdef.addManagedRole('WorkspaceMember',
                                "python:1",
                                master_role=1)

    def _makeWorkflows(self):

        #
        # WORKFLOW DEFINITION
        #

        wftool = self.wftool

        id = 'wf'
        wf = WorkflowDefinition(id)

        if id in wftool.objectIds():
            wftool._delObjects([id])

        wftool._setObject(id, wf)
        wf = wftool.wf

        #
        # STATES
        #

        wf.states.addState('delegating')
        wf.states.addState('writing')
        wf.states.addState('validating')
        wf.states.addState('closed')

        wf.states.setInitialState('delegating')

        # Check if they do exist
        states = list(wf.states.objectIds())
        states.sort()
        self.assertEqual(tuple(states), ('closed',
                                         'delegating',
                                         'validating',
                                         'writing',
                                         ))

        # Add behaviors to states
        s = wf.states.get('delegating')
        s.setProperties(
            title='Delegating',
            description='Delegating',
            state_behaviors = (STATE_BEHAVIOR_PUSH_DELEGATEES,
                               STATE_BEHAVIOR_POP_DELEGATEES,
                               STATE_BEHAVIOR_WORKFLOW_UP,
                               STATE_BEHAVIOR_WORKFLOW_LOCK,
                               STATE_BEHAVIOR_WORKFLOW_UNLOCK,
                               STATE_BEHAVIOR_WORKFLOW_RESET,),
            push_on_workflow_variable = ['Pilots', 'Associates', 'Observers'],
            pop_on_workflow_variable = ['Pilots', 'Associates', 'Observers'],
            workflow_up_on_workflow_variable = ['Pilots'],
            workflow_lock_on_workflow_variable = ['Pilots', 'Associates',
                                                  'Observers'],
            workflow_unlock_on_workflow_variable = ['Pilots', 'Associates',
                                                    'Observers'],
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)


        self._setStackDefinitionsFor(s)

        s = wf.states.get('writing')
        s.setProperties(
            title='Writing',
            description='Writing',
            state_behaviors = (STATE_BEHAVIOR_WORKFLOW_LOCK,
                               STATE_BEHAVIOR_WORKFLOW_UNLOCK,
                               STATE_BEHAVIOR_RETURNED_UP_HIERARCHY,
                               STATE_BEHAVIOR_WORKFLOW_RESET,),
            workflow_lock_on_workflow_variable = ['Pilots', 'Associates',
                                                  'Observers'],
            workflow_unlock_on_workflow_variable = ['Pilots', 'Associates',
                                                    'Observers'],
            returned_up_hierarchy_on_workflow_variable = ['Pilots'],
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)


        s = wf.states.get('validating')
        s.setProperties(
            title='Validating',
            description='Validating',
            state_behaviors = (STATE_BEHAVIOR_PUSH_DELEGATEES,
                               STATE_BEHAVIOR_POP_DELEGATEES,
                               STATE_BEHAVIOR_WORKFLOW_DOWN,
                               STATE_BEHAVIOR_WORKFLOW_LOCK,
                               STATE_BEHAVIOR_WORKFLOW_UNLOCK,
                               STATE_BEHAVIOR_WORKFLOW_RESET,),
            push_on_workflow_variable = ['Pilots'],
            pop_on_workflow_variable = ['Pilots'],
            workflow_down_on_workflow_variable = ['Pilots'],
            workflow_lock_on_workflow_variable = ['Pilots', 'Associates',
                                                  'Observers'],
            workflow_unlock_on_workflow_variable = ['Pilots', 'Associates',
                                                    'Observers'],
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)

        s = wf.states.get('closed')
        s.setProperties(
            title='Closed',
            description='Closed',
            state_behaviors = (STATE_BEHAVIOR_WORKFLOW_UNLOCK,
                               STATE_BEHAVIOR_WORKFLOW_RESET,),
            workflow_unlock_on_workflow_variable = ['Pilots', 'Associates',
                                                    'Observers'],
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)


        #
        # TRANSITIONS
        #

        # Initial transition
        wf.transitions.addTransition('create')
        t = wf.transitions.get('create')
        t.setProperties('title',
                        'delegating',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(TRANSITION_INITIAL_CREATE,
                                             ))

        # Delegate
        wf.transitions.addTransition('delegate')
        t = wf.transitions.get('delegate')
        t.setProperties('title',
                        'delegating',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(
            TRANSITION_BEHAVIOR_PUSH_DELEGATEES,
            ),
                        push_on_workflow_variable=['Pilots'],
                        )

        # to_writing
        wf.transitions.addTransition('to_writing')
        t = wf.transitions.get('to_writing')
        t.setProperties('title',
                        'to_writing',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=())

        # Validate
        wf.transitions.addTransition('validate')
        t = wf.transitions.get('validate')
        t.setProperties('title',
                        'delegate',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=('behavior_push_delegatees',
                                             'behavior_pop_delegatees',
                                             'behavior_workflow_down',
                                             'behavior_workflow_lock',
                                             'behavior_workflow_unlock',
                                             'behavior_workflow_reset'))

        # to_validate
        wf.transitions.addTransition('to_validate')
        t = wf.transitions.get('to_validate')
        t.setProperties('title',
                        'to_validate',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(
            'behavior_workflow_lock',
            'behavior_workflow_unlock',
            'behavior_return_up_delegatees_hierarchy',
            'behavior_workflow_reset'))

        # Close
        wf.transitions.addTransition('close')
        t = wf.transitions.get('close')
        t.setProperties('title',
                        'close',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=('behavior_workflow_unlock'))


        # Check if they do exist
        transitions = wf.transitions.objectIds()
        transitions.sort()
        self.assertEqual(tuple(transitions), ('close',
                                              'create',
                                              'delegate',
                                              'to_validate',
                                              'to_writing',
                                              'validate',
                                              ))

        #
        # Variables
        #

        for v in ('action',
                  'actor',
                  'comments',
                  'review_history',
                  'time',
                  'dest_container',
                  ):
            wf.variables.addVariable(v)

        vdef = wf.variables['action']
        vdef.setProperties(description='The last transition',
                           default_expr='transition/getId|nothing',
                           for_status=1, update_always=1)

        vdef = wf.variables['actor']
        vdef.setProperties(description='The ID of the user who performed '
                           'the last transition',
                           default_expr='user/getId',
                           for_status=1, update_always=1)

        vdef = wf.variables['comments']
        vdef.setProperties(description='Comments about the last transition',
                           default_expr="python:state_change.kwargs.get('comment',\
                           '')",
                           for_status=1, update_always=1)

        vdef = wf.variables['review_history']
        vdef.setProperties(description='Provides access to workflow history',
                           default_expr="state_change/getHistory",
                           props={'guard_permissions':'',
                                  'guard_roles':'Manager; WorkspaceManager; \
                                  WorkspaceMember; WorkspaceReader; Member',
                                  'guard_expr':''})

        vdef = wf.variables['time']
        vdef.setProperties(description='Time of the last transition',
                           default_expr="state_change/getDateTime",
                           for_status=1, update_always=1)

        vdef = wf.variables['dest_container']
        vdef.setProperties(description='Destination container for the last \
        paste/publish',
                           default_expr="python:state_change.kwargs.get(\
                           'dest_container', '')",
                           for_status=1, update_always=1)

        wf.variables.setStateVar('review_state')

        #
        # Set transitions on states
        #

        s = wf.states.get('delegating')
        s.transitions += ('delegate',)

        #
        # Workflow for the container
        #

        id2 = 'wf2'
        wf2 = WorkflowDefinition(id2)
        wftool._setObject(id2, wf2)

        # A a state
        wf2.states.addState('work')
        s = wf2.states.get('work')
        s.transitions = ('create',)

        # Initial transition
        wf2.transitions.addTransition('create')
        t = wf2.transitions.get('create')
        t.setProperties('title',
                        'create',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(tbdict[TRANSITION_INITIAL_CREATE],
                                             ))

        # Allow sub-content creation
        wf2.transitions.addTransition('create_content')
        t = wf2.transitions.get('create_content')
        t.setProperties('title',
                        'create',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(tbdict[TRANSITION_ALLOWSUB_CREATE],
                                             ))
    ###################################################################
    # TESTS STARTS HERE
    ###################################################################

    def test_wftool_api_at_initialization(self):

        #
        # TEST WORKFLOW TOOL API RELATED TO WORKFLOW STACKS
        #

        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')

        # Test content / wftool fixtures
        self.assertEqual(wftool.getChainFor(content), ('wf',))
        self.assertEqual(len(wftool.getWorkflowsFor(content)),  1)
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #
        #  def getStackDefinitionsFor(self, ob)
        #

        stackdefs = wftool.getStackDefinitionsFor(content)

        # Test returned structure
        self.assert_(isinstance(stackdefs, DictType))
        self.assertNotEqual(stackdefs, {})

        # Test fixtures of stackdefs
        keys = stackdefs.keys()
        keys.sort()
        self.assert_(len(keys) == 3)
        self.assertEqual(keys, ['Associates', 'Observers', 'Pilots'])

        self.assertNotEqual(stackdefs['Associates'], None)
        self.assertNotEqual(stackdefs['Observers'], None)
        self.assertNotEqual(stackdefs['Pilots'], None)

        self.assert_(isinstance(stackdefs['Pilots'],
                                HierarchicalStackDefinition))
        self.assert_(isinstance(stackdefs['Associates'],
                                SimpleStackDefinition))
        self.assert_(isinstance(stackdefs['Observers'],
                                SimpleStackDefinition))


        #
        # getStackDefinitionFor(self, ob, wf_var_id='')
        #

        assos = wftool.getStackDefinitionFor(content, 'Associates')
        obs = wftool.getStackDefinitionFor(content, 'Observers')
        pilots = wftool.getStackDefinitionFor(content, 'Pilots')

        self.assert_(isinstance(assos,
                                SimpleStackDefinition))
        self.assert_(isinstance(obs,
                                SimpleStackDefinition))
        self.assert_(isinstance(pilots,
                                HierarchicalStackDefinition))
        self.assertNotEqual(assos, None)
        self.assertNotEqual(obs, None)
        self.assertNotEqual(pilots, None)

        # Test consistency
        self.assertEqual( wftool.getStackDefinitionFor(content, 'Associates'),
                          wftool.getStackDefinitionsFor(content)['Associates'])
        self.assertEqual( wftool.getStackDefinitionFor(content, 'Observers'),
                          wftool.getStackDefinitionsFor(content)['Observers'])
        self.assertEqual( wftool.getStackDefinitionFor(content, 'Pilots'),
                          wftool.getStackDefinitionsFor(content)['Pilots'])

        # Stack doesn't exist

        self.assertEqual(wftool.getStackDefinitionFor(content), None)
        self.assertEqual(wftool.getStackDefinitionFor(content, 'Pas bien'),
                         None)

        #
        # getDelegateesDataStructures(self, ob)
        # Note the status is not yet set for stacks
        #

        ds = wftool.getStacks(content)
        self.assert_(isinstance(ds, DictType))
        keys = ds.keys()
        keys.sort()
        self.assert_(len(keys) == 3)
        self.assertEqual(keys, ['Associates', 'Observers', 'Pilots'])

        # it's initialized within wftool._changeStatusOf()
        for v in ds.values():
            self.assertNotEqual(v, None)

        #
        # def getDelegateesDataStructureFor(self, ob, stack_id)
        #

        ds_assos = wftool.getStackFor(content, 'Associates')
        ds_obs = wftool.getStackFor(content, 'Observers')
        ds_pilots = wftool.getStackFor(content, 'Pilots')

        # it's initialized within wftool._changeStatusOf()
        self.assertNotEqual(ds_assos, None)
        self.assertNotEqual(ds_obs, None)
        self.assertNotEqual(ds_pilots, None)

        # concistency
        self.assertEqual(wftool.getStackFor(content, 'Associates'),
                         wftool.getStacks(content)['Associates'])
        self.assertEqual(wftool.getStackFor(content, 'Observers'),
                         wftool.getStacks(content)['Observers'])

    def test_current_state(self):

        #
        # Here, let's check the current state props
        #

        wftool = self.wftool
        content = getattr(self.portal.f, 'dummy')

        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        # Check current state fixtures
        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        # Check stackdefs
        stackdefs = current_state.getStackDefinitions()
        keys = stackdefs.keys()
        keys.sort()
        self.assert_(isinstance(stackdefs, DictType))
        self.assertEqual(keys, ['Associates', 'Observers', 'Pilots'])
        self.assert_(isinstance(stackdefs['Associates'],
                                SimpleStackDefinition))
        self.assert_(isinstance(stackdefs['Observers'],
                                SimpleStackDefinition))
        self.assert_(isinstance(stackdefs['Pilots'],
                                HierarchicalStackDefinition))

        # Check consistency
        self.assertEqual(current_state.getStackDefinitionFor('Associates'),
                         stackdefs['Associates'])
        self.assertEqual(current_state.getStackDefinitionFor('Observers'),
                         stackdefs['Observers'])
        self.assertEqual(current_state.getStackDefinitionFor('Pilots'),
                         stackdefs['Pilots'])

        # Check behaviors given this workflow definition
        behaviors = current_state.state_behaviors
        self.assertEqual(behaviors, (STATE_BEHAVIOR_PUSH_DELEGATEES,
                                     STATE_BEHAVIOR_POP_DELEGATEES,
                                     STATE_BEHAVIOR_WORKFLOW_UP,
                                     STATE_BEHAVIOR_WORKFLOW_LOCK,
                                     STATE_BEHAVIOR_WORKFLOW_UNLOCK,
                                     STATE_BEHAVIOR_WORKFLOW_RESET,))
        self.assertEqual(current_state.push_on_workflow_variable,
                         ['Pilots', 'Associates', 'Observers'])
        self.assertEqual(current_state.pop_on_workflow_variable,
                         ['Pilots', 'Associates', 'Observers'])
        self.assertEqual(current_state.workflow_up_on_workflow_variable,
                         ['Pilots'])
        self.assertEqual(current_state.workflow_lock_on_workflow_variable,
                         ['Pilots', 'Associates','Observers'])
        self.assertEqual(current_state.workflow_unlock_on_workflow_variable,
                        ['Pilots', 'Associates', 'Observers'])
        self.assertEqual(current_state.workflow_reset_on_workflow_variable,
                         ['Pilots', 'Associates', 'Observers'],)

        #
        # Test possible transitions
        #

        allowed_transitions = current_state.getTransitions()
        # Not yet initialized
        self.assertEqual(allowed_transitions, ('delegate',))

    def test_pilots_hierarchical_alone(self):

        wftool = self.wftool
        content = getattr(self.portal.f, 'dummy')

        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        # Check current state fixtures
        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        # Check stack intialization
        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assert_(pstacks is not None)

        #
        # Delegate toto
        #

        wftool.doActionFor(content, 'delegate',
                           current_wf_var_id='Pilots',
                           member_ids=['toto'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent())
        self.assertEqual({0:['toto']}, pstacks.getStackContent())

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef.listLocalRoles(pstacks))
        self.assertEqual(pstackdef.listLocalRoles(pstacks),
                         {'toto': ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')
        # It's been updated for next time
        self.assertEqual(flrm,
                         {'toto': ('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k == 'user:toto':
                self.assert_('WorkspaceManager' in v)

        # Manager can't manage the stack
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        #
        # Delegate tata
        #

        wftool.doActionFor(content, 'delegate',
                           current_wf_var_id='Pilots',
                           member_ids=['tata'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent())
        self.assertEqual({0:['toto', 'tata']}, pstacks.getStackContent())

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef.listLocalRoles(pstacks))
        self.assertEqual(pstackdef.listLocalRoles(pstacks),
                         {'toto': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm,
                         {'toto': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',)},
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:toto', 'user:tata',):
                self.assert_('WorkspaceManager' in v)

        # Manager can't manage the stack
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        #
        # Delegate Manager
        #

        wftool.doActionFor(content, 'delegate',
                           current_wf_var_id='Pilots',
                           member_ids=['manager'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent())
        self.assertEqual({0:['toto', 'tata', 'manager']},
                         pstacks.getStackContent())

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef.listLocalRoles(pstacks))
        self.assertEqual(pstackdef.listLocalRoles(pstacks),
                         {'toto': ('WorkspaceManager',),
                          'manager': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',),
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm,
                         {'toto': ('WorkspaceManager',),
                          'manager': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',)},
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:toto', 'user:tata',):
                self.assert_('WorkspaceManager' in v)

        # Manager can't manage the stack
        self.assert_(wftool.canManageStack(content, 'Pilots'))
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WorkflowToolTests))
    return suite

if __name__ == '__main__':
    framework()
