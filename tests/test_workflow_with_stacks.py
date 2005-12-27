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
ZopeTestCase.installProduct('CPSWorkflow')
ZopeTestCase.installProduct('ZCTextIndex')

# XXX Break those dependencies
ZopeTestCase.installProduct('CPSCore')
ZopeTestCase.installProduct('CPSDefault')
ZopeTestCase.installProduct('CPSUserFolder')

import unittest

from Acquisition import aq_parent, aq_inner

from AccessControl import Unauthorized
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager

from Products.CPSCore.CPSBase import CPSBaseFolder as Folder

from Products.CMFDefault.Portal import manage_addCMFSite

from Products.CMFCore.utils import getToolByName

from Products.CPSWorkflow.workflow import WorkflowDefinition
from Products.CPSWorkflow.workflow import TRIGGER_USER_ACTION

from Products.CPSWorkflow.configuration import addConfiguration

from Products.CPSWorkflow.workflowtool import Config_id

from Products.CPSWorkflow.constants import *

from Products.CPSWorkflow.basicstackdefinitions import SimpleStackDefinition
from Products.CPSWorkflow.basicstackdefinitions import \
     HierarchicalStackDefinition

from Products.CPSWorkflow.basicstacks import SimpleStack
from Products.CPSWorkflow.basicstacks import HierarchicalStack

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

        # Add a user with groups
        self.portal.manage_delObjects(['acl_users'])
        self.portal.manage_addProduct['CPSUserFolder'].addUserFolderWithGroups(self.portal)
        self.assert_('acl_users' in self.portal.objectIds())
        uf = self.portal.acl_users
        uf._doAddUser('manager', '', ['Manager'], [])

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
        self.portal.manage_addProduct['CPSDefault'].manage_addTool(
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

        # Create users (as members)
        aclu = self.portal.acl_users
        aclu._doAddUser('toto', '','', ['Member'],)
        aclu._doAddUser('tata', '','', ['Member'],)

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
        self.wftool.invokeFactoryFor(f, 'File', 'dummy')

    ######################################################################

    def _setStackDefinitionsFor(self, s):

        # Add Pilots stack
        s.addStackDefinition(
            'Hierarchical Stack Definition',
            'Hierarchical Stack',
            'Pilots',
            managed_role_exprs= {'WorkspaceManager': "python:level == stack.getCurrentLevel() and 1 or nothing",
                                 'WorkspaceMember' : "python:level < stack.getCurrentLevel() and 1 or nothing",
                                 'WorkspaceReader' : "python:level > stack.getCurrentLevel() and 1 or nothing",
                                 },
            manager_stack_ids=['Associates', 'Observers'],
            empty_stack_manage_guard={'guard_roles':'Owner; WorkspaceManager'},
            )

        # Add Associates stack
        s.addStackDefinition(
            'Simple Stack Definition',
            'Simple Stack',
            'Associates',
            managed_role_exprs={'WorkspaceMember': 'python:1',
                                },
            empty_stack_manage_guard={'guard_roles':'Owner; WorkspaceMember'},
            manager_stack_ids=['Observers']
            )

        # Add Observers stack
        s.addStackDefinition(
            'Simple Stack Definition',
            'Simple Stack',
            'Observers',
            managed_role_exprs={'WorkspaceReader': 'python:1',
                                },
            empty_stack_manage_guard={'guard_roles':'Owner; WorkspaceReader'},
            )

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
                               STATE_BEHAVIOR_WORKFLOW_RESET,),
            stackdefs={'Pilots': {'stackdef_type': 'Hierarchical Stack Definition',
                                  'stack_type'   : 'Hierarchical Stack',
                                  'var_id'    : 'Pilots',
                                  'managed_role_exprs' :{'WorkspaceManager': "python:level == stack.getCurrentLevel() and 1 or nothing",
                                                         'WorkspaceMember' : "python:level < stack.getCurrentLevel() and 1 or nothing",
                                                         'WorkspaceReader' : "python:level > stack.getCurrentLevel() and 1 or nothing",
                                                         },
                                  'empty_stack_manage_guard':{'guard_roles':'Owner; WorkspaceManager'},
                                  'manager_stack_ids':['Associates', 'Observers'],
                                  },
                       'Associates': {'stackdef_type' : 'Simple Stack Definition',
                                      'stack_type': 'Simple Stack',
                                      'var_id':'Associates',
                                      'managed_role_exprs':{'WorkspaceMember': 'python:1',},
                                      'empty_stack_manage_guard':{'guard_roles':'Owner; WorkspaceMember'},
                                      'manager_stack_ids':['Observers'],
                                      },
                       'Observers': {'stackdef_type' : 'Simple Stack Definition',
                                     'stack_type': 'Simple Stack',
                                     'var_id':'Observers',
                                     'managed_role_exprs':{'WorkspaceReader': 'python:1',},
                                     'empty_stack_manage_guard':{'guard_roles':'Owner; WorkspaceReader'},
                                     'manager_stack_ids':[],
                                     },
                       },
            push_on_workflow_variable = ['Pilots', 'Associates', 'Observers'],
            pop_on_workflow_variable = ['Pilots', 'Associates', 'Observers'],
            workflow_up_on_workflow_variable = ['Pilots'],
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)


        #
        # test creation success
        #

        stackdefs = s.getStackDefinitions()
        self.assert_(len(stackdefs)==3)
        self.assertNotEqual(s.getStackDefinitionFor('Pilots'), None)
        self.assertNotEqual(s.getStackDefinitionFor('Associates'), None)
        self.assertNotEqual(s.getStackDefinitionFor('Observers'), None)

        s = wf.states.get('writing')
        s.setProperties(
            title='Writing',
            description='Writing',
            stackdefs={'Pilots': {'stackdef_type': 'Hierarchical Stack Definition',
                                  'stack_type'   : 'Hierarchical Stack',
                                  'var_id'    : 'Pilots',
                                  'managed_role_exprs' :{'WorkspaceManager': "python:level == stack.getCurrentLevel() and 1 or nothing",
                                                         'WorkspaceMember' : "python:level < stack.getCurrentLevel() and 1 or nothing",
                                                         'WorkspaceReader' : "python:level > stack.getCurrentLevel() and 1 or nothing",
                                                         },
                                  'empty_stack_manage_guard':{'guard_roles':'Owner; WorkspaceManager'},
                                  'manager_stack_ids':['Associates', 'Observers'],
                                  },
                       'Associates': {'stackdef_type' : 'Simple Stack Definition',
                                      'stack_type': 'Simple Stack',
                                      'var_id':'Associates',
                                      'managed_role_exprs':{'WorkspaceMember': 'python:1',},
                                      'empty_stack_manage_guard':{'guard_roles':'Owner; WorkspaceMember'},
                                      'manager_stack_ids':['Observers'],
                                      },
                       'Observers': {'stackdef_type' : 'Simple Stack Definition',
                                     'stack_type': 'Simple Stack',
                                     'var_id':'Observers',
                                     'managed_role_exprs':{'WorkspaceReader': 'python:1',},
                                     'empty_stack_manage_guard':{'guard_roles':'Owner; WorkspaceReader'},
                                     'manager_stack_ids':[],
                                     },
                       },
            state_behaviors = (STATE_BEHAVIOR_WORKFLOW_RESET,),
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)

        #
        # test creation success
        #

        stackdefs = s.getStackDefinitions()
        self.assert_(len(stackdefs)==3)
        self.assertNotEqual(s.getStackDefinitionFor('Pilots'), None)
        self.assertNotEqual(s.getStackDefinitionFor('Associates'), None)
        self.assertNotEqual(s.getStackDefinitionFor('Observers'), None)


        s = wf.states.get('validating')
        s.setProperties(
            title='Validating',
            description='Validating',
            state_behaviors = (STATE_BEHAVIOR_PUSH_DELEGATEES,
                               STATE_BEHAVIOR_POP_DELEGATEES,
                               STATE_BEHAVIOR_WORKFLOW_DOWN,
                               STATE_BEHAVIOR_WORKFLOW_RESET,),
            push_on_workflow_variable = ['Pilots'],
            pop_on_workflow_variable = ['Pilots'],
            workflow_down_on_workflow_variable = ['Pilots'],
            workflow_reset_on_workflow_variable = ['Pilots', 'Associates',
                                                   'Observers'],)

        s = wf.states.get('closed')
        s.setProperties(
            title='Closed',
            description='Closed',
            state_behaviors = (STATE_BEHAVIOR_WORKFLOW_RESET,),
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
                        push_on_workflow_variable=['Pilots', 'Associates'],
                        )

        # Reset
        wf.transitions.addTransition('reset')
        t = wf.transitions.get('reset')
        t.setProperties('title',
                        '',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(
            TRANSITION_BEHAVIOR_WORKFLOW_RESET,
            ),
                        workflow_reset_on_workflow_variable=['Pilots',
                                                             'Associates'],
                        )

        # remove_delegate
        wf.transitions.addTransition('remove_delegate')
        t = wf.transitions.get('remove_delegate')
        t.setProperties('title',
                        'delegating',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(
            TRANSITION_BEHAVIOR_POP_DELEGATEES,
            ),
                        pop_on_workflow_variable=['Pilots'],
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
                        'delegating',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(
            TRANSITION_BEHAVIOR_WORKFLOW_UP,),
                        workflow_up_on_workflow_variable=['Pilots'],
                        )

        # to_validate
        wf.transitions.addTransition('to_validate')
        t = wf.transitions.get('to_validate')
        t.setProperties('title',
                        'to_validate',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(
            'behavior_workflow_reset'))

        # Close
        wf.transitions.addTransition('close')
        t = wf.transitions.get('close')
        t.setProperties('title',
                        'close',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=())


        # Check if they do exist
        transitions = wf.transitions.objectIds()
        transitions.sort()
        self.assertEqual(tuple(transitions), ('close',
                                              'create',
                                              'delegate',
                                              'remove_delegate',
                                              'reset',
                                              'to_validate',
                                              'to_writing',
                                              'validate',
                                              ))

        # silent
        wf.transitions.addTransition('silent')
        t = wf.transitions.get('silent')
        t.setProperties('title',
                        '',
                        trigger_type=TRIGGER_USER_ACTION,
                        )
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
        s.transitions += ('delegate', 'remove_delegate', 'silent', 'reset',
                          'validate')

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
                        transition_behavior=(TRANSITION_INITIAL_CREATE,))

        # Allow sub-content creation
        wf2.transitions.addTransition('create_content')
        t = wf2.transitions.get('create_content')
        t.setProperties('title',
                        'create',
                        trigger_type=TRIGGER_USER_ACTION,
                        transition_behavior=(TRANSITION_ALLOWSUB_CREATE,))

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
                                     STATE_BEHAVIOR_WORKFLOW_RESET,))
        self.assertEqual(current_state.push_on_workflow_variable,
                         ['Pilots', 'Associates', 'Observers'])
        self.assertEqual(current_state.pop_on_workflow_variable,
                         ['Pilots', 'Associates', 'Observers'])
        self.assertEqual(current_state.workflow_up_on_workflow_variable,
                         ['Pilots'])
        self.assertEqual(current_state.workflow_reset_on_workflow_variable,
                         ['Pilots', 'Associates', 'Observers'],)

        #
        # Test possible transitions
        #

        allowed_transitions = current_state.getTransitions()
        # Not yet initialized
        self.assertEqual(allowed_transitions, ('delegate', 'remove_delegate',
                                               'silent', 'reset', 'validate'))

    def test_stack_hierarchical_behavior_with_users_no_levels_one_level(self):

        self.login('manager')

        wftool = self.wftool
        content = getattr(self.portal.f, 'dummy')

        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assert_(pstacks is not None)

        #########################################
        # Test with other members not granted
        #########################################

        self.login('toto')
        stack = wftool.getStackFor(content, 'Pilots')
        #raise str(getSecurityManager().validate(None, stack, 'container',
        #                                        stack.container))
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        #wftool.doActionFor(content, 'delegate',
        #                   current_wf_var_id='Pilots',
        #                   member_ids=['xxx'],
        #                   levels=[0])

        #pstacks = wftool.getStackFor(content, 'Pilots')

        self.login('tata')
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        self.login('manager')

        ############################################
        # Delegate toto
        ############################################

        wftool.doActionFor(content, 'delegate',
                           current_wf_var_id='Pilots',
                           push_ids=['user:toto'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent(context=content))
        self.assertEqual({0:['user:toto']},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'toto': ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')
        # It's been updated for next time
        self.assertEqual(flrm,
                         #{'toto': ('WorkspaceManager',)}
                         {}
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k == 'user:toto':
                self.assert_('WorkspaceManager' in v)

        # Manager can't manage the stack
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        ################################################
        # Delegate tata
        ################################################

        wftool.doActionFor(content, 'delegate',
                           current_wf_var_id='Pilots',
                           push_ids=['user:tata'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent(context=content))
        self.assertEqual({0:['user:toto', 'user:tata']},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'tata': ('WorkspaceManager',),
                          'toto': ('WorkspaceManager',)
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm,
                         {'toto': ('WorkspaceManager',),
                          #'tata': ('WorkspaceManager',)
                          },
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:toto', 'user:tata',):
                self.assert_('WorkspaceManager' in v)

            # Manager can't manage the stack
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        ################################################
        # EXECUTE BORING TRANSITION
        # check if nothing moved
        ################################################

        wftool.doActionFor(content, 'silent')

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent(context=content))
        self.assertEqual({0:['user:toto', 'user:tata']},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'tata': ('WorkspaceManager',),
                          'toto': ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')
        # It's been updated for next time
        self.assertEqual(flrm,
                         {'tata': ('WorkspaceManager',),
                          'toto': ('WorkspaceManager',)},
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:toto', 'user:tata',):
                self.assert_('WorkspaceManager' in v)

        # Manager can't manage the stack
        self.assert_(not wftool.canManageStack(content, 'Pilots'))

        #################################################
        # Delegate Manager
        #################################################

        wftool.doActionFor(content, 'delegate',
                           current_wf_var_id='Pilots',
                           push_ids=['user:manager'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent(context=content))
        self.assertEqual({0:['user:toto', 'user:tata', 'user:manager']},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
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
                          'tata': ('WorkspaceManager',)},
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:toto', 'user:tata','user:manager'):
                self.assert_('WorkspaceManager' in v)

        # Manager can't manage the stack
        self.assert_(wftool.canManageStack(content, 'Pilots'))

        ####################################################
        # REMOVE TOTO
        ####################################################

        wftool.doActionFor(content, 'remove_delegate',
                           current_wf_var_id='Pilots',
                           pop_ids=['0,user:toto'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent(context=content))
        self.assertEqual({0:['user:tata', 'user:manager']},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',),
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm,
                         {'manager': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',),
                          'toto': ('WorkspaceManager',)},
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:manager', 'user:tata',):
                self.assert_('WorkspaceManager' in v)

        self.assert_('user:toto' not in lc.keys())

        # Manager
        self.assert_(wftool.canManageStack(content, 'Pilots'))

        # toto can't manage the stack anymore
        self.logout()
        self.login('toto')
        self.assert_(not wftool.canManageStack(content, 'Pilots'))
        self.logout()
        self.login('manager')

        ####################################################
        # REMOVE TATA
        ####################################################

        wftool.doActionFor(content, 'remove_delegate',
                           current_wf_var_id='Pilots',
                           pop_ids=['0,user:tata'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(pstacks.getStackContent(context=content))
        self.assertEqual({0:['user:manager']},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager': ('WorkspaceManager',),
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm,
                         {'manager': ('WorkspaceManager',),
                          'tata': ('WorkspaceManager',),
                          }
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        for k, v in lc.items():
            if k in ('user:manager',):
                self.assert_('WorkspaceManager' in v)

        self.assert_('user:toto' not in lc.keys())
        self.assert_('user:tata' not in lc.keys())

        # Manager
        self.assert_(wftool.canManageStack(content, 'Pilots'))

        ####################################################
        # REMOVE manager
        ####################################################

        wftool.doActionFor(content, 'remove_delegate',
                           current_wf_var_id='Pilots',
                           pop_ids=['0,user:manager'],
                           levels=[0])
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assert_(not pstacks.getStackContent(context=content))
        self.assertEqual({},
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assert_(not pstackdef._getLocalRolesMapping(pstacks))
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm,
                         {'manager': ('WorkspaceManager',),
                          }
                         )

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:toto' not in lc.keys())
        self.assert_('user:tata' not in lc.keys())
        self.assert_('user:manager' not in lc.keys())

        # Manager
        self.assert_( not wftool.canManageStack(content, 'Pilots'))

    def test_resetOnSImpleStack(self):

        self.login('manager')
        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Associates')
        self.assert_(pstacks is not None)

        ############################
        # PUSH me within
        ############################

        kw = {'push_ids': ('user:manager',),
              'current_wf_var_id' : 'Associates'}
        wftool.doActionFor(content,'delegate',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager' : ('WorkspaceMember',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(flrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())

        # Manager
        self.assert_( wftool.canManageStack(content, 'Associates'))

        ############################
        # reset with new_users
        ############################

        kw = {'reset_ids': ('user:toto',),
              'current_wf_var_id':'Associates'}
        wftool.doActionFor(content,'reset',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:toto'],
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'toto' : ('WorkspaceMember',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(flrm, {'manager':('WorkspaceMember',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:toto' in lc.keys())

        # Manager
        self.assert_( not wftool.canManageStack(content, 'Associates'))

        ############################
        # reset with new_groups
        ############################

        kw = {'reset_ids': ('group:nuxeo',),
              'current_wf_var_id':'Associates'}
        wftool.doActionFor(content,'reset',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['group:nuxeo'],
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'group:nuxeo' : ('WorkspaceMember',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(flrm, {'toto':('WorkspaceMember',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('group:nuxeo' in lc.keys())

        # Manager
        self.assert_( not wftool.canManageStack(content, 'Associates'))

        ############################
        # reset with new_stack
        ############################

        new_stack = SimpleStack()

        kw = {'new_stack': new_stack,
              'reset_ids': ('user:manager',),
              'current_wf_var_id':'Associates'}
        wftool.doActionFor(content,'reset',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager',],
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager':('WorkspaceMember',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(flrm, {'group:nuxeo':('WorkspaceMember',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_(not 'group:nuxeo' in lc.keys())
        self.assert_('user:manager' in lc.keys())

        # Manager
        self.assert_( wftool.canManageStack(content, 'Associates'))

    def test_resetOnHierarchicalStack(self):

        self.login('manager')
        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assert_(pstacks is not None)

        ############################
        # PUSH me within
        ############################

        kw = {'push_ids': ('user:manager',),
              'levels':(0,),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getStackContent(context=content)[0])

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager' : ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())

        # Manager
        self.assert_( wftool.canManageStack(content, 'Pilots'))

        ############################
        # reset with new_users
        ############################

        kw = {'reset_ids': ('user:toto',),
              'current_wf_var_id':'Pilots'}
        wftool.doActionFor(content,'reset',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:toto'],
                         pstacks.getStackContent(context=content)[0])

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'toto' : ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {'manager':('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:toto' in lc.keys())

        # Manager
        self.assert_( not wftool.canManageStack(content, 'Pilots'))

        ############################
        # reset with new_groups
        ############################

        kw = {'reset_ids': ('group:nuxeo',),
              'current_wf_var_id':'Pilots'}
        wftool.doActionFor(content,'reset',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['group:nuxeo'],
                         pstacks.getStackContent(context=content)[0])

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'group:nuxeo' : ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {'toto':('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('group:nuxeo' in lc.keys())

        # Manager
        self.assert_( not wftool.canManageStack(content, 'Pilots'))

        ############################
        # reset with new_stack
        ############################

        new_stack = HierarchicalStack()

        kw = {'new_stack': new_stack,
              'reset_ids': ('user:manager',),
              'current_wf_var_id':'Pilots'}
        wftool.doActionFor(content,'reset',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager',],
                         pstacks.getStackContent(context=content)[0])

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager':('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {'group:nuxeo':('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_(not 'group:nuxeo' in lc.keys())
        self.assert_('user:manager' in lc.keys())

        # Manager
        self.assert_( wftool.canManageStack(content, 'Pilots'))

    def test_replaceOnHierarchicalStack(self):

        self.login('manager')
        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assert_(pstacks is not None)

        ############################
        # PUSH me within
        ############################

        kw = {'push_ids': ('user:manager',),
              'levels':(0,),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getStackContent(context=content)[0])

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager' : ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())

        # Manager
        self.assert_( wftool.canManageStack(content, 'Pilots'))

        ##############################################################
        # Replace the element within the stack and follow the reset
        # transition
        ##############################################################

        stack = wftool.getStackFor(content, 'Pilots')
        new_stack = stack.getCopy()
        self.assertNotEqual(stack, new_stack)
        new_stack.replace('user:manager', 'user:toto')

        wftool.doActionFor(content, 'reset',
                           new_stack=new_stack,
                           current_wf_var_id='Pilots')
        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:toto'],
                         pstacks.getStackContent(context=content)[0])

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'toto' : ('WorkspaceManager',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {'manager':('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' not in lc.keys())
        self.assert_('user:toto' in lc.keys())

        # Manager
        self.assert_(not wftool.canManageStack(content, 'Pilots'))


    def test_replaceOnSimpleStack(self):

        self.login('manager')
        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Associates')
        self.assert_(pstacks is not None)

        ############################
        # PUSH me within
        ############################

        kw = {'push_ids': ('user:manager',),
              'levels':(0,),
              'current_wf_var_id' : 'Associates'}
        wftool.doActionFor(content,'delegate',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'manager' : ('WorkspaceMember',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(flrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())

        # Manager
        self.assert_( wftool.canManageStack(content, 'Associates'))

        ##############################################################
        # Replace the element within the stack and follow the reset
        # transition
        ##############################################################

        stack = wftool.getStackFor(content, 'Associates')
        new_stack = stack.getCopy()
        self.assertNotEqual(stack, new_stack)
        new_stack.replace('user:manager', 'user:toto')

        wftool.doActionFor(content, 'reset',
                           new_stack=new_stack,
                           current_wf_var_id='Associates')
        pstacks = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:toto'],
                         pstacks.getStackContent(context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'toto' : ('WorkspaceMember',)})

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(flrm, {'manager':('WorkspaceMember',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' not in lc.keys())
        self.assert_('user:toto' in lc.keys())

        # Manager
        self.assert_(not wftool.canManageStack(content, 'Associates'))

    def test_stack_element_security(self):
        self.login('manager')
        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        ##################################################################
        # Add a default guard on the stackdef for viewing stack elements
        ##################################################################

        stackdef = wftool.getStackDefinitionFor(content, 'Associates')
        stackdef.setViewStackElementGuard(guard_roles='Manager')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Associates')
        self.assert_(pstacks is not None)

        ############################
        # PUSH me within
        ############################

        kw = {'push_ids': ('user:manager',),
              'levels':(0,),
              'current_wf_var_id' : 'Associates'}
        wftool.doActionFor(content,'delegate',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Associates')

        # Without security checks
        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        self.assertEqual(str(elt), 'user:manager')

        # With security checks
        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        self.assertEqual(str(elt), 'user:manager')
        self.logout()

        ##############################################
        # LOGIN WITH toto who's not Manager
        # not allowed to view the element because of the guard
        ##############################################

        self.login('toto')
        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        self.assertEqual(elt.meta_type, 'Hidden User Stack Element')

        ##################################################################
        # Change the default guard on the stackdef for viewing stack elements
        ##################################################################

        self.logout()

        self.login('manager')
        stackdef = wftool.getStackDefinitionFor(content, 'Associates')
        stackdef.setViewStackElementGuard(guard_roles='')
        self.logout()

        self.login('toto')
        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        self.assertEqual(elt.meta_type, 'User Stack Element')
        self.logout()

        ###############################################################
        # Override the default guard with a guard on the element
        ###############################################################

        self.login('manager')
        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        elt.setViewGuard(guard_roles='Manager')

        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        self.assertEqual(str(elt), 'user:manager')

        self.logout()

        self.login('toto')
        scontent = pstacks.getStackContent(type='object', context=content)
        elt = scontent[0]
        self.assertEqual(elt.meta_type, 'Hidden User Stack Element')
        self.logout()

    def test_update_roles_with_stack_element_security(self):

        wftool = self.wftool
        content = getattr(self.portal.f, 'dummy')

        #
        # push people on hstack
        #
        kw = {'push_ids': ('user:manager',),
              'levels':(0,),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate', **kw)

        hstack = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(hstack is not None)
        self.assertEqual({0: ['user:manager']},
                         hstack.getStackContent(context=content))

        # Check local roles mapping
        hstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'manager' : ('WorkspaceManager',)})

        # Check the former local role mapping
        hsflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(hsflrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)
        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceManager' in lc['user:manager'])

        # push toto too, so that he getsthe same role than the one he already
        # has thanks too the Associates stack
        self.login('manager')
        self.assert_( wftool.canManageStack(content, 'Pilots'))

        kw = {'push_ids': ('user:toto',),
              'levels':(1,),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate', **kw)

        hstack = wftool.getStackFor(content, 'Pilots')

        self.assertEqual({0: ['user:manager'],
                          1: ['user:toto']},
                         hstack.getStackContent(context=content))

        # Check local roles mapping
        hstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'manager': ('WorkspaceManager',),
                          'toto' : ('WorkspaceReader',)})

        # Check the former local role mapping
        hsflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(hsflrm, {'manager':('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceManager' in lc['user:manager'])
        self.assert_('user:toto' in lc.keys())
        self.assert_('WorkspaceReader' in lc['user:toto'])

        # hide manager from toto by changing default guard on stack elements
        # guard: manager cannot see toto anymore
        scontent = hstack.getStackContent(type='object', context=content)
        elt = scontent[1][0]
        guard_expr = "python:user.getId() != 'manager'"
        elt.setViewGuard(guard_expr=guard_expr)
        elt.setEditGuard(guard_expr=guard_expr)

        # move level up
        kw = {'current_wf_var_id' : 'Pilots'}
        hstack = wftool.getStackFor(content, 'Pilots')
        self.assertEqual(hstack.getCurrentLevel(), 0)
        wftool.doActionFor(content, 'validate', **kw)
        hstack = wftool.getStackFor(content, 'Pilots')
        self.assertEqual(hstack.getCurrentLevel(), 1)

        # Check local roles mapping
        hstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        hstack = wftool.getStackFor(content, 'Pilots')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'manager': ('WorkspaceMember',),
                          'toto' : ('WorkspaceManager',)})

        # Check the former local role mapping
        hsflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                          'Pilots')
        self.assertEqual(hsflrm, {'manager': ('WorkspaceManager',),
                                  'toto': ('WorkspaceReader',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:manager'])
        self.assert_('user:toto' in lc.keys())
        self.assert_('WorkspaceManager' in lc['user:toto'])


    def test_moveUpMoveDownWithHierarchical(self):
        # Test move up and move down with a hierarchical stack
        self.login('manager')
        wftool = self.wftool

        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #########################################
        # Check current state fixtures
        #########################################

        wf = wftool['wf']
        current_state = wf._getWorkflowStateOf(content)
        self.assertEqual(current_state.getId(), 'delegating')

        #########################################
        # Check stack intialization
        # It should not be empty
        #########################################

        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assert_(pstacks is not None)

        ##########################################
        # PUSH
        ##########################################

        kw = {'push_ids': ('user:manager', 'user:toto', 'user:tata'),
              'levels':(0,1,2),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate',
                           **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getLevelContent(level=0, context=content))
        self.assertEqual(['user:toto'],
                         pstacks.getLevelContent(level=1, context=content))
        self.assertEqual(['user:tata'],
                         pstacks.getLevelContent(level=2, context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'tata'   : ('WorkspaceReader',),
                          'manager': ('WorkspaceManager',),
                          'toto'   : ('WorkspaceReader',),
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('user:toto' in lc.keys())
        self.assert_('user:tata' in lc.keys())

        # MANAGER
        self.assert_( wftool.canManageStack(content, 'Pilots'))
        self.logout()

        self.login('toto')
        self.assert_(not wftool.canManageStack(content, 'Pilots'))
        self.logout()

        self.login('tata')
        self.assert_(not wftool.canManageStack(content, 'Pilots'))
        self.logout()

        #########################################################
        # MOVE UP
        #########################################################

        self.login('manager')
        kw = {'current_wf_var_id' : 'Pilots'}
        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assertEqual(pstacks.getCurrentLevel(), 0)
        wftool.doActionFor(content, 'validate', **kw)
        self.assertEqual(pstacks.getCurrentLevel(), 1)

        pstacks = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getLevelContent(level=0, context=content))
        self.assertEqual(['user:toto'],
                         pstacks.getLevelContent(level=1, context=content))
        self.assertEqual(['user:tata'],
                         pstacks.getLevelContent(level=2, context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'tata'   : ('WorkspaceReader',),
                          'manager': ('WorkspaceMember',),
                          'toto'   : ('WorkspaceManager',),
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {'tata'   : ('WorkspaceReader',),
                                'manager': ('WorkspaceManager',),
                                'toto'   : ('WorkspaceReader',),})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('user:toto' in lc.keys())
        self.assert_('user:tata' in lc.keys())

        self.logout()

        #########################################################
        # MOVE UP AGAIN
        #########################################################

        self.login('manager')
        kw = {'current_wf_var_id' : 'Pilots'}
        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assertEqual(pstacks.getCurrentLevel(), 1)

        wftool.doActionFor(content, 'validate', **kw)

        pstacks = wftool.getStackFor(content, 'Pilots')
        self.assertEqual(pstacks.getCurrentLevel(), 2)

        # Check stack status
        self.assert_(pstacks is not None)
        self.assertEqual(['user:manager'],
                         pstacks.getLevelContent(level=0, context=content))
        self.assertEqual(['user:toto'],
                         pstacks.getLevelContent(level=1, context=content))
        self.assertEqual(['user:tata'],
                         pstacks.getLevelContent(level=2, context=content))

        # Check local roles mapping
        pstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(pstackdef._getLocalRolesMapping(pstacks),
                         {'tata'   : ('WorkspaceManager',),
                          'manager': ('WorkspaceMember',),
                          'toto'   : ('WorkspaceMember',),
                          })

        # Check the former local role mapping
        flrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(flrm, {'tata'   : ('WorkspaceReader',),
                                'manager': ('WorkspaceMember',),
                                'toto'   : ('WorkspaceManager',),})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('user:toto' in lc.keys())
        self.assert_('user:tata' in lc.keys())

        self.logout()


    def test_role_settings_with_several_stacks(self):

        self.login('manager')
        wftool = self.wftool
        content = getattr(self.portal.f, 'dummy')
        self.assertEqual(wftool.getInfoFor(content, 'review_state'),
                         'delegating')

        #
        # push in associates stack
        #
        kw = {'push_ids': ('user:manager',),
              'current_wf_var_id' : 'Associates'}
        wftool.doActionFor(content,'delegate', **kw)

        sstack = wftool.getStackFor(content, 'Associates')

        # Check stack status
        self.assert_(sstack is not None)
        self.assertEqual(['user:manager'],
                         sstack.getStackContent(context=content))

        # Check local roles mapping
        sstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'manager' : ('WorkspaceMember',)})

        # Check the former local role mapping
        ssflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(ssflrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:manager'])

        # push toto too
        self.assert_( wftool.canManageStack(content, 'Associates'))

        kw = {'push_ids': ('user:toto',),
              'current_wf_var_id' : 'Associates'}
        wftool.doActionFor(content,'delegate', **kw)

        sstack = wftool.getStackFor(content, 'Associates')

        self.assertEqual(['user:manager', 'user:toto'],
                         sstack.getStackContent(context=content))

        # Check local roles mapping
        sstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'manager': ('WorkspaceMember',),
                          'toto' : ('WorkspaceMember',)})

        # Check the former local role mapping
        ssflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Associates')

        # It's been updated for next time
        self.assertEqual(ssflrm, {'manager':('WorkspaceMember',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:manager'])
        self.assert_('user:toto' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:toto'])

        #
        # push people on hstack
        #
        kw = {'push_ids': ('user:manager',),
              'levels':(0,),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate', **kw)

        hstack = wftool.getStackFor(content, 'Pilots')

        # Check stack status
        self.assert_(hstack is not None)
        self.assertEqual({0: ['user:manager']},
                         hstack.getStackContent(context=content))

        # Check local roles mapping
        hstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'manager' : ('WorkspaceManager',)})

        # Check the former local role mapping
        hsflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(hsflrm, {})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)
        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceManager' in lc['user:manager'])

        # push toto too, so that he getsthe same role than the one he already
        # has thanks too the Associates stack
        self.assert_( wftool.canManageStack(content, 'Pilots'))

        kw = {'push_ids': ('user:toto',),
              'levels':(-1,),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content,'delegate', **kw)

        hstack = wftool.getStackFor(content, 'Pilots')

        self.assertEqual({0: ['user:manager'],
                          -1: ['user:toto']},
                         hstack.getStackContent(context=content))

        # Check local roles mapping
        hstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'manager': ('WorkspaceManager',),
                          'toto' : ('WorkspaceMember',)})

        # Check the former local role mapping
        hsflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                        'Pilots')

        # It's been updated for next time
        self.assertEqual(hsflrm, {'manager':('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)

        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceManager' in lc['user:manager'])
        self.assert_('user:toto' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:toto'])


        # pop toto from the Pilots stack (pop behaviour is only Pilots stack)
        kw = {'pop_ids': ('-1,user:toto',),
              'current_wf_var_id' : 'Pilots'}
        wftool.doActionFor(content, 'remove_delegate', **kw)

        sstack = wftool.getStackFor(content, 'Associates')
        # Check the former local role mapping
        ssflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                          'Associates')
        # It's been updated for next time
        self.assertEqual(ssflrm, {'manager': ('WorkspaceMember',),
                                  'toto': ('WorkspaceMember',)})
        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)
        self.assertEqual(['user:manager', 'user:toto'],
                         sstack.getStackContent(context=content))
        # Check local roles mapping
        sstackdef = wftool.getStackDefinitionFor(content, 'Associates')
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'manager': ('WorkspaceMember',),
                          'toto': ('WorkspaceMember',)})

        hstack = wftool.getStackFor(content, 'Pilots')
        # Check the former local role mapping
        hsflrm = wftool.getFormerLocalRoleMappingForStack(content, 'wf',
                                                          'Pilots')
        # It's been updated for next time
        self.assertEqual(hsflrm, {'manager': ('WorkspaceManager',),
                                  'toto': ('WorkspaceMember',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)
        self.assertEqual({0: ['user:manager']},
                         hstack.getStackContent(context=content))
        # Check local roles mapping
        hstackdef = wftool.getStackDefinitionFor(content, 'Pilots')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'manager': ('WorkspaceManager',)})

        # Check local roles on the content
        mtool = getToolByName(self.portal, 'portal_membership')
        lc = mtool.getMergedLocalRoles(content)
        self.assert_('user:manager' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:manager'])
        self.assert_('WorkspaceManager' in lc['user:manager'])
        self.assert_('user:toto' in lc.keys())
        self.assert_('WorkspaceMember' in lc['user:toto'])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WorkflowToolTests))
    return suite

if __name__ == '__main__':
    framework()
