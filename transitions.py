# -*- coding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author : Florent Guillaume <fg@nuxeo.com>
# Contributor : Julien Anguenot <ja@nuxeo.com>
#               - CPS Workflow refactoring and cleanup
#               - Workflow stack support
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

"""CPS Workflow Transitions

This modules extends the DCWorkflow based transitions and transitions
definitions.

It currently adds :

 - Transition flags which are here to define an allowed behavior on the
   transition

 - More properties on the TransitionDefinition It's holding the
   configuration. (i.e : transitions flags defined for a given transition and
   associated values. Either transitions or workflow variables)

 - Support for stack workflows. (c.f : doc/StackWorkflows)
"""

from zLOG import LOG, ERROR, DEBUG

from Globals import DTMLFile

from Products.DCWorkflow.Transitions \
     import TransitionDefinition as DCWFTransitionDefinition
from Products.DCWorkflow.Transitions import Transitions as DCWFTransitions
from Products.DCWorkflow.Transitions import TRIGGER_AUTOMATIC
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION

# For old code that doesn't import directly from constants
from Products.CPSWorkflow.constants import *


class TransitionDefinition(DCWFTransitionDefinition):
    """CPS Transition Definition

    It extends the DC Workfow Transition Definition by adding transition flags.
    """

    meta_type = 'CPS Workflow Transition'

    #
    # It holds the flag values
    #

    transition_behavior = ()

    #
    # Transitions allowed at destination
    #

    clone_allowed_transitions = []
    checkout_allowed_initial_transitions = []
    checkin_allowed_transitions = []

    #
    # Stack workflow transition flags
    # Workflow variables holding the stack workflow on which the transition
    # will be executed
    #

    push_on_workflow_variable = []
    pop_on_workflow_variable = []
    workflow_up_on_workflow_variable = []
    workflow_down_on_workflow_variable = []
    workflow_reset_on_workflow_variable = []

    _properties_form = DTMLFile('zmi/workflow_transition_properties',
                                globals())

    def setProperties(self,
                      title,
                      new_state_id,
                      transition_behavior=None,
                      clone_allowed_transitions=None,
                      checkout_allowed_initial_transitions=None,
                      checkin_allowed_transitions=None,
                      push_on_workflow_variable = None,
                      pop_on_workflow_variable = None,
                      workflow_up_on_workflow_variable = None,
                      workflow_down_on_workflow_variable = None,
                      workflow_reset_on_workflow_variable = None,
                      REQUEST=None,
                      **kw):
        """Set the properties."""
        if transition_behavior is not None:
            self.transition_behavior = tuple(transition_behavior)
        if clone_allowed_transitions is not None:
            self.clone_allowed_transitions = clone_allowed_transitions

        if checkout_allowed_initial_transitions is not None:
            self.checkout_allowed_initial_transitions = \
                checkout_allowed_initial_transitions
        if checkin_allowed_transitions is not None:
            self.checkin_allowed_transitions = checkin_allowed_transitions

        # Stack workflow transition flags
        if push_on_workflow_variable is not None:
            self.push_on_workflow_variable = push_on_workflow_variable
        if pop_on_workflow_variable is not None:
            self.pop_on_workflow_variable = pop_on_workflow_variable
        if workflow_up_on_workflow_variable is not None:
            self.workflow_up_on_workflow_variable = \
                 workflow_up_on_workflow_variable
        if workflow_down_on_workflow_variable is not None:
            self.workflow_down_on_workflow_variable = \
                 workflow_down_on_workflow_variable
        if workflow_reset_on_workflow_variable is not None:
            self.workflow_reset_on_workflow_variable = \
                 workflow_reset_on_workflow_variable

        # Now call original method.
        if REQUEST is not None:
            kw.update(REQUEST.form)
        prkw = {}
        for n in ('trigger_type', 'script_name', 'after_script_name',
                  'actbox_name', 'actbox_url', 'actbox_category',
                  'props', 'description'):
            if kw.has_key(n):
                prkw[n] = kw[n]
        return DCWFTransitionDefinition.setProperties(self,
                                                      title, new_state_id,
                                                      REQUEST=REQUEST,
                                                      **prkw)

    def getAvailableTransitionIds(self):
        return self.getWorkflow().transitions.keys()

    def getStackWorkflowVariablesForBehavior(self, behavior):
        """Returns the variables on wich the transition behavior applies
        """
        _behavior_variables = {
            TRANSITION_BEHAVIOR_PUSH_DELEGATEES :
                self.push_on_workflow_variable,
            TRANSITION_BEHAVIOR_POP_DELEGATEES  :
                self.pop_on_workflow_variable,
            TRANSITION_BEHAVIOR_WORKFLOW_UP   :
                self.workflow_up_on_workflow_variable,
            TRANSITION_BEHAVIOR_WORKFLOW_DOWN :
                self.workflow_down_on_workflow_variable,
            TRANSITION_BEHAVIOR_WORKFLOW_RESET  :
                self.workflow_reset_on_workflow_variable,
            }
        return _behavior_variables.get(behavior, ())

    def _getStackWorkflowFlagsRange(self):
        """Returns the range for stack workflow flags
        """
        return range(40, 50)

    def getAvailableStackWorkflowTransitionFlags(self):
        """Returns the transition flags defined on this transition related to
        stack workflows
        """
        _interested_behaviors = ()
        behaviors = self.transition_behavior
        for behavior in behaviors:
            if behavior in self._getStackWorkflowFlagsRange():
                _interested_behaviors += (behavior,)
        return _interested_behaviors

class Transitions(DCWFTransitions):
    """CPS Transitions

    Extends DC Workflow Transition.  Actually, the goal is to new meta_type and
    use the TransitionDefinition
    """

    meta_type = 'CPS Workflow Transitions'

    all_meta_types = ({'name':TransitionDefinition.meta_type,
                       'action':'addTransition',
                       },)

    def addTransition(self, id, REQUEST=None):
        """Add a new transition to the workflow."""
        tdef = TransitionDefinition(id)
        self._setObject(id, tdef)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Transition added.')

    _manage_transitions = DTMLFile('zmi/workflow_transitions', globals())
