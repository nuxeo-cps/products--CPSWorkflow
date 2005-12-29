#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Anahide Tchertchian <at@nuxeo.com>
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
"""Test workflow imported with CMFSetup
"""

import unittest

from Products.CPSWorkflow.tests.SetupWorkflowTestCase import SetupWorkflowTestCase
from Products.GenericSetup.tests.common import DummyImportContext

# workflow classes
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.CPSWorkflow.workflow import WorkflowDefinition as CPSWorkflowDefinition
# permissions
from Products.CMFCore.permissions import View, ModifyPortalContent
# transition behaviours
from Products.CPSWorkflow.transitions import *
# state behaviours
from Products.CPSWorkflow.states import *

class TestWorkflowImport:
    """Test workflow import methods
    """
    # waiting for API refactoring
    pass


class TestFullDCWorkflowImport(SetupWorkflowTestCase):
    """Test full DC workflow import

    A DCWorkflow xml export should be imported well using the CPSWorkflow
    importer
    """
    # TODO
    pass


class TestFullCPSWorkflowImport(SetupWorkflowTestCase):
    """Test full CPS workflow import
    """

    #
    # Test case methods
    #

    def setUp(self):
        SetupWorkflowTestCase.setUp(self)

        # import workflow
        context = DummyImportContext(self.root)

        wftool_export = self._getFileData('workflows.xml')
        context._files['workflows.xml'] = wftool_export
        filepath = 'workflows/test_cps_workflow/definition.xml'
        wf_export = self._getFileData(filepath)
        context._files[filepath] = wf_export
        filepath = 'workflows/test_cps_workflow/scripts/add_language_to_proxy.py'
        script_export = self._getFileData(filepath)
        context._files[filepath] = script_export

        self._setupAdapters()
        self._setupRegistrations()

        from Products.CMFCore.exportimport.workflow import importWorkflowTool
        try:
            importWorkflowTool(context)
            self.wf = self.wftool.test_cps_workflow
        except:
            self.tearDown()
            raise

    #
    # Helper methods
    #

    def _getXMLdirectory(self):
        return 'xml/test_cps_workflow/'

    #
    # Tests
    #

    def test_WorkflowPresence(self):
        # ok, not really useful
        self.assert_('test_cps_workflow' in self.wftool.objectIds())

    def test_WorkflowType(self):
        self.assertEqual(self.wf.meta_type, CPSWorkflowDefinition.meta_type)

    def test_WorkflowProperties(self):
        self.assertEqual(self.wf.getId(), 'test_cps_workflow')
        self.assertEqual(self.wf.title_or_id(), "CPS Workflow Definition")
        self.assertEqual(self.wf.state_var, 'review_state')

    def test_WorkflowPermissions(self):
        permissions = [View, ModifyPortalContent]
        self.assertEqual(list(self.wf.permissions), permissions)

    def test_Variables(self):
        variable_ids = [
            'action',
            'actor',
            'comments',
            'review_history',
            'time',
            'language_revs',
            'dest_container',
            # special variable (stack)
            'Reviewers',
            ]
        self.assertEqual(self.wf.variables.objectIds(), variable_ids)

    def test_States(self):
        state_ids = [
            'pending',
            'published',
            ]
        self.assertEqual(self.wf.states.objectIds(), state_ids)

    def test_StatesPermissions(self):
        permissions = [
            'View',
            'Modify portal content',
            ]
        pending = self.wf.states.pending
        self.assertEqual(list(pending.getManagedPermissions()), permissions)
        self.assertEqual(pending.getPermissionInfo('View'),
                         {'acquired': 0,
                          'roles': ['Manager',
                                    'SectionManager',
                                    'SectionReviewer',
                                    'SectionIntermediateReviewer',
                                    ],
                          })
        self.assertEqual(pending.getPermissionInfo('Modify portal content'),
                         {'acquired': 0,
                          'roles': ['Manager',
                                    'SectionManager',
                                    'SectionReviewer',
                                    'SectionIntermediateReviewer'],
                          })

        published = self.wf.states.published
        self.assertEqual(list(published.getManagedPermissions()), permissions)
        self.assertEqual(published.getPermissionInfo('View'),
                         {'acquired': 0,
                          'roles': ['Manager',
                                    'SectionManager',
                                    'SectionReviewer',
                                    'SectionIntermediateReviewer',
                                    'SectionReader',
                                    ],
                          })
        self.assertEqual(published.getPermissionInfo('Modify portal content'),
                         {'acquired': 0,
                          'roles': ['Manager',
                                    ],
                          })

    def test_StatesTransitions(self):
        pending = self.wf.states.pending
        transitions = [
            'accept',
            'reject',
            'manage_delegatees',
            'move_up_delegatees',
            'move_down_delegatees',
            ]
        self.assertEqual(list(pending.transitions), transitions)

        published = self.wf.states.published
        transitions = [
            'unpublish',
            ]
        self.assertEqual(list(published.transitions), transitions)

    def test_StatesStateBehaviors(self):
        pending = self.wf.states.pending
        behaviors = [
            STATE_BEHAVIOR_PUSH_DELEGATEES,
            STATE_BEHAVIOR_POP_DELEGATEES,
            STATE_BEHAVIOR_WORKFLOW_UP,
            STATE_BEHAVIOR_WORKFLOW_DOWN,
            ]
        self.assertEqual(list(pending.state_behaviors), behaviors)

        published = self.wf.states.published
        self.assertEqual(list(published.state_behaviors), [])

    def test_StatesStackDefinitions(self):
        pending = self.wf.states.pending
        stackdefs = pending.getStackDefinitions()
        stack_var_id = 'Reviewers'
        self.assertEqual(stackdefs.keys(), [stack_var_id])

        # test stackdef configuration
        stackdef = stackdefs[stack_var_id]
        self.assertEqual(stackdef.meta_type, 'Hierarchical Stack Definition')
        self.assertEqual(stackdef.getStackDataStructureType(),
                         'Hierarchical Stack')
        self.assertEqual(stackdef.getStackWorkflowVariableId(), stack_var_id)
        self.assertEqual(stackdef.getManagerStackIds(), [])
        managed_roles = [
            'SectionReviewer',
            'SectionIntermediateReviewer',
            ]
        self.assertEqual(stackdef.getManagedRoles(), managed_roles)
        expr = stackdef._managed_role_exprs.get('SectionReviewer')
        self.assertEqual(expr,
                         "python:stack.getAllLevels() and level == "
                         "stack.getAllLevels()[-1] and level == "
                         "stack.getCurrentLevel()")
        expr = stackdef._managed_role_exprs.get('SectionIntermediateReviewer')
        self.assertEqual(expr,
                         "python:stack.getAllLevels() and level < "
                         "stack.getAllLevels()[-1] or level != "
                         "stack.getCurrentLevel()")

        guard = stackdef.getEmptyStackManageGuard()
        self.assertEqual(guard.permissions, ())
        guard_roles = (
            'Manager',
            'SectionManager',
            'SectionReviewer',
            'SectionIntermediateReviewer',
            )
        self.assertEqual(guard.roles, guard_roles)
        self.assertEqual(guard.groups, ())
        self.assertEqual(guard.getExprText(), '')

        # test stack guards as empty guards
        guards = [
            stackdef.getEditStackElementGuard(),
            stackdef.getViewStackElementGuard(),
            ]
        for guard in guards:
            self.assertEqual(guard.permissions, ())
            self.assertEqual(guard.roles, ())
            self.assertEqual(guard.groups, ())
            self.assertEqual(guard.getExprText(), '')

        published = self.wf.states.published
        self.assertEqual(published.getStackDefinitions(), {})

    def test_Transitions(self):
        transition_ids = [
            'publish',
            'submit',
            'unpublish',
            'accept',
            'reject',
            'manage_delegatees',
            'move_up_delegatees',
            'move_down_delegatees',
            ]
        self.assertEqual(self.wf.transitions.objectIds(), transition_ids)

    def test_TransitionsGuards(self):
        t = self.wf.transitions.reject
        guard = t.getGuard()
        self.assertEqual(guard.permissions, ())
        guard_roles = (
            'Manager',
            'SectionManager',
            'SectionReviewer',
            'SectionIntermediateReviewer',
            )
        self.assertEqual(guard.permissions, ())
        self.assertEqual(guard.roles, guard_roles)
        self.assertEqual(guard.groups, ())
        expr = "python:user.has_role(('Manager', 'SectionManager', " + \
               "'SectionReviewer'), here) or user.has_role((" + \
               "'SectionIntermediateReviewer',), here) and " + \
               "here.portal_workflow.canManageStack(here, 'Reviewers')"
        self.assertEqual(guard.getExprText(), expr)

        t = self.wf.transitions.manage_delegatees
        guard = t.getGuard()
        self.assertEqual(guard.permissions, ())
        self.assertEqual(guard.roles, guard_roles)
        self.assertEqual(guard.groups, ())
        self.assertEqual(guard.getExprText(), '')

    def test_TransitionsActions(self):
        t = self.wf.transitions.reject
        self.assertEqual(t.actbox_name, 'action_reject')
        self.assertEqual(t.actbox_url, '%(content_url)s/content_reject_form')
        self.assertEqual(t.actbox_category, 'workflow')

    def test_TransitionsBehaviors(self):
        t = self.wf.transitions.reject
        self.assertEqual(list(t.transition_behavior),
                         [TRANSITION_BEHAVIOR_DELETE])
        t = self.wf.transitions.manage_delegatees
        self.assertEqual(list(t.transition_behavior),
                         [TRANSITION_BEHAVIOR_PUSH_DELEGATEES,
                          TRANSITION_BEHAVIOR_POP_DELEGATEES])

    def test_Scripts(self):
        script_ids = [
            'add_language_to_proxy',
            ]
        self.assertEqual(self.wf.scripts.objectIds(), script_ids)

    def test_ScriptsContent(self):
        script = self.wf.scripts.add_language_to_proxy
        data = script.read()
        self.assertEqual(data, """\
## Script (Python) "add_language_to_proxy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
lang=state_change.kwargs.get(\'lang\')
from_lang=state_change.kwargs.get(\'from_lang\')
state_change.object.addLanguageToProxy(lang, from_lang)
""")

def test_suite():
    suites = []
    suites.append(unittest.makeSuite(TestWorkflowImport))
    suites.append(unittest.makeSuite(TestFullDCWorkflowImport))
    suites.append(unittest.makeSuite(TestFullCPSWorkflowImport))
    return unittest.TestSuite(suites)

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')

