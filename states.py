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

"""CPS Workflow States

Extends DCWorkflow States and DCWorkflow State Definitions.

It adds :

  - CPS States can store stack definitions
  - State bahaviors

Check the documentation within the doc sub-folder
"""

from zLOG import LOG, ERROR, DEBUG

from Globals import DTMLFile

from Products.DCWorkflow.States import StateDefinition as DCWFStateDefinition
from Products.DCWorkflow.States import States as DCWFStates

from stackregistries import WorkflowStackDefRegistry

#
# State behaviors Use for workflow stacks right now.  It permits to allow a
# behavior on the state. You might have shared transitions doing the same job
# on several states.
#

STATE_BEHAVIOR_PUSH_DELEGATEES = 101
STATE_BEHAVIOR_POP_DELEGATEES = 102
STATE_BEHAVIOR_WORKFLOW_UP = 103
STATE_BEHAVIOR_WORKFLOW_DOWN = 104
STATE_BEHAVIOR_RETURNED_UP_HIERARCHY = 105
STATE_BEHAVIOR_WORKFLOW_LOCK = 106
STATE_BEHAVIOR_WORKFLOW_UNLOCK = 107
STATE_BEHAVIOR_WORKFLOW_RESET = 108

state_behavior_export_dict = {
    STATE_BEHAVIOR_PUSH_DELEGATEES : 'Push Delegatees',
    STATE_BEHAVIOR_POP_DELEGATEES  : 'Pop Delegatees',
    STATE_BEHAVIOR_WORKFLOW_UP     : 'Workflow Up',
    STATE_BEHAVIOR_WORKFLOW_DOWN   : 'Workflow Down',
    STATE_BEHAVIOR_RETURNED_UP_HIERARCHY  : 'Return up hierarchy',
    STATE_BEHAVIOR_WORKFLOW_LOCK     : 'Workflow Lock',
    STATE_BEHAVIOR_WORKFLOW_UNLOCK   : 'Workflow UnLock',
    STATE_BEHAVIOR_WORKFLOW_RESET : 'Workflow Reset',
    }

class StateDefinition(DCWFStateDefinition):
    """ CPS State Definition
    """

    meta_type = 'CPS Workflow State'

    manage_options = (
        DCWFStateDefinition.manage_options[0],
        {'label': 'Workflow Stacks',
         'action': 'manage_advanced_properties'},
        ) + DCWFStateDefinition.manage_options[1:]

    _properties_form = DTMLFile(
        'zmi/workflow_state_properties',
        globals())

    _advanced_properties_form = DTMLFile(
        'zmi/workflow_state_advanced_properties',
        globals())

    state_behaviors = ()
    stackdefs = {}

    # State Behaviors depend on a workflow variables
    push_on_workflow_variable = []
    pop_on_workflow_variable = []
    returned_up_hierarchy_on_workflow_variable = []
    workflow_up_on_workflow_variable = []
    workflow_down_on_workflow_variable = []
    workflow_lock_on_workflow_variable = []
    workflow_unlock_on_workflow_variable = []
    workflow_reset_on_workflow_variable = []

    def setProperties(self,
                      title='',
                      description='',
                      transitions=(),
                      state_behaviors=(),
                      stackdefs={},
                      push_on_workflow_variable = None,
                      pop_on_workflow_variable = None,
                      returned_up_hierarchy_on_workflow_variable = None,
                      workflow_up_on_workflow_variable = None,
                      workflow_down_on_workflow_variable = None,
                      workflow_lock_on_workflow_variable = None,
                      workflow_unlock_on_workflow_variable = None,
                      workflow_reset_on_workflow_variable = None,
                      REQUEST=None,
                      **kw
                      ):
        """Set state properties

        DCWorkflow properties / CPS extensions
        """

        self.title = str(title)
        self.description = str(description)
        self.transitions = tuple(map(str, transitions))
        self.state_behaviors = tuple(state_behaviors)

        # Simple edit properties form with no stackdef specified Avoid removing
        # the configuration for stacks if not specified
        if stackdefs:
            self.stackdefs = dict(stackdefs)

        # Stack workflow state behavior flags
        if push_on_workflow_variable is not None:
            self.push_on_workflow_variable = push_on_workflow_variable
        if pop_on_workflow_variable is not None:
            self.pop_on_workflow_variable = pop_on_workflow_variable
        if returned_up_hierarchy_on_workflow_variable is not None:
            self.returned_up_hierarchy_on_workflow_variable = \
                 returned_up_hierarchy_on_workflow_variable
        if workflow_up_on_workflow_variable is not None:
            self.workflow_up_on_workflow_variable = \
                 workflow_up_on_workflow_variable
        if workflow_down_on_workflow_variable is not None:
            self.workflow_down_on_workflow_variable = \
                 workflow_down_on_workflow_variable
        if workflow_lock_on_workflow_variable is not None:
            self.workflow_lock_on_workflow_variable = \
                 workflow_lock_on_workflow_variable
        if workflow_unlock_on_workflow_variable is not None:
            self.workflow_unlock_on_workflow_variable = \
                 workflow_unlock_on_workflow_variable
        if workflow_reset_on_workflow_variable is not None:
            self.workflow_reset_on_workflow_variable = \
                 workflow_reset_on_workflow_variable

        if REQUEST is not None:
            return self.manage_properties(REQUEST, 'Properties changed.')

    def manage_advanced_properties(self,  REQUEST, manage_tabs_message=None):
        """
        """
        return self._advanced_properties_form(
            REQUEST,
            management_view='Advanced Properties',
            manage_tabs_message=manage_tabs_message,)

    #
    # API
    #

    def getStackDefinitions(self):
        """Returns all stack definitions defined on this state
        """
        return self.stackdefs

    def getStackDefinitionFor(self, var_id):
        """Return the stack definition given its id
        """
        return self.getStackDefinitions().get(var_id)

    def addStackDefinition(self, stackdef_type, stack_type, var_id,
                           REQUEST=None, **kw):
        """Add a new stack definition on this state

        stackdef_type : is the stack definition type

        stack_type : stack type (cf. above for the differrent available types

        var_id : workflow variable id used to store this new variable
        """
        self._p_changed = 1
        workflow = self.getWorkflow()

        # www checks
        if not var_id:
            if REQUEST is not None:
                return self.manage_advanced_properties(
                    REQUEST,
                    'You need to specify a variable id')
            return -1
        if not kw.get('ass_local_role'):
            if REQUEST is not None:
                return self.manage_advanced_properties(
                    REQUEST,
                    'Please, specify an associated local roles for this stack')
            return -1

        # Add a workflow variable with new_stack_id as id
        if var_id not in workflow.variables.keys():
            var = workflow.variables.addVariable(var_id)
            var = workflow.variables.get(var_id)
            var.setProperties(
                description="Variable holding a stack",
                default_expr="python:state_change.getStackFor(var_id='%s')" %var_id,
                for_status=1,
                update_always=0)
        else:
            if REQUEST is not None:
                return self.manage_advanced_properties(
                    REQUEST,
                    'The id you choose is already taken !')
            return -1


        stackdef = None

        # Call the stack def registries to get an instance associated to a
        # given stack type
        stackdef = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            stackdef_type,
            stack_type,
            var_id,
            **kw)

        if stackdef is not None:
            stackdefs = self.getStackDefinitions()
            stackdefs[var_id] = stackdef
            self.stackdefs = stackdefs

        if REQUEST is not None:
            return self.manage_advanced_properties(
                REQUEST,
                'New workflow variable defined')

    def delStackDefinitionsById(self, ids=[], REQUEST=None):
        """Remove stack definitions given their ids

        It removes as well the corresponding workflow variable
        """
        self._p_changed = 1
        for id in ids:
            if self.getStackDefinitions().has_key(id):
                workflow = self.getWorkflow()
                try:
                    workflow.variables.deleteVariables([id])
                except KeyError:
                    pass
                del self.stackdefs[id]
        if REQUEST is not None:
            return self.manage_advanced_properties(
                REQUEST,
                'Delegate workflow variables removed !')

    #
    # Misc
    #

    def getAvailableStateBehaviors(self):
        """Get the possible bahavior for the state
        """
        return state_behavior_export_dict

class States(DCWFStates):
    meta_type = 'CPS Workflow States'

    all_meta_types = ({'name':StateDefinition.meta_type,
                       'action':'addState',
                       },)

    def addState(self, id, REQUEST=None):
        """Add a new state to the workflow."""
        sdef = StateDefinition(id)
        self._setObject(id, sdef)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'State added.')
