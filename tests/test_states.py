#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# (C) Copyright 2004-2005 Nuxeo SARL <http://nuxeo.com>
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

import unittest

from Products.CMFCore.tests.base.testcase import SecurityRequestTest

from Products.CPSWorkflow.workflow import WorkflowDefinition
from Products.CPSWorkflow.workflow import TRIGGER_USER_ACTION

from Products.CPSWorkflow.states import StateDefinition
from Products.CPSWorkflow.constants import STATE_FLAGS_EXPORT

# XXX default values for sdef.state_delegatees_vars_info is not {} as it should
# be.  it comes from the fact that test_workflow_with_stacks is dirty and
# doesn't clean at the end of test. Needs to be fixed

class TestCPSWorkflowStates(SecurityRequestTest):

    def setUp(self):
        SecurityRequestTest.setUp(self)

        from Products.CPSWorkflow.workflowtool import addWorkflowTool
        addWorkflowTool(self.root)

    def test_simple_state_definition(self):
        sdef = StateDefinition('sdef')

        # Test initial properties
        self.assertEqual(sdef.state_behaviors, ())
        self.assertEqual(sdef.transitions, ())
        #self.assertEqual(sdef.state_delegatees_vars_info, {})

        # Just call it without anything
        sdef.setProperties()

        # Test property again
        self.assertEqual(sdef.state_behaviors, ())
        self.assertEqual(sdef.transitions, ())
        #self.assertEqual(sdef.state_delegatees_vars_info, {})

        # Test adding state behaviors
        sdef.setProperties(state_behaviors=STATE_FLAGS_EXPORT.keys())

        # Test property again
        self.assertEqual(sdef.state_behaviors,
                         tuple(STATE_FLAGS_EXPORT.keys()))
        self.assertEqual(sdef.transitions, ())
        #self.assertEqual(sdef.state_delegatees_vars_info, {})


    def makeWorkflows(self):
        id = 'wf'
        wf = WorkflowDefinition(id)
        self.root.portal_workflow._setObject(id, wf)
        wf = self.root.portal_workflow.wf

        # Create states
        wf.states.addState('s1')
        states = list(wf.states.objectIds())
        states.sort()
        self.assertEqual(tuple(states), ('s1',))

        # Create transition
        wf.transitions.addTransition('t1')
        t1 = wf.transitions.get('t1')
        t1.setProperties('title', 's1', trigger_type=TRIGGER_USER_ACTION,
            transition_behavior=('initial_create',))
        transitions = wf.transitions.objectIds()
        self.assertEqual(tuple(transitions), ('t1',))
        return wf

    def test_state_definition_on_workflow(self):
        wf = self.makeWorkflows()
        sdef = wf.states.get('s1')

        # Test initial properties
        self.assertEqual(sdef.state_behaviors, ())
        self.assertEqual(sdef.transitions, ())
        sdef.setProperties()

        # Test property again
        self.assertEqual(sdef.state_behaviors, ())
        self.assertEqual(sdef.transitions, ())

        # Test adding state behaviors
        sdef.setProperties(state_behaviors=STATE_FLAGS_EXPORT.keys())

        # Test property again
        self.assertEqual(sdef.state_behaviors,
                         tuple(STATE_FLAGS_EXPORT.keys()))
        self.assertEqual(sdef.transitions, ())

        # Test add delegatees var info
        for stackdef_type, stack_type, var_id, lc in (
            ('Hierarchical Stack Definition', 'Hierarchical Stack',
             'toto', 'WorkspaceManager'),
            ('Simple Stack Definition', 'Simple Stack',
             'tata', 'WorkspaceMember')):
            sdef.addStackDefinition(stackdef_type,
                                    stack_type,
                                    var_id)


        # Add Expressions
        new_stackdef = sdef.getStackDefinitionFor('toto')
        new_stackdef.addManagedRole('WorkspaceManager', 'python:1')
        new_stackdef = sdef.getStackDefinitionFor('tata')
        new_stackdef.addManagedRole('WorkspaceMember', 'python:1')

        # Test property again
        self.assertEqual(sdef.state_behaviors,
                         tuple(STATE_FLAGS_EXPORT.keys()))
        self.assertEqual(sdef.transitions, ())

        dinfo = sdef.getStackDefinitionFor('toto')
        self.assertNotEqual(dinfo, None)
        self.assertEqual(dinfo.getStackDataStructureType(),
                         'Hierarchical Stack')
        self.assertEqual(dinfo.getStackWorkflowVariableId(), 'toto')
        self.assert_('WorkspaceManager' in dinfo.getManagedRoles())

        dinfo = sdef.getStackDefinitionFor('tata')
        self.assertNotEqual(dinfo, None)
        self.assertEqual(dinfo.getStackDataStructureType(), 'Simple Stack')
        self.assertEqual(dinfo.getStackWorkflowVariableId(), 'tata')
        self.assert_('WorkspaceMember' in dinfo.getManagedRoles())

        # Let's remove the delegatees var info
        sdef.delStackDefinitionsById(['toto'])

        # Test property again
        self.assertEqual(sdef.state_behaviors,
                         tuple(STATE_FLAGS_EXPORT.keys()))
        self.assertEqual(sdef.transitions, ())

        dinfo = sdef.getStackDefinitionFor('toto')
        self.assertEqual(dinfo, None)

        dinfo = sdef.getStackDefinitionFor('tata')
        self.assertNotEqual(dinfo, None)
        self.assertEqual(dinfo.getStackDataStructureType(), 'Simple Stack')
        self.assertEqual(dinfo.getStackWorkflowVariableId(), 'tata')
        self.assert_('WorkspaceMember' in dinfo.getManagedRoles())

        # Let's remove the delegatees var info
        sdef.delStackDefinitionsById(['toto'])

        # Test property again
        self.assertEqual(sdef.state_behaviors,
                         tuple(STATE_FLAGS_EXPORT.keys()))
        self.assertEqual(sdef.transitions, ())

        dinfo = sdef.getStackDefinitionFor('tata')
        self.assertNotEqual(dinfo, None)
        self.assertEqual(dinfo.getStackDataStructureType(), 'Simple Stack')
        self.assertEqual(dinfo.getStackWorkflowVariableId(), 'tata')
        self.assert_('WorkspaceMember' in dinfo.getManagedRoles())

        # Let's remove the delegatees var info
        sdef.delStackDefinitionsById(['tata'])

        # Test property again
        self.assertEqual(sdef.state_behaviors,
                         tuple(STATE_FLAGS_EXPORT.keys()))
        self.assertEqual(sdef.transitions, ())
        #self.assertEqual(sdef.state_delegatees_vars_info, {})
        self.assertEqual(sdef.getStackDefinitionFor('toto'), None)
        self.assertEqual(sdef.getStackDefinitionFor('tata'), None)
        #self.assertEqual(sdef.getDelegateesVarsInfo(), {})

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestCPSWorkflowStates)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
