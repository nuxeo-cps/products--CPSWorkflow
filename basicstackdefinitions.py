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

"""Basic stack definitions modules

This module contains basic stack definitions.

c.f : doc/stackdefinitions.txt
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager

from stackdefinition import StackDefinition
from stackregistries import WorkflowStackDefRegistry

from zope.interface import implements
from zope.interface.verify import verifyClass, DoesNotImplement
from Products.CPSWorkflow.interfaces import IWorkflowStackDefinition


class SimpleStackDefinition(StackDefinition):
    """Simple Stack Definition
    """

    implements(IWorkflowStackDefinition)

    meta_type = 'Simple Stack Definition'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #
    # PRIVATE API
    # Overrides the not implemented method of Stack
    #

    def _getLocalRolesMapping(self, ds):
        """Give the local roles mapping for the member / group ids within the
        stack

        Simple case : all the member of the stack have the associated local
        role
        """

        mapping = {}

        # Prepare the ds
        ds = self._prepareStack(ds)

        #
        # Build the local role mapping Have to respect the fact that some
        # stacks might have be able to define different local roles for the
        # same element in the stack at a given time
        #

        # XXX AT: access to real StackElement object to update role mappings
        # even if current user is not supposed to view/edit some stack
        # elements.
        # Plus give access to the whole element call result in expression (and
        # not just user/group id, even if it does not make any difference
        # here).
        # Check if this is the wanted behaviour.
        stack_content = ds._getElementsContainer()
        for elt in stack_content:
            elt_id = elt.getIdForRoleSettings()
            for role_id in self.getManagedRoles():
                if self._getExpressionForRole(role_id, ds, level=None,
                                              elt=elt):
                    mapping[elt_id] = mapping.get(elt_id, ()) + (role_id,)

        return mapping

    def _canManageStack(self, ds, aclu, mtool, context, **kw):
        """Check if the current authenticated member scan manage stack

        Simple case in here. If a user is in the stack it can manage it we need
        the acl_users in use and the member_ship tool since I don't want to
        explicit acquicition in here

        We need the context if the case is not yet intialized
        """

        if mtool.isAnonymousUser():
            return 0

        # prepare the ds
        ds = self._prepareStack(ds)

        #
        # Cope with member id.
        # It can be passed within th kw (member_id)
        #

        member_id = kw.get('member_id')
        if member_id is None:
            member = mtool.getAuthenticatedMember()
            member_id = member.getMemberId()
        else:
            member = mtool.getMemberById(member_id)

        #
        # Check first if the member is granted because of irts position within
        # the stack content
        #

        # XXX AT: see if stack content needs to be filtered by rights on elt
        for each in ds.getStackContent(type='role', context=context):
            if not each.startswith('group:'):
                if each == member_id:
                    return 1
            else:
                try:
                    group_no_prefix = each[len('group:'):]
                    group = aclu.getGroupById(group_no_prefix)
                    group_users = group.getUsers()
                    if member_id in group_users:
                        return 1
                except KeyError:
                    # Group has probably been removed
                    pass

        #
        # Now let's cope with the first case when the stack is not yet
        # intialized. Call the specific guard for this
        #

        if ds.getStackContent() == []:
            wf_def = self._getWorkflowDefinition()
            return self.getEmptyStackManageGuard().check(
                getSecurityManager(), wf_def, context)

        return 0

InitializeClass(SimpleStackDefinition)

###################################################
###################################################

class HierarchicalStackDefinition(StackDefinition):
    """Hierarchical Stack Definition
    """

    implements(IWorkflowStackDefinition)

    meta_type = 'Hierarchical Stack Definition'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #
    # PRIVATE API
    # Overrides the not implemented method of Stack
    #

    def _canManageStack(self, ds, aclu, mtool, context, **kw):
        """Check if the current authenticated member scan manage stack

        Here, only the people at the current level are allowed to manage the
        stack. We need the acl_users in use and the member_ship tool since I
        don't want to explicit acquicition in here

        context is needed when the stack has just been initialized.
        """

        if mtool.isAnonymousUser():
            return 0

        # prepare the ds
        ds = self._prepareStack(ds)

        #
        # Cope with member id.
        # It can be passed within the kw (member_id)
        #

        member_id = kw.get('member_id')
        if member_id is None:
            member = mtool.getAuthenticatedMember()
            member_id = member.getMemberId()
        else:
            member = mtool.getMemberById(member_id)

        #
        # Check first if the member is granted because of its position within
        # the stack content.
        # e.g.check that current user, or one of its groups, is at current level

        # XXX AT: see if stack content needs to be filtered by rights on elt
        for each in ds.getLevelContent(type='role', context=context):
            if not each.startswith('group:'):
                if each == member_id:
                    return 1
            else:
                try:
                    # XXX AT: Maybe we could think that, statistically, there
                    # are more users in a given group than groups for a given
                    # user. So maybe could replace this code checking that
                    # given group is in user's computed groups, instead of
                    # iterating on each group's content?
                    group_no_prefix = each[len('group:'):]
                    group = aclu.getGroupById(group_no_prefix)
                    group_users = group.getUsers()
                    if member_id in group_users:
                        return 1
                except KeyError:
                    # Group has probably been removed
                    pass

        #
        # Now let's cope with the first case when the stack is not yet
        # initialized.
        #
        if ds.getStackContent() == {}:
            wf_def = self._getWorkflowDefinition()
            return self.getEmptyStackManageGuard().check(
                getSecurityManager(), wf_def, context)

        return 0

    def _getLocalRolesMapping(self, ds):
        """Give the local roles mapping for the member / group ids within the
        stack

        Simple case : all the member of the stack have the associated local
        role
        """

        mapping = {}

        # Prepare the ds
        ds = self._prepareStack(ds)

        #
        # Build the local role mapping Have to respect the fact that some
        # stacks might have be able to define different local roles for the
        # same element in the stack at a given time
        #

        # XXX AT: access to real StackElement object to update role mappings
        # even if current user is not supposed to view/edit some stack
        # elements.
        # Plus give access to it in expression (and not just user/group id,
        # even if it does not make any difference here).
        stack_content = {}
        for clevel in ds.getAllLevels():
            stack_content[clevel] = ds._getLevelContentValues(clevel)
        for level, elts in stack_content.items():
            for elt in elts:
                elt_id = elt.getIdForRoleSettings()
                for role_id in self.getManagedRoles():
                    if self._getExpressionForRole(role_id, ds, level, elt):
                        mapping[elt_id] = mapping.get(elt_id, ()) + (role_id,)

        return mapping

    #
    # SPECIFIC PRIVATE API
    #

    def _doIncLevel(self, ds):
        """Increase the stack level
        """
        ds = self._prepareStack(ds)
        ds.doIncLevel()
        ds = ds.getCopy()
        return ds

    def _doDecLevel(self, ds):
        """Decrease the stack level
        """
        ds = self._prepareStack(ds)
        ds.doDecLevel()
        ds = ds.getCopy()
        return ds

InitializeClass(HierarchicalStackDefinition)

#####################################################################
#####################################################################

WorkflowStackDefRegistry.register(SimpleStackDefinition)
WorkflowStackDefRegistry.register(HierarchicalStackDefinition)
