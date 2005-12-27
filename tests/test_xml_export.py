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
"""Test workflow exported with CMFSetup
"""

import unittest

from Products.CPSWorkflow.tests.SetupWorkflowTestCase import SetupWorkflowTestCase
from Products.GenericSetup.tests.common import DummyExportContext

# Imports for sample workflows

# workflow classes
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.CPSWorkflow.workflow import WorkflowDefinition as CPSWorkflowDefinition
# permissions
from Products.CMFCore.permissions import View, ModifyPortalContent
# transition behaviours
from Products.CPSWorkflow.transitions import *
# state behaviours
from Products.CPSWorkflow.states import *
# wf triggers
#from Products.DCWorkflow.Transitions import TRIGGER_AUTOMATIC
#from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION
#from Products.DCWorkflow.Transitions import TRIGGER_WORKFLOW_METHOD


class TestWorkflowExport:
    """Test workflow export methods
    """
    # waiting for API refactoring
    pass


class TestFullDCWorkflowExport(SetupWorkflowTestCase):
    """Test full workflow with DCWorkflow workflow
    """

    #
    # Helper methods
    #

    def _setUpTestDCWorkflow(self):
        """Setup a test DC workflow
        """
        wfdef = {
            'wfid': 'test_dc_workflow',
            'wftype': 'dc_workflow (Web-configurable workflow)',
            'permissions': (View,
                            ModifyPortalContent,
                            ),
            'state_var': 'review_state',
            'variables': {},
            'states': {},
            'transitions': {},
            'scripts': {},
            }
        self._setUpTestWorkflow(wfdef)

    #
    # Tests
    #

    def test_DCWorkflowExport(self):
        self.assertEqual(self.wftool.objectIds(), [])
        self._setUpTestDCWorkflow()
        self.assertEqual(self.wftool.objectIds(), ['test_dc_workflow'])
        wf = self.wftool.test_dc_workflow
        self.assertEqual(wf.meta_type, DCWorkflowDefinition.meta_type)

        #XXX TODO


class TestFullCPSWorkflowExport(SetupWorkflowTestCase):
    """Test full workflow with CPSWorkflow workflow
    """

    #
    # Helper methods
    #

    def _getXMLdirectory(self):
        return 'xml/test_cps_workflow/'

    def _setUpTestCPSWorkflow(self):
        """Setup a test CPS workflow
        """
        wfdef = {
            'wfid': 'test_cps_workflow',
            'wftype': 'cps_workflow (Web-configurable workflow for CPS)',
            'permissions': (View,
                            ModifyPortalContent,
                            ),
            'state_var': 'review_state',
            'variables': self._getCPSWorkflowVariables(),
            'states': self._getCPSWorkflowStates(),
            'transitions': self._getCPSWorkflowTransitions(),
            'scripts': self._getCPSWorkflowScripts(),
            }
        self._setUpTestWorkflow(wfdef)

    def _getCPSWorkflowVariables(self):
        """Get the validation workflow variables
        """
        variables = {}
        variables['action'] = {
            'description': 'The last transition',
            'default_expr': 'transition/getId|nothing',
            'for_status': 1,
            'update_always': 1,
            }
        variables['actor'] = {
            'description': 'The ID of the user who performed the last transition',
            'default_expr': 'user/getId',
            'for_status': 1,
            'update_always': 1,
            }
        variables['comments'] = {
            'description': 'Comments about the last transition',
            'default_expr': "python:state_change.kwargs.get('comment', '')",
            'for_status': 1,
            'update_always': 1,
            }
        variables['review_history'] = {
            'description': 'Provides access to workflow history',
            'default_expr': "state_change/getHistory",
            'props': {
                'guard_roles': 'Manager; SectionManager; \
                SectionReviewer; SectionIntermediateReviewer',
                },
            }
        variables['time'] = {
            'description': 'Time of the last transition',
            'default_expr': "state_change/getDateTime",
            'for_status': 1,
            'update_always': 1,
            }
        variables['language_revs'] = {
            'description': 'The language revisions of the proxy',
            'default_expr': 'state_change/getLanguageRevisions',
            'for_status': 1,
            'update_always': 1,
            }
        variables['dest_container'] = {
            'description': 'Destination container for the last paste/publish',
            'default_expr': "python:state_change.kwargs.get('dest_container', '')",
            'for_status': 1,
            'update_always': 1,
            }
        return variables

    def _getCPSWorkflowStates(self):
        """Get the validation workflow states
        """
        states = {}

        # lists of roles to be used in stacks and transitions guard roles
        # definitions
        view_roles = ('Manager',
                      'SectionManager',
                      'SectionReviewer',
                      'SectionIntermediateReviewer',
                      'SectionReader',
                      )
        edit_roles = ('Manager',
                      'SectionManager',
                      'SectionReviewer',
                      'SectionIntermediateReviewer',
                      )

        validation_stack = {
            'stackdef_type': 'Hierarchical Stack Definition',
            'stack_type'   : 'Hierarchical Stack',
            'var_id'    : 'Reviewers',
            'managed_role_exprs' : {
                # SectionReviewer: top of the stack, and at current level
                'SectionReviewer': "python:stack.getAllLevels() and level == stack.getAllLevels()[-1] and level == stack.getCurrentLevel()",
                # SectionIntermediateReviewer: not top of the stack or not at current level
                'SectionIntermediateReviewer': "python:stack.getAllLevels() and level < stack.getAllLevels()[-1] or level != stack.getCurrentLevel()",
                },
            'empty_stack_manage_guard': {
                'guard_roles': '; '.join(edit_roles),
                },
            }

        states['pending'] = {
            'title': 'Waiting for reviewer',
            'transitions': ('accept',
                            'reject',
                            'manage_delegatees',
                            'move_up_delegatees',
                            'move_down_delegatees',
                            ),
            'permissions': {
                View: edit_roles,
                ModifyPortalContent: edit_roles,
                },
            'state_behaviors': (STATE_BEHAVIOR_PUSH_DELEGATEES,
                                STATE_BEHAVIOR_POP_DELEGATEES,
                                STATE_BEHAVIOR_WORKFLOW_DOWN,
                                STATE_BEHAVIOR_WORKFLOW_UP,
                                ),
            'stackdefs' : {
                'Reviewers': validation_stack,
                },
            'push_on_workflow_variable' : ('Reviewers',),
            'pop_on_workflow_variable' : ('Reviewers',),
            'workflow_down_on_workflow_variable' : ('Reviewers',),
            'workflow_up_on_workflow_variable' : ('Reviewers',),
            }
        states['published'] = {
            'title': 'Public',
            'transitions': ('unpublish',),
            'permissions': {
                View: view_roles,
                ModifyPortalContent: ('Manager',),
                },
            }
        return states

    def _getCPSWorkflowTransitions(self):
        """Get the validation workflow transitions
        """
        transitions = {}

        view_roles = 'Manager; SectionManager; SectionReviewer; ' +\
                     'SectionIntermediateReviewer; SectionReader'
        edit_roles = 'Manager; SectionManager; SectionReviewer; ' +\
                     'SectionIntermediateReviewer'
        pub_roles = 'Manager; SectionManager; SectionReviewer'

        transitions['publish'] = {
            'title': 'Member publishes directly',
            'new_state_id': 'published',
            'transition_behavior': (TRANSITION_INITIAL_PUBLISHING,
                                    TRANSITION_BEHAVIOR_FREEZE,
                                    TRANSITION_BEHAVIOR_MERGE),
            'props': {
               'guard_roles': pub_roles,
               },
            }
        transitions['submit'] = {
            'title': 'Member requests publishing',
            'new_state_id': 'pending',
            'transition_behavior': (TRANSITION_INITIAL_PUBLISHING,
                                    TRANSITION_BEHAVIOR_FREEZE),
            'props': {
                'guard_roles': 'Manager; Member',
                },
            }
        transitions['accept'] = {
            'title': 'Reviewer accepts publishing',
            'new_state_id': 'published',
            'transition_behavior': (TRANSITION_BEHAVIOR_MERGE,),
            'actbox_name': 'action_accept',
            'actbox_category': 'workflow',
            'actbox_url': '%(content_url)s/content_accept_form',
            'props': {
                'guard_roles': pub_roles,
                },
            }
        transitions['reject'] = {
            'title': 'Reviewer rejects publishing',
            'new_state_id': '',
            'transition_behavior': (TRANSITION_BEHAVIOR_DELETE,),
            'actbox_name': 'action_reject',
            'actbox_category': 'workflow',
            'actbox_url': '%(content_url)s/content_reject_form',
            'props': {
                'guard_roles': edit_roles,
                # Let's filter SectionIntermediateReviewer users so that only
                # reviewer at current level can reject the document.
                # We now that users with role SectionIntermediateReviewer are at
                # current level only if they can manage the stack.
                'guard_expr': "python:user.has_role(('Manager', 'SectionManager', 'SectionReviewer'), here) or user.has_role(('SectionIntermediateReviewer',), here) and here.portal_workflow.canManageStack(here, 'Reviewers')",
                },
            }
        transitions['unpublish'] = {
            'title': 'Reviewer removes content from publication',
            'new_state_id': '',
            'transition_behavior': (TRANSITION_BEHAVIOR_DELETE,),
            'actbox_name': 'action_un_publish',
            'actbox_category': 'workflow',
            'actbox_url': '%(content_url)s/content_unpublish_form',
            'props': {
                'guard_roles': pub_roles,
                },
            }
        transitions['manage_delegatees'] = {
            'title': "Manage delegatees and add strange characters in title :)",
            'new_state_id': '',
            'transition_behavior': (TRANSITION_BEHAVIOR_PUSH_DELEGATEES,
                                    TRANSITION_BEHAVIOR_POP_DELEGATEES,
                                    ),
            'push_on_workflow_variable' : ('Reviewers',),
            'pop_on_workflow_variable' : ('Reviewers',),
            'actbox_name': 'manage_delegatees',
            'actbox_category': 'workflow',
            'actbox_url': '%(content_url)s/content_manage_delegatees_form',
            'props': {
                'guard_roles': edit_roles,
                },
            }
        transitions['move_up_delegatees'] = {
            'title': "Move up delegatees",
            'new_state_id': '',
            'transition_behavior': (TRANSITION_BEHAVIOR_WORKFLOW_UP,
                                    ),
            'workflow_up_on_workflow_variable' : ('Reviewers',),
            'actbox_name': 'move_up_delegatees',
            'actbox_category': 'workflow',
            'actbox_url': '%(content_url)s/content_move_up_delegatees_form?current_var_id=Reviewers',
            'props': {
                'guard_roles': edit_roles,
                },
            }
        transitions['move_down_delegatees'] = {
            'title': "Move down delegatees",
            'new_state_id': '',
            'transition_behavior': (TRANSITION_BEHAVIOR_WORKFLOW_DOWN,
                                    ),
            'workflow_down_on_workflow_variable' : ('Reviewers',),
            'actbox_name': 'move_down_delegatees',
            'actbox_category': 'workflow',
            'actbox_url': '%(content_url)s/content_move_down_delegatees_form?current_var_id=Reviewers',
            'props': {
                'guard_roles': edit_roles,
                },
            }
        return transitions

    def _getCPSWorkflowScripts(self):
        """Get the validation workflow scripts
        """
        # dummy script that is not used in the wf, just for test
        scripts = {}
        scripts['add_language_to_proxy'] = {
            '_owner': None,
            'script': """\
##parameters=state_change
lang=state_change.kwargs.get('lang')
from_lang=state_change.kwargs.get('from_lang')
state_change.object.addLanguageToProxy(lang, from_lang)
"""
            }
        return scripts

    #
    # Tests
    #

    def test_CPSWorkflowExport(self):
        self.assertEqual(self.wftool.objectIds(), [])
        self._setUpTestCPSWorkflow()
        self.assertEqual(self.wftool.objectIds(), ['test_cps_workflow'])
        wf = self.wftool.test_cps_workflow
        self.assertEqual(wf.meta_type, CPSWorkflowDefinition.meta_type)

        self._setupAdapters()

        # export wf
        context = DummyExportContext(self.root)

        from Products.CMFCore.exportimport.workflow import exportWorkflowTool
        exportWorkflowTool(context)

        # files :
        # - workflows
        # - test_cps_workflow definition
        # - test_cps_workflow script
        self.assertEqual(len(context._wrote), 3)

        # workflows
        filename, text, content_type = context._wrote[0]
        filepath = 'workflows.xml'
        self.assertEqual(filename, filepath)
        self.assertEqual(content_type, 'text/xml')
        wftool_export = self._getFileData(filepath)
        self._compareDOM(text, wftool_export)

        # test_cps_workflow
        filename, text, content_type = context._wrote[1]
        filepath = 'workflows/test_cps_workflow/definition.xml'
        self.assertEqual(filename, filepath)
        self.assertEqual(content_type, 'text/xml')
        wf_export = self._getFileData(filepath)
        self._compareDOM(text, wf_export)

        # test wf script
        filename, text, content_type = context._wrote[2]
        filepath = 'workflows/test_cps_workflow/scripts/add_language_to_proxy.py'
        self.assertEqual(filename, filepath)
        self.assertEqual(content_type, 'text/plain')
        script_export = self._getFileData(filepath)
        self.assertEqual(text, script_export)

def test_suite():
    suites = []
    suites.append(unittest.makeSuite(TestWorkflowExport))
    suites.append(unittest.makeSuite(TestFullDCWorkflowExport))
    suites.append(unittest.makeSuite(TestFullCPSWorkflowExport))
    return unittest.TestSuite(suites)

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')

