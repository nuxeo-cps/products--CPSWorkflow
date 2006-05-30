# -*- coding: iso-8859-15 -*-
# (C) Copyright 2002-2006 Nuxeo SAS <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
# Contributor : Julien Anguenot <ja@nuxeo.com>
#               - Refactoring CPS Workflow
#               - Stack Workflow support (transition flags)
#               - Workflow Guard enhanced
#               - Unit tests
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

"""CPS Workflow

Workflow extending DCWorkflow with enhanced transitions. It adds, as well, a
stack workflow support to be able to define dynamic delegation / validation
chains through dedicated transitions.
"""

from zLOG import LOG, TRACE

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from Acquisition import aq_parent
from Acquisition import aq_inner
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import ObjectMoved
from Products.CMFCore.WorkflowCore import ObjectDeleted
from Products.CMFCore.WorkflowCore import WorkflowException

from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION

from expression import CPSStateChangeInfo as StateChangeInfo
from expression import createExprContext

from zope.interface import implements
from Products.CPSWorkflow.interfaces import ICPSWorkflowDefinition

from Products.CPSCore.ProxyBase import ProxyBase
from Products.CPSCore.EventServiceTool import getEventService

from constants import TRANSITION_FLAGS_EXPORT

#
# Backwards compatibility with CPS3 <= 3.2.x
# Importing transition flags from here before.
#

from Products.CPSWorkflow.transitions import *
from Products.CPSWorkflow.states import *

class WorkflowDefinition(DCWorkflowDefinition):
    """A Workflow implementation with enhanced transitions.

    Features:
    - Extended transition description,
    - Knowledge of proxies.
    """

    implements(ICPSWorkflowDefinition)

    meta_type = 'CPS Workflow'
    title = 'CPS Workflow Definition'
    state_var = 'review_state'

    security = ClassSecurityInfo()

    def __init__(self, id):
        self.id = id
        # CPS versions
        self._addObject(States('states'))
        self._addObject(Transitions('transitions'))
        # Normal DCWorkflow versions
        from Products.DCWorkflow.Variables import Variables
        self._addObject(Variables('variables'))
        from Products.DCWorkflow.Worklists import Worklists
        self._addObject(Worklists('worklists'))
        from Products.DCWorkflow.Scripts import Scripts
        self._addObject(Scripts('scripts'))

    #
    # Overloads
    #

    security.declarePrivate('notifyCreated')
    def notifyCreated(self, ob):
        """Notified when a CMF object has been created.

        Does nothing for CPS as all is done by wftool.invokeFactory.
        """
        pass

    security.declarePrivate('updateStackDefinitionsRoleMappingFor')
    def updateStackDefinitionsRoleMappingsFor(self, ob, **kw):
        """Update local roles for delegatees that are within workflow stacks
        """
        current_wf_var_id = kw.get('current_wf_var_id', '')

        wftool = getToolByName(self, 'portal_workflow')
        stackdefs = wftool.getStackDefinitionsFor(ob)

        changed = 0

        #
        # First save the former local roles maping They will be
        # overriden if defined on the state just after.  For the other
        # ones, we need to keep the flrm's since the stackdef might be
        # defined on another state further within the process
        # definition or called by a stack flaged transition.
        #

        tdef = kw.get('tdef')
        history = wftool.getHistoryOf(self.id, ob)
        try:
            former_status = history[-2]
        except IndexError:
            # Virgin instance ;)
            pass
        else:
            sflrm = former_status.get('sflrm', {})
            for k, v in sflrm.items():
                wftool.updateFormerLocalRoleMappingForStack(ob, self.id,
                                                                k, v)

        #
        # Let's ask the stack definition for the list of local roles
        #

        for stackdef in stackdefs.keys():

            # Update only the variable on wich the transition just applied
            if not stackdef == current_wf_var_id:
                continue

            ds = wftool.getInfoFor(ob, stackdef, self.id)
            former_mapping = wftool.getFormerLocalRoleMappingForStack(
                ob, self.id, stackdef)
            mapping = stackdefs[stackdef]._getLocalRolesMapping(ds)

            #
            # First remove associated local roles to the ones who are not
            # supposed to have any (not a single one)
            #

            for id in former_mapping.keys():
                old_local_roles = former_mapping[id]

                # Remove all previous local roles in this case
                if id not in mapping.keys():
                    roles_to_remove = old_local_roles

                # Remove only local roles that are only within the
                # previous mapping
                else:
                    roles_to_remove = []
                    for old_role in old_local_roles:
                        if old_role not in mapping[id]:
                            roles_to_remove.append(old_role)


                # Check that no other stack distributes currently this role
                # to the current member
                roles_to_keep = ()
                for old_local_role in roles_to_remove:
                    stacks = wftool.getStacks(ob)
                    for stack_id, stack in stacks.items():
                        if stack_id != current_wf_var_id:
                            # The current transition is already
                            # executed on ob thus we can take the
                            # former mapping for this other given
                            if (old_local_role in
                                wftool.getFormerLocalRoleMappingForStack(
                                ob, self.id, stack_id).get(id, ())):
                                roles_to_keep += (old_local_role,)

                # Do the actual job to remove absolete roles
                for old_local_role in roles_to_remove:

                    # Don't remove those already managed by another stack
                    if old_local_role in roles_to_keep:
                        continue

                    if not id.startswith('group:'):
                        current_roles = list(
                            ob.get_local_roles_for_userid(userid=id))
                        new_roles = [role for role in current_roles
                                     if role != old_local_role]
                        ob.manage_delLocalRoles(userids=[id])
                        if new_roles:
                            ob.manage_setLocalRoles(id, new_roles)
                    else:
                        id = id[len('group:'):]
                        current_roles = list(
                            ob.get_local_roles_for_groupid(groupid=id))
                        new_roles = [role for role in current_roles
                                     if role != old_local_role]
                        ob.manage_delLocalGroupRoles(groupids=[id])
                        if new_roles:
                            ob.manage_setLocalGroupRoles(id, new_roles)

                # Update ?
                if roles_to_remove:
                    changed = 1

            #
            # Add local roles to member / groups within the mapping if
            # they don't have the roles already in their merged local roles
            #

            for id in mapping.keys():
                changed = 1
                local_roles = mapping[id]
                if not id.startswith('group:'):
                    current_roles = ob.get_local_roles_for_userid(userid=id)
                    new_roles = list(current_roles)
                    for role in local_roles:
                        if role not in new_roles:
                            new_roles.append(role)
                    ob.manage_setLocalRoles(id, new_roles)
                else:
                    id = id[len('group:'):]
                    current_roles = ob.get_local_roles_for_groupid(groupid=id)
                    new_roles = list(current_roles)
                    for role in local_roles:
                        if role not in new_roles:
                            new_roles.append(role)
                    ob.manage_setLocalGroupRoles(id, new_roles)

            # Update the former local role mapping
            wftool.updateFormerLocalRoleMappingForStack(ob, self.id, stackdef,
                                                        mapping)
        return changed

    def updateRoleMappingsFor(self, ob, **kw):
        """Change the object permissions according to the current state.

        Change the local roles of the people eventually within workflow
        stacks according to stackdefinition rules.

        Returns True if some change on an object was done.
        """

        # Update permissions according to the current state
        changed = DCWorkflowDefinition.updateRoleMappingsFor(self, ob)

        # Update Local roles according the workflow stack definitions rules
        stackdefs_changed = self.updateStackDefinitionsRoleMappingsFor(ob,
                                                                       **kw)

        return (changed and stackdefs_changed)

    def _checkStackGuards(self, t, ob, **kw):
        """Check the stack workflow transition guards on the transition for ob

        If one of them allowed the user to manage the stack it means the user
        is allowed to follow the transition
        """

        wftool = aq_parent(aq_inner(self))
        _interested_behaviors = t.getAvailableStackWorkflowTransitionFlags()

        # Check if stack workflow flags are defined on the transition
        if not _interested_behaviors:
            return 1

        #
        # Now check each interesting behaviors on this transition We will check
        # if the current authenticated user can manage one of the stack related
        # to the behavior
        #

        for behavior in _interested_behaviors:
            var_ids = t.getStackWorkflowVariablesForBehavior(behavior)
            for var_id in var_ids:

                if wftool.canManageStack(ob, var_id, **kw):


                    #
                    # Check in here if the transition flag is compatible with
                    # the current stack and stackdef context
                    #

                    stack = wftool.getStackFor(ob, var_id)
                    if var_id in t.workflow_down_on_workflow_variable:
                        if (not stack or
                            not stack.hasLowerLevel()):
                            return 0

                    if var_id in t.workflow_up_on_workflow_variable:
                        if (not stack or
                            not stack.hasUpperLevel()):
                            return 0

                    # XXX cope with other cases if needed
                    return 1

        return 0

    def _checkTransitionGuard(self, t, ob, **kw):
        """Check the transition guard

        DC workflow + stack def checks
        """
        guard = t.guard
        return (guard is None or
                guard.check(getSecurityManager(), self, ob, **kw) and
                self._checkStackGuards(t, ob, **kw))

    def _changeStateOf(self, ob, tdef=None, kwargs=None):
        """
        Changes state.  Can execute multiple transitions if there are
        automatic transitions.
        If on a CMF site tdef set to None means the object
        was just created.
        Of on a CPS site tdef is not None but has a TRANSITION_INITIAL_CREATE
        """
        moved_exc = None
        while 1:
            try:
                sdef = self._executeTransition(ob, tdef, kwargs)
            except ObjectMoved, moved_exc:
                ob = moved_exc.getNewObject()
                sdef = self._getWorkflowStateOf(ob)
                # Re-raise after all transitions.
            if sdef is None:
                break
            # look for automatic transitions
            tdef = self._findAutomaticTransition(ob, sdef)
            if tdef is None:
                # No more automatic transitions.
                break
            # Else continue.
        if moved_exc is not None:
            # Re-raise.
            raise moved_exc

    def _executeTransition(self, ob, tdef=None, kwargs=None):
        """Put the object in a new state, following transition tdef.

        Can be called at creation, when there is no current workflow
        state.
        """

        sci = None
        econtext = None
        moved_exc = None
        utool = getToolByName(self, 'portal_url') # CPS
        wftool = aq_parent(aq_inner(self))
        evtool = getEventService(self)

        # Get the stack ds defined for this object in this current state
        # If it's the creation time no stacks are defined
        stacks = wftool.getStacks(ob)

        # Figure out the old and new states.
        old_sdef = self._getWorkflowStateOf(ob)
        ### CPS: Allow initial transitions to have no old state.
        #
        if old_sdef is not None:
            old_state = old_sdef.getId()
        else:
            old_state = None
        #
        ###
        if tdef is None:
            # CPS: tdef is never None for CPSWorkflow
            raise WorkflowException('No transition!')
            #new_state = self.initial_state
            #former_status = {}
        else:
            new_state = tdef.new_state_id
            if not new_state:
                # Stay in same state.
                new_state = old_state
            former_status = self._getStatusOf(ob)
        new_sdef = self.states.get(new_state, None)
        if new_sdef is None:
            raise WorkflowException, (
                "Destination state '%s' undefined for "
                "transition '%s' in workflow '%s'" %(
                new_state, tdef.getId(), self.getId()))


        ### CPS: Behavior sanity checks.
        #
        behavior = tdef.transition_behavior
        LOG('CPSWorkflow', TRACE, 'Behavior in wf %s, trans %s: %s'
            % (self.getId(), tdef.getId(), behavior))
        kwargs = kwargs.copy() # Because we'll modify it.

        if TRANSITION_BEHAVIOR_MOVE in behavior:
            raise NotImplementedError
            ## Check allowed from source container.
            #src_container = aq_parent(aq_inner(ob))
            #ok, why = wftool.isBehaviorAllowedFor(src_container,
            #                                     TRANSITION_ALLOWSUB_MOVE,
            #                                     get_details=1)
            #if not ok:
            #    raise WorkflowException("src_container=%s does not allow "
            #                            "subobject move (%s)" %
            #                            (src_container.getId(), why))
            ## Now check dest container.
            #dest_container = kwargs.get('dest_container')
            #if dest_container is None:
            #    raise WorkflowException('Missing dest_container for move '
            #                            'transition=%s' % tdef.getId())
            #dest_container = self._objectMaybeFromRpath(dest_container)
            #ok, why = wftool.isBehaviorAllowedFor(dest_container, #XXXincorrect
            #                                     TRANSITION_INITIAL_MOVE,
            #                                  transition=self.dest_transition,
            #                                     get_details=1)
            #if not ok:
            #    raise WorkflowException("dst_container=%s does not allow "
            #                            "object initial move (%s)" %
            #                            (dst_container.getId(), why))
            #XXX now do move (recreate into dest container)
            #XXX raise ObjectDeleted ??? ObjectMoved ???
        if TRANSITION_BEHAVIOR_COPY in behavior:
            raise NotImplementedError
            #XXX
        if TRANSITION_BEHAVIOR_PUBLISHING in behavior:
            dest_container = kwargs.get('dest_container')
            if dest_container is None:
                raise WorkflowException("Missing dest_container for publishing"
                                        " transition=%s for ob=%s" %
                                        (tdef.getId(), ob))
            dest_container = self._objectMaybeFromRpath(dest_container)
            # Put it back so that it's useable from variables.
            kwargs['dest_container'] = utool.getRelativeUrl(dest_container)
            initial_transition = kwargs.get('initial_transition')
            if initial_transition is None:
                raise WorkflowException("Missing initial_transition for "
                                        "publishing transition=%s" %
                                        tdef.getId())
            if initial_transition not in tdef.clone_allowed_transitions:
                raise WorkflowException("Incorrect initial_transition %s, "
                                        "allowed=%s"
                                        % (initial_transition,
                                           tdef.clone_allowed_transitions))
        if TRANSITION_BEHAVIOR_CHECKOUT in behavior:
            dest_container = kwargs.get('dest_container')
            if dest_container is None:
                raise WorkflowException("Missing dest_container for checkout"
                                        " transition=%s" % tdef.getId())
            dest_container = self._objectMaybeFromRpath(dest_container)
            kwargs['dest_container'] = utool.getRelativeUrl(dest_container)
            initial_transition = kwargs.get('initial_transition')
            if initial_transition is None:
                raise WorkflowException("Missing initial_transition for "
                                        "checkout transition=%s" %
                                        tdef.getId())
            if initial_transition not in \
                    tdef.checkout_allowed_initial_transitions:
                raise WorkflowException("Incorrect initial_transition %s, "
                                        "allowed=%s"
                                        % (initial_transition,
                                    tdef.checkout_allowed_initial_transitions))
            language_map = kwargs.get('language_map')
        if TRANSITION_BEHAVIOR_CHECKIN in behavior:
            dest_objects = kwargs.get('dest_objects')
            if dest_objects is None:
                raise WorkflowException("Missing dest_objects for checkin"
                                        " transition=%s" % tdef.getId())
            dest_objects = [self._objectMaybeFromRpath(d)
                            for d in dest_objects]
            kwargs['dest_objects'] = [utool.getRelativeUrl(d)
                                      for d in dest_objects]
            checkin_transition = kwargs.get('checkin_transition')
            if checkin_transition is None:
                raise WorkflowException("Missing checkin_transition for "
                                        "checkin transition=%s" % tdef.getId())
            if checkin_transition not in tdef.checkin_allowed_transitions:
                raise WorkflowException("Incorrect checkin_transition %s, "
                                        "allowed=%s"
                                        % (checkin_transition,
                                           tdef.checkin_allowed_transitions))
            for dest_object in dest_objects:
                # Check that they have the same docid.
                if ob.getDocid() != dest_object.getDocid():
                    raise WorkflowException("Cannot checkin into different "
                                            "docid")
                # Check that the default language is still the same than
                # when we did checkout. # XXX We want to be more flexible.
                lang = ob.getDefaultLanguage()
                if (ob._getFromLanguageRevisions().get(lang, 1) !=
                    dest_object._getLanguageRevisions().get(lang, 2)):
                    raise WorkflowException("Cannot checkin into changed "
                                            "document %s" %
                                       '/'.join(dest_object.getPhysicalPath()))
        if TRANSITION_BEHAVIOR_DELETE in behavior:
            pass
            ## XXX Check that container allows delete.
            #container = aq_parent(aq_inner(ob))
            #ok, why = wftool.isBehaviorAllowedFor(container,
            #                                     TRANSITION_ALLOWSUB_DELETE,
            #                                     get_details=1)
            #if not ok:
            #    raise WorkflowException("Container=%s does not allow "
            #                            "subobject deletion (%s)" %
            #                            (container.getId(), why))
        #
        ###

        # Execute the "before" script.
        if tdef is not None and tdef.script_name:
            script = self.scripts[tdef.script_name]
            # Pass lots of info to the script in a single parameter.
            sci = StateChangeInfo(
                ob, self, former_status, tdef, old_sdef, new_sdef, stacks, kwargs, )
            try:
                script(sci)  # May throw an exception.
            except ObjectMoved, moved_exc:
                ob = moved_exc.getNewObject()
                # Re-raise after transition

        ### CPS: Behavior.
        #

        delete_ob = None

        if TRANSITION_BEHAVIOR_MOVE in behavior:
            raise NotImplementedError
            #XXX now do move (recreate into dest container)
            #XXX raise ObjectDeleted ??? ObjectMoved ???

        if TRANSITION_BEHAVIOR_COPY in behavior:
            raise NotImplementedError
            #XXX

        if TRANSITION_BEHAVIOR_PUBLISHING in behavior:
            wftool.cloneObject(ob, dest_container, initial_transition, kwargs)

        if TRANSITION_BEHAVIOR_CHECKOUT in behavior:
            wftool.checkoutObject(ob, dest_container, initial_transition,
                                  language_map, kwargs)

        if TRANSITION_BEHAVIOR_CHECKIN in behavior:
            for dest_object in dest_objects:
                wftool.checkinObject(ob, dest_object, checkin_transition)
            # Now delete the original object.
            delete_ob = ob

        if TRANSITION_BEHAVIOR_FREEZE in behavior:
            # Freeze the object.
            if isinstance(ob, ProxyBase):
                # XXX use an event?

                ob.freezeProxy()
                ob.proxyChanged()

        if TRANSITION_BEHAVIOR_DELETE in behavior:
            delete_ob = ob

        if TRANSITION_BEHAVIOR_MERGE in behavior:
            container = aq_parent(aq_inner(ob))
            dest_ob = wftool.mergeObject(ob, container,
                                         self.state_var, new_state)
            if dest_ob is not None:
                delete_ob = ob
                # Provide info to the UI to get a correct redirect.
                res = ('ObjectMoved', utool.getRelativeUrl(dest_ob))
                moved_exc = ObjectMoved(dest_ob, res)
                ob = dest_ob

        #################################################
        #              Stack workflows cases
        ##################################################

        if TRANSITION_BEHAVIOR_PUSH_DELEGATEES in behavior:

            LOG("::CPSWorkflow._executeTansition() :: "
                "FLAG : TRANSITION_BEHAVIOR_PUSH_DELEGATEES",
                TRACE,
                str(kwargs))

            #
            # Get the stack definitions from the transition definition
            # The workflow variable id is the stackdef id.
            #

            sdef_behaviors = new_sdef.state_behaviors
            push_allowed_on_variables = new_sdef.push_on_workflow_variable

            #
            # First check if the state allows the behavior
            # Raise an exception if not allowed
            #

            if STATE_BEHAVIOR_PUSH_DELEGATEES not in sdef_behaviors:
                raise WorkflowException(
                    "State behavior not allowed for '%s' on '%s'" %(
                    STATE_BEHAVIOR_PUSH_DELEGATEES,
                    new_sdef.getId(),
                    ))

            wf_vars = tdef.push_on_workflow_variable

            #
            # Raise an exception if not variables are associated to the
            # transition flag. Mostly for debuging right now. It's anyway a
            # problem of configuration
            #

            if not wf_vars:
                raise WorkflowException(
                    "Transition %s needs associated variables to execute on" %(
                    TRANSITION_BEHAVIOR_PUSH_DELEGATEES,
                    ))

            for wf_var in wf_vars:

                #
                # Filter on the working workflow variable It's necessarly since
                # the transition can be allowed on several wf variable id
                #

                current_wf_var_id = kwargs.get('current_wf_var_id', '')
                if current_wf_var_id != wf_var:
                    continue

                #
                # Check here if the behavior is allowed by the state for this
                # given worfklow variable id
                #

                if wf_var not in push_allowed_on_variables:
                    raise WorkflowException(
                        "State %s dosen't allow '%s' on var '%s'" %(
                        new_sdef.getId(),
                        STATE_BEHAVIOR_PUSH_DELEGATEES,
                        wf_var,
                        ))

                stackdef = new_sdef.getStackDefinitionFor(wf_var)
                if stackdef is not None:
                    ds = stacks.get(wf_var)
                    stacks[wf_var] = stackdef._push(ds, **kwargs)

        if TRANSITION_BEHAVIOR_POP_DELEGATEES in behavior:

            LOG("::CPSWorkflow._executeTansition() :: "
                "FLAG : TRANSITION_BEHAVIOR_POP_DELEGATEES",
                TRACE,
                str(kwargs))

            #
            # Get the stack definitions from the transition definition
            # The workflow variable id is the stackdef id.
            #


            sdef_behaviors = new_sdef.state_behaviors
            pop_allowed_on_variables = new_sdef.pop_on_workflow_variable

            #
            # First check if the state allows the behavior
            # Raise an exception if not allowed
            #

            if STATE_BEHAVIOR_POP_DELEGATEES not in sdef_behaviors:
                raise WorkflowException(
                    "State behavior not allowed for '%s' on '%s'" %(
                    STATE_BEHAVIOR_POP_DELEGATEES,
                    new_sdef.getId(),
                    ))

            wf_vars = tdef.pop_on_workflow_variable

            #
            # Raise an exception if not variables are associated to the
            # transition flag. Mostly for debuging right now. It's anyway a
            # problem of configuration
            #

            if not wf_vars:
                raise WorkflowException(
                    "Transition %s needs associated variables to execute on" %(
                    TRANSITION_BEHAVIOR_POP_DELEGATEES,
                    ))

            for wf_var in wf_vars:

                #
                # Filter on the working workflow variable It's necessarly since
                # the transition can be allowed on several wf variable id
                #
                current_wf_var_id = kwargs.get('current_wf_var_id', '')
                if current_wf_var_id != wf_var:
                    continue

                #
                # Check here if the behavior is allowed by the state for this
                # given worfklow variable id
                #

                if wf_var not in pop_allowed_on_variables:
                    raise WorkflowException(
                        "State %s dosen't allow '%s' on var '%s'" %(
                        new_sdef.getId(),
                        STATE_BEHAVIOR_POP_DELEGATEES,
                        wf_var,
                        ))

                stackdef = new_sdef.getStackDefinitionFor(wf_var)
                if stackdef is not None:
                    ds = stacks.get(wf_var)
                    stacks[wf_var] = stackdef._pop(ds, **kwargs)

        if TRANSITION_BEHAVIOR_EDIT_DELEGATEES in behavior:
            LOG("::CPSWorkflow._executeTansition() :: "
                "FLAG : TRANSITION_BEHAVIOR_EDIT_DELEGATEES",
                TRACE,
                str(kwargs))

            #
            # Get the stack definitions from the transition definition
            # The workflow variable id is the stackdef id.
            #

            sdef_behaviors = new_sdef.state_behaviors
            edit_allowed_on_variables = new_sdef.edit_on_workflow_variable

            #
            # First check if the state allows the behavior
            # Raise an exception if not allowed
            #

            if STATE_BEHAVIOR_EDIT_DELEGATEES not in sdef_behaviors:
                raise WorkflowException(
                    "State behavior not allowed for '%s' on '%s'" %(
                    STATE_BEHAVIOR_EDIT_DELEGATEES,
                    new_sdef.getId(),
                    ))

            wf_vars = tdef.edit_on_workflow_variable

            #
            # Raise an exception if not variables are associated to the
            # transition flag. Mostly for debuging right now. It's anyway a
            # problem of configuration
            #

            if not wf_vars:
                raise WorkflowException(
                    "Transition %s needs associated variables to execute on" %(
                    TRANSITION_BEHAVIOR_EDIT_DELEGATEES,
                    ))

            for wf_var in wf_vars:

                #
                # Filter on the working workflow variable It's necessarly since
                # the transition can be allowed on several wf variable id
                #

                current_wf_var_id = kwargs.get('current_wf_var_id', '')
                if current_wf_var_id != wf_var:
                    continue

                #
                # Check here if the behavior is allowed by the state for this
                # given worfklow variable id
                #

                if wf_var not in edit_allowed_on_variables:
                    raise WorkflowException(
                        "State %s dosen't allow '%s' on var '%s'" %(
                        new_sdef.getId(),
                        STATE_BEHAVIOR_EDIT_DELEGATEES,
                        wf_var,
                        ))

                stackdef = new_sdef.getStackDefinitionFor(wf_var)
                if stackdef is not None:
                    ds = stacks.get(wf_var)
                    stacks[wf_var] = stackdef._edit(ds, **kwargs)

        if TRANSITION_BEHAVIOR_WORKFLOW_UP in behavior:

            LOG("::CPSWorkflow._executeTansition() :: "
                "FLAG : TRANSITION_BEHAVIOR_WORKFLOW_UP",
                TRACE,
                str(kwargs))

            #
            # Get the stack definitions from the transition definition
            # The workflow variable id is the stackdef id.
            #

            sdef_behaviors = new_sdef.state_behaviors
            up_vars = new_sdef.workflow_up_on_workflow_variable

            #
            # First check if the state allows the behavior
            # Raise an exception if not allowed
            #

            if STATE_BEHAVIOR_WORKFLOW_UP not in sdef_behaviors:
                raise WorkflowException(
                    "State behavior not allowed for '%s' on '%s'" %(
                    STATE_BEHAVIOR_WORKFLOW_UP,
                    new_sdef.getId(),
                    ))

            wf_vars = tdef.workflow_up_on_workflow_variable

            #
            # Raise an exception if not variables are associated to the
            # transition flag. Mostly for debuging right now. It's anyway a
            # problem of configuration
            #

            if not wf_vars:
                raise WorkflowException(
                    "Transition %s needs associated variables to execute on" %(
                    TRANSITION_BEHAVIOR_WORKFLOW_UP,
                    ))

            for wf_var in wf_vars:

                #
                # Filter on the working workflow variable It's necessarly since
                # the transition can be allowed on several wf variable id
                #

                current_wf_var_id = kwargs.get('current_wf_var_id', '')
                if current_wf_var_id != wf_var:
                    continue

                #
                # Check here if the behavior is allowed by the state for this
                # given worfklow variable id
                #

                if wf_var not in up_vars:
                    raise WorkflowException(
                        "State %s dosen't allow '%s' on var '%s'" %(
                        new_sdef.getId(),
                        STATE_BEHAVIOR_WORKFLOW_UP,
                        wf_var,
                        ))

                stackdef = new_sdef.getStackDefinitionFor(wf_var)
                if stackdef is not None:
                    ds = stacks.get(wf_var)
                    stacks[wf_var] = stackdef._doIncLevel(ds)

        if TRANSITION_BEHAVIOR_WORKFLOW_DOWN in behavior:

            LOG("::CPSWorkflow._executeTansition() :: "
                "FLAG : TRANSITION_BEHAVIOR_WORKFLOW_DOWN",
                TRACE,
                str(kwargs))

            #
            # Get the stack definitions from the transition definition
            # The workflow variable id is the stackdef id.
            #

            sdef_behaviors = new_sdef.state_behaviors
            down_vars = new_sdef.workflow_down_on_workflow_variable

            #
            # First check if the state allows the behavior
            # Raise an exception if not allowed
            #

            if STATE_BEHAVIOR_WORKFLOW_DOWN not in sdef_behaviors:
                raise WorkflowException(
                    "State behavior not allowed for '%s' on '%s'" %(
                    STATE_BEHAVIOR_WORKFLOW_DOWN,
                    new_sdef.getId(),
                    ))

            wf_vars = tdef.workflow_down_on_workflow_variable

            #
            # Raise an exception if not variables are associated to the
            # transition flag. Mostly for debuging right now. It's anyway a
            # problem of configuration
            #

            if not wf_vars:
                raise WorkflowException(
                    "Transition %s needs associated variables to execute on" %(
                    TRANSITION_BEHAVIOR_WORKFLOW_DOWN,
                    ))

            for wf_var in wf_vars:

                #
                # Filter on the working workflow variable It's necessarly since
                # the transition can be allowed on several wf variable id
                #

                current_wf_var_id = kwargs.get('current_wf_var_id', '')
                if current_wf_var_id != wf_var:
                    continue

                #
                # Check here if the behavior is allowed by the state for this
                # given worfklow variable id
                #

                if wf_var not in down_vars:
                    raise WorkflowException(
                        "State %s dosen't allow '%s' on var '%s'" %(
                        new_sdef.getId(),
                        STATE_BEHAVIOR_WORKFLOW_DOWN,
                        wf_var,
                        ))

                stackdef = new_sdef.getStackDefinitionFor(wf_var)
                if stackdef is not None:
                    ds = stacks.get(wf_var)
                    stacks[wf_var] = stackdef._doDecLevel(ds)


        if TRANSITION_BEHAVIOR_WORKFLOW_RESET in behavior:

            LOG("::CPSWorkflow._executeTansition() :: "
                "FLAG : TRANSITION_BEHAVIOR_WORKFLOW_RESET",
                TRACE,
                str(kwargs))

            #
            # Get the stack definitions from the transition definition
            # The workflow variable id is the stackdef id.
            #

            sdef_behaviors = new_sdef.state_behaviors
            reset_vars = new_sdef.workflow_reset_on_workflow_variable

            #
            # First check if the state allows the behavior
            # Raise an exception if not allowed
            #

            if STATE_BEHAVIOR_WORKFLOW_RESET not in sdef_behaviors:
                raise WorkflowException(
                    "State behavior not allowed for '%s' on '%s'" %(
                    STATE_BEHAVIOR_WORKFLOW_RESET,
                    new_sdef.getId(),
                    ))

            wf_vars = tdef.workflow_reset_on_workflow_variable

            #
            # Raise an exception if not variables are associated to the
            # transition flag. Mostly for debuging right now. It's anyway a
            # problem of configuration
            #

            if not wf_vars:
                raise WorkflowException(
                    "Transition %s needs associated variables to execute on" %(
                    TRANSITION_BEHAVIOR_WORKFLOW_RESET,
                    ))

            for wf_var in wf_vars:

                #
                # Filter on the working workflow variable It's necessarly since
                # the transition can be allowed on several wf variable id
                #

                current_wf_var_id = kwargs.get('current_wf_var_id', '')

                if current_wf_var_id != wf_var:
                    continue

                #
                # Check here if the behavior is allowed by the state for this
                # given worfklow variable id
                #

                if wf_var not in reset_vars:
                    raise WorkflowException(
                        "State %s dosen't allow '%s' on var '%s'" %(
                        new_sdef.getId(),
                        STATE_BEHAVIOR_WORKFLOW_RESET,
                        wf_var,
                        ))

                stackdef = new_sdef.getStackDefinitionFor(wf_var)
                if stackdef is not None:
                    ds = stacks.get(wf_var)
                    stacks[wf_var] = stackdef._reset(ds, **kwargs)

        #
        # Update variables.
        #

        state_values = new_sdef.var_values
        if state_values is None:
            state_values = {}
        tdef_exprs = None
        if tdef is not None:
            tdef_exprs = tdef.var_exprs
        if tdef_exprs is None:
            tdef_exprs = {}
        status = {}
        for id, vdef in self.variables.items():
            if not vdef.for_status:
                continue
            expr = None
            if state_values.has_key(id):
                value = state_values[id]
            elif tdef_exprs.has_key(id):
                expr = tdef_exprs[id]
            # FIXME AT: stack variables are set to update_always=0, so are not
            # updated here, which is a problem on some use cases (CPSCourrier
            # reset transition).
            # options:
            # - set update_always=1 on stack variables (if ok, but will not be
            #   compatible with existing stacks)
            # - check the update_always property here only if variable is not a
            #   stack variable -> implemented here
            elif (id not in stacks.keys()
                  and not vdef.update_always
                  and former_status.has_key(id)):
                # Preserve former value
                value = former_status[id]
            else:
                if vdef.default_expr is not None:
                    expr = vdef.default_expr
                else:
                    value = vdef.default_value
            if expr is not None:
                # Evaluate an expression.
                if econtext is None:
                    # Lazily create the expression context.
                    if sci is None:
                        sci = StateChangeInfo(
                            ob, self, former_status, tdef,
                            old_sdef, new_sdef, stacks, kwargs)
                    econtext = createExprContext(sci)
                value = expr(econtext)

            status[id] = value

        # update stack variables, initializing stacks defined in given state
        stacks = {}
        stackdefs = new_sdef.getStackDefinitions()
        for stackdef_id, stackdef in stackdefs.items():
            # stack is a variable, it has just been updated in the status
            if status[stackdef_id] is None:
                # Construct stack instance
                new_stack = stackdef._prepareStack(None)
                status[stackdef_id] = new_stack

        # Update state.
        status[self.state_var] = new_state
        tool = aq_parent(aq_inner(self))
        tool.setStatusOf(self.id, ob, status)

        # Update role to permission assignments.
        kw = {}
        kw['current_wf_var_id'] = kwargs.get('current_wf_var_id', '')
        kw['tdef'] = tdef
        self.updateRoleMappingsFor(ob, **kw)

        # Execute the "after" script.
        if tdef is not None and tdef.after_script_name:
            script = self.scripts[tdef.after_script_name]
            # Taking care of the case of an "after" script for a deleted object.
            # The condition delete_ob == ob is here to make sure we don't reset
            # ob in case of a TRANSITION_BEHAVIOR_MERGE.
            if delete_ob is not None and delete_ob == ob:
                ob = None
            # Pass lots of info to the script in a single parameter.
            sci = StateChangeInfo(
                ob, self, status, tdef, old_sdef, new_sdef, stacks, kwargs)
            script(sci)  # May throw an exception.

        ### CPS: Delete. Done after setting status, to keep history.
        #
        if delete_ob is not None:
            # XXX refactoring.
            evtool.notify('workflow_%s' % tdef.getId(),
                          delete_ob, {'kwargs': kwargs})
            container = aq_parent(aq_inner(delete_ob))
            container._delObject(delete_ob.getId())
            if moved_exc is not None:
                raise moved_exc
            else:
                raise ObjectDeleted

        ### CPS: Event notification. This has to be done after all the
        # potential transition scripts.
        #
        # XXX pass a whole sci ?
        evtool.notify('workflow_%s' % tdef.getId(), ob, {'kwargs': kwargs})
        #
        ###

        # Return the new state object.
        if moved_exc is not None:
            # Propagate the notification that the object has moved.
            raise moved_exc
        else:
            return new_sdef

    #
    # API
    #

    security.declarePrivate('getInfoFor')
    def getInfoFor(self, ob, name, default):
        """Allows the user to request information provided by the workflow.
        This method must perform its own security checks.

        The method is overrided because we need to use the StateChangeInfo
        defined within the CPSWorkflow.expression
        """
        if name == self.state_var:
            return self._getWorkflowStateOf(ob, 1)
        vdef = self.variables[name]
        if vdef.info_guard is not None and not vdef.info_guard.check(
            getSecurityManager(), self, ob):
            return default
        status = self._getStatusOf(ob)
        if status is not None and status.has_key(name):
            value = status[name]

        # Not set yet.  Use a default.
        elif vdef.default_expr is not None:
            ec = createExprContext(StateChangeInfo(ob, self, status))
            value = vdef.default_expr(ec)
        else:
            value = vdef.default_value
        return value

    security.declarePrivate('insertIntoWorkflow')
    def insertIntoWorkflow(self, ob, initial_transition, initial_behavior,
                           kwargs):
        """Insert an object into the workflow.

        The guard on the initial transition is evaluated in the
        context of the container of the object.

        (Called by WorkflowTool when inserting an object into the workflow
        after a create, copy, publishing, etc.)
        """
        tdef = self.transitions.get(initial_transition, None)
        if tdef is None:
            raise WorkflowException("No initial transition '%s' "
                                    "in workflow '%s'" %
                                    (initial_transition, self.getId()))
        # Check it's really an initial transition.
        if initial_behavior not in tdef.transition_behavior:
            raise WorkflowException("workflow=%s transition=%s"
                                    " not a behavior=%s" %
                                    (self.getId(), initial_transition,
                                     initial_behavior))
        container = aq_parent(aq_inner(ob))
        if not self._checkTransitionGuard(tdef, container, **kwargs):
            raise WorkflowException("Unauthorized transition %s"
                                    % initial_transition)
        self._changeStateOf(ob, tdef, kwargs)


    security.declarePrivate('isBehaviorAllowedFor')
    def isBehaviorAllowedFor(self, ob, behavior, transition=None,
                             get_details=0):
        """Is the behavior allowed?

        Tests that the specified behavior is allowed in a transition.

        If transition is present, only check a transition with this name.
        """
        LOG('WF', TRACE, 'isBehaviorAllowedFor ob=%s wf=%s beh=%s'
            % (ob.getId(), self.getId(), behavior))
        sdef = self._getWorkflowStateOf(ob)
        if sdef is None:
            if get_details:
                return 0, 'no state'
            else:
                return 0
        res = []
        for tid in sdef.transitions:
            if transition is not None and transition != tid:
                continue
            LOG('WF', TRACE, ' Test transition %s' % tid)
            tdef = self.transitions.get(tid, None)
            if tdef is None:
                continue
            if behavior not in tdef.transition_behavior:
                LOG('WF', TRACE, '  Not a %s' % (behavior,))
                continue
            if not self._checkTransitionGuard(tdef, ob):
                LOG('WF', TRACE, '  Guard failed')
                continue
            LOG('WF', TRACE, '  Ok')
            if get_details:
                return 1, ''
            else:
                return 1
        if get_details:
            friendly_behavior = TRANSITION_FLAGS_EXPORT.get(behavior, behavior)
            return 0, ('state=%s (transition=%s) has no behavior=%s'
                       % (sdef.getId(), transition, friendly_behavior))
        else:
            return 0

    security.declarePrivate('getAllowedPublishingTransitions')
    def getAllowedPublishingTransitions(self, ob):
        """Get the list of allowed initial transitions for publishing."""
        sdef = self._getWorkflowStateOf(ob)
        if sdef is None:
            return []
        d = {}
        for tid in sdef.transitions:
            tdef = self.transitions.get(tid, None)
            if tdef is None:
                continue
            if TRANSITION_BEHAVIOR_PUBLISHING not in tdef.transition_behavior:
                continue
            if not self._checkTransitionGuard(tdef, ob):
                continue
            for t in tdef.clone_allowed_transitions:
                d[t] = None
        return d.keys()

    security.declarePrivate('getInitialTransitions')
    def getInitialTransitions(self, context, behavior):
        """Get the possible initial transitions in a context according to
        this workflow.

        context: the context in which the guard is evaluated.

        behavior: the type of initial transition to check for.

        Returns a sequence of transition names.
        """
        LOG('WF', TRACE, "getInitialTransitions behavior=%s " % behavior)
        transitions = []
        for tdef in self.transitions.values():
            LOG('WF', TRACE, ' Test transition %s' % tdef.getId())
            if behavior not in tdef.transition_behavior:
                LOG('WF', TRACE, '  Not a %s' % behavior)
                continue
            if not self._checkTransitionGuard(tdef, context):
                LOG('WF', TRACE, '  Guard failed')
                continue
            LOG('WF', TRACE, '  Ok')
            transitions.append(tdef.getId())
        LOG('WF', TRACE, ' Returning transitions=%s' % (transitions,))
        return transitions

    security.declarePrivate('getManagedPermissions')
    def getManagedPermissions(self):
        """Get the permissions managed by this workflow."""
        return self.permissions

    def _objectMaybeFromRpath(self, ob):
        if isinstance(ob, str):
            rpath = ob
            if not rpath or rpath.find('../') >= 0 or rpath.startswith('/'):
                raise WorkflowException("Unauthorized rpath %s" % rpath)
            portal = getToolByName(self, 'portal_url').getPortalObject()
            ob = portal.unrestrictedTraverse(rpath) # XXX unrestricted ?
        return ob

    # debug
    security.declarePrivate('listObjectActions')
    def listObjectActions(self, info):
        '''
        Allows this workflow to
        include actions to be displayed in the actions box.
        Called only when this workflow is applicable to
        info.content.
        Returns the actions to be displayed to the user.
        '''
        LOG('listObjectActions', TRACE, 'Called for wf %s' % self.getId())
        ob = info.content
        sdef = self._getWorkflowStateOf(ob)
        if sdef is None:
            return None
        res = []
        for tid in sdef.transitions:
            LOG('listObjectActions', TRACE, ' Checking %s' % tid)
            tdef = self.transitions.get(tid, None)
            if tdef is not None and tdef.trigger_type == TRIGGER_USER_ACTION:
                if tdef.actbox_name:
                    if self._checkTransitionGuard(tdef, ob):
                        res.append((tid, {
                            'id': tid,
                            'name': tdef.actbox_name % info,
                            'url': tdef.actbox_url % info,
                            'permissions': (),  # Predetermined.
                            'category': tdef.actbox_category}))
                        LOG('listObjectActions', TRACE, '  Guard ok')
                    else:
                        LOG('listObjectActions', TRACE, '  Guard failed')
                else:
                    LOG('listObjectActions', TRACE, '  No user-visible action')
        res.sort()
        return map((lambda (id, val): val), res)

    #
    # ZMI
    #

    # hooked via view in CPSUtil
    manage_options = DCWorkflowDefinition.manage_options + (
        {'label': 'Export', 'action': 'manage_genericSetupExport.html'},
        )


InitializeClass(WorkflowDefinition)

from Products.CMFCore.WorkflowTool import addWorkflowFactory
addWorkflowFactory(WorkflowDefinition, id='cps_workflow',
                   title='Web-configurable workflow for CPS')
