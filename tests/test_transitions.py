# -*- coding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author : Julien Anguenot <ja@nuxeo.com>
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
from Products.CPSWorkflow.transitions import TransitionDefinition

class TestCPSWorkflowTransitions(SecurityRequestTest):

    def setUp(self):
        SecurityRequestTest.setUp(self)

        from Products.CPSWorkflow.workflowtool import addWorkflowTool
        addWorkflowTool(self.root)

    def test_cps_transition_definition(self):

        #
        # Test the CPS Transition class
        #

        tdef = TransitionDefinition(id='fake')
        tdef.setProperties(title='Transition def title',
                           new_state_id='')
        self.assertRaises(AttributeError, tdef.getAvailableTransitionIds)
        self.assertEqual(tdef.getWorkflow(), None)

        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           transition_behavior=(101,),)
        self.assertEqual(tdef.transition_behavior, (101,))

        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           transition_behavior=(101,102),)
        self.assertEqual(tdef.transition_behavior, (101,102))

        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           transition_behavior=(101,),)
        self.assertEqual(tdef.transition_behavior, (101,))

        # Workflow stack stuffs
        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           push_on_workflow_variable=['xx', 'yy'],)
        self.assertEqual(tdef.push_on_workflow_variable, ['xx', 'yy'])

        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           pop_on_workflow_variable=['xx', 'yy'],)
        self.assertEqual(tdef.pop_on_workflow_variable, ['xx', 'yy'])

        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           workflow_up_on_workflow_variable=['xx', 'yy'],)
        self.assertEqual(tdef.workflow_up_on_workflow_variable, ['xx', 'yy'])

        tdef.setProperties(title='Transition def title',
                           new_state_id='',
                           workflow_down_on_workflow_variable=['xx', 'yy'],)
        self.assertEqual(tdef.workflow_down_on_workflow_variable, ['xx', 'yy'])

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
        sdef = wf.transitions.get('t1')

        # more tests

    def test_comment_behaviour(self):
       tdef = TransitionDefinition(id='fake')
       expr = "python:proxy.portal_type == 'TightDoc' and 'required' or 'none'"
       tdef.setProperties('Title', '', comment_behaviour_expr=expr)
       class FakeProxy:
           pass

       proxy = FakeProxy()
       proxy.portal_type = 'TightDoc'
       context = None
       self.assertEquals(tdef.getCommentBehaviour(proxy, context), 'required')
       proxy.portal_type = 'Other type'
       self.assertEquals(tdef.getCommentBehaviour(proxy, context), 'none')

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestCPSWorkflowTransitions)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
