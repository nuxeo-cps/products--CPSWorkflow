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

from types import StringType, DictType

from Globals import DTMLFile
from OFS.ObjectManager import ObjectManager
from Acquisition import aq_parent, aq_inner, aq_base

from Products.DCWorkflow.States import StateDefinition as DCWFStateDefinition
from Products.DCWorkflow.States import States as DCWFStates

from stackdefinition import StackDefinition
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
STATE_BEHAVIOR_WORKFLOW_RESET = 108

state_behavior_export_dict = {
    STATE_BEHAVIOR_PUSH_DELEGATEES : 'Push Delegatees',
    STATE_BEHAVIOR_POP_DELEGATEES  : 'Pop Delegatees',
    STATE_BEHAVIOR_WORKFLOW_UP     : 'Workflow Up',
    STATE_BEHAVIOR_WORKFLOW_DOWN   : 'Workflow Down',
    STATE_BEHAVIOR_WORKFLOW_RESET : 'Workflow Reset',
    }

class StateDefinition(DCWFStateDefinition, ObjectManager):
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

    _stackdefinition_properties_form = DTMLFile(
        'zmi/workflow_state_stackdef_edit',
        globals()
        )

    state_behaviors = ()
    stackdefs = {}

    # State Behaviors depend on a workflow variables
    push_on_workflow_variable = []
    pop_on_workflow_variable = []
    workflow_up_on_workflow_variable = []
    workflow_down_on_workflow_variable = []
    workflow_reset_on_workflow_variable = []

    def setProperties(self,
                      title='',
                      description='',
                      transitions=(),
                      state_behaviors=(),
                      stackdefs={},
                      push_on_workflow_variable = None,
                      pop_on_workflow_variable = None,
                      workflow_up_on_workflow_variable = None,
                      workflow_down_on_workflow_variable = None,
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

        # Stack defs
        if stackdefs and isinstance(stackdefs, DictType):
            for k, stackdef_conf in stackdefs.items():
                if k in self.getStackDefinitions().keys():
                    self.delStackDefinitionsById(k)
                self.addStackDefinition(**stackdef_conf)

        # Stack workflow state behavior flags
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

        if REQUEST is not None:
            return self.manage_properties(REQUEST, 'Properties changed.')

    def manage_advanced_properties(self,  REQUEST, manage_tabs_message=None):
        """
        """
        return self._advanced_properties_form(
            REQUEST,
            manage_tabs_message=manage_tabs_message,)

    def manage_stackdefinition(self, stackdef_id, REQUEST):
        """
        """
        return self._stackdefinition_properties_form(
            stackdef_id,
            REQUEST)

    #
    # API
    #

    def getStackDefinitions(self):
        """Returns all stack definitions defined on this state
        """
        stackdefs = {}
        for k, v in self.__dict__.items():
            if isinstance(v, StackDefinition):
                stackdefs[k] = self._getOb(k)
        return stackdefs

    def getStackDefinitionFor(self, var_id):
        """Return the stack definition given its id
        """
        return self.getStackDefinitions().get(var_id)

    def addStackDefinition(self, stackdef_type='', stack_type='',
                           var_id='', REQUEST=None, **kw):
        """Add a new stack definition on this state

        stackdef_type : is the stack definition type

        stack_type : stack type (cf. above for the differrent available types

        var_id : workflow variable id used to store this new variable
        """
        self._p_changes = 1

        if REQUEST is not None:
            kw = REQUEST.form

        self._p_changed = 1
        workflow = self.getWorkflow()

        # www checks
        if not var_id:
            if REQUEST is not None:
                return self.manage_advanced_properties(
                    REQUEST,
                    'You need to specify a variable id')
            return -1

        # Add a workflow variable with new_stack_id as id
        if var_id not in workflow.variables.keys():
            var = workflow.variables.addVariable(var_id)
            var = workflow.variables.get(var_id)
            var.setProperties(
                description="Variable holding a stack",
                default_expr="python:state_change.getStackFor(var_id='%s')" %var_id,
                for_status=1,
                update_always=0,
                # XXX AT: not currently possible to set View permission on the
                # stack, because in canManageStack, for instance, we check the
                # stack content to tell if user can edit the stack. When view
                # permission is set, user sees the stacks as anepty stack, the
                # empty stack guard is evaluated.
                #props={'guard_permissions': 'View',},
                )

        stackdef = None

        # Clean the kw before passing it to constructor
        if kw.get('stack_type'):
            del kw['stack_type']

        # Call the stack def registries to get an instance associated to a
        # given stack type
        stackdef = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            stackdef_type,
            stack_type,
            var_id,
            **kw)

        if stackdef is not None:
            if self.getStackDefinitionFor(var_id) is not None:
                self.manage_delObjects([var_id])
            self._setObject(var_id, stackdef)

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
                self._delObject(id)
        if REQUEST is not None:
            return self.manage_advanced_properties(
                REQUEST, 'Delegate workflow variables removed !')

    def updateStackDefinition(self, stackdef_type='', stack_type='',
                              old_wf_var_id='', wf_var_id='', REQUEST=None,
                              **kw):
        """Update an existing stack definition
        """

        # Purge the kw to avoid multiple keyword args while passing the kw
        # to the stack defs constructors.
        if REQUEST is not None:
            kw.update(REQUEST.form)
            for elt in ('stack_type', 'stackdef_type', 'wf_var_id'):
                del kw[elt]

        updated = 0
        # Here stackdef type doesn't change
        stackdef = self.getStackDefinitionFor(old_wf_var_id)
        if stackdef_type == stackdef.meta_type:
            # Workflow variable id doesn't changed
            if old_wf_var_id == wf_var_id:
                stackdef.__init__(stack_type, wf_var_id, **kw)
                updated = 1

        if not updated:
            if (old_wf_var_id != wf_var_id and
                self.getStackDefinitionFor(wf_var_id) is not None):
                # Workflow variable already exists
                if REQUEST is not None:
                    return self.manage_advanced_properties(
                        REQUEST, 'Workflow variable Id already exists !')
            # Save manage_roles
            managed_roles = stackdef._managed_role_exprs
            self.delStackDefinitionsById(ids=[old_wf_var_id])
            self.addStackDefinition(stackdef_type, stack_type, wf_var_id,
                                    REQUEST=None, **kw)
            stackdef = self.getStackDefinitionFor(wf_var_id)
            stackdef._managed_role_exprs = managed_roles

        if REQUEST is not None:
            return self.manage_advanced_properties(
                REQUEST, 'Stack definition updated !')

    def addManagedRoleExpressionFor(self, wf_var_id, role_id, expression,
                                    REQUEST=None):
        """Add managed role expression to a stack definition
        """
        stackdef = self.getStackDefinitionFor(wf_var_id)
        if stackdef is not None:
            stackdef.addManagedRole(role_id, expression)
        if REQUEST is not None:
            return self.manage_advanced_properties(
                REQUEST, 'Stack definition updated !')

    def delManagedRoleExpressionsFor(self, wf_var_id, role_ids, REQUEST=None):
        """Remove managed role expression to a stack definition
        """
        if isinstance(role_ids, StringType):
            role_ids = [role_ids]
        stackdef = self.getStackDefinitionFor(wf_var_id)
        if stackdef is not None:
            for role_id in role_ids:
                stackdef.delManagedRole(role_id)
        if REQUEST is not None:
            return self.manage_advanced_properties(
                REQUEST, 'Stack definition updated !')

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
