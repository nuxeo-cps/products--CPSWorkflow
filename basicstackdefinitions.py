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
from AccessControl import ClassSecurityInfo

from Products.CMFCore.permissions import View, ModifyPortalContent

from basicstacks import SimpleStack, HierarchicalStack
from stackdefinition import StackDefinition
from stackregistries import WorkflowStackDefRegistry

from interfaces import IWorkflowStackDefinition

class SimpleStackDefinition(StackDefinition):
    """Simple Stack Definition
    """

    meta_type = 'Simple Stack Definition'

    security = ClassSecurityInfo()

    __implements__ = (IWorkflowStackDefinition,)

    def _prepareStack(self, ds):
        """Prepare stack on wich we gonna work one

        ds is the data structure holding the delegatees
        """
        LOG("_prepareStack()", DEBUG, 'Simple Stack')
        if ds is not None:
            if ds.meta_type != 'Simple Stack':
                ds = None
        if ds is None:
            ds = SimpleStack()
        return ds

    def _push(self, ds, **kw):
        """Push delegatees

        This method has to be implemented by a child class
        """
        LOG("::SimpleStackDefinition.push()::",
            DEBUG,
            str(kw))

        #
        # Prepare stack.
        # ds comes usually from the status
        # It might be None of not yet initialized
        #

        ds = self._prepareStack(ds)

        #
        # First extract the needed information
        # No level information is needed in here
        #

        member_ids = kw.get('member_ids', ())
        group_ids  = kw.get('group_ids',  ())

        if not (member_ids or group_ids):
            return ds

        #
        # Push members / groups
        # groups gota prefixed id  'group:'
        #

        for member_id in member_ids:
            ds.push(member_id)
        for group_id in group_ids:
            prefixed_group_id = 'group:'+group_id
            ds.push(prefixed_group_id)

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

    def _pop(self, ds, **kw):
        """pop delegatees
        """

        LOG("::SimpleStackDefinition.pop()::",
            DEBUG,
            str(kw))

        #
        # Prepare stack.
        # ds comes usually from the status
        # It might be None of not yet initialized
        #

        ds = self._prepareStack(ds)

        #
        # Pop member / group given ids
        #

        ids = kw.get('ids', ())

        if not ids:
            return ds

        for id in ids:
            ds.removeElement(id)

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

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

        for elt in ds.getStackContent():
            for role_id in self.getManagedRoles():
                if self._getExpressionForRole(role_id, ds):
                    mapping[elt] = mapping.get(elt, ()) + (role_id,)
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

        for each in ds.getStackContent():
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
        # Now let's cope with the first case when the stack is not et
        # intialized. We will grant the 'Owner' of the document and the people
        # having the same local role as the associated local roles of the stack
        #

        # XXX Owner is hardcoded
        # change this for a guard
        _granted_local_roles = ('Owner', self._master_role)

        if ds.getStackContent() == []:
            if context is not None:
                member_roles = member.getRolesInContext(context)
                for lc in _granted_local_roles:
                    if lc in member_roles:
                        return 1

        return 0

InitializeClass(SimpleStackDefinition)

###################################################
###################################################

class HierarchicalStackDefinition(StackDefinition):
    """Hierarchical Stack Definition
    """

    meta_type = 'Hierarchical Stack Definition'

    __implements__ = (IWorkflowStackDefinition,)

    security = ClassSecurityInfo()

    def _prepareStack(self, ds):
        """Prepare stack on wich we gonna work one

        ds is the data structure holding the delegatees
        """
        LOG("_prepareStack()", DEBUG, 'Hierarchical Stack')
        if ds is not None:
            if ds.meta_type != 'Hierarchical Stack':
                ds = None
        if ds is None:
            ds = HierarchicalStack()
        return ds

    def _push(self, ds, **kw):
        """Push delegatees

        This method has to be implemented by a child class
        """
        LOG("::HierarchicalStackDefinition.push()::",
            DEBUG,
            str(kw))

        #
        # First extract the needed information
        # No level information is needed in here
        #

        member_ids = kw.get('member_ids', ())
        group_ids  = kw.get('group_ids',  ())
        levels = kw.get('levels', ())

        if not ((member_ids or group_ids) and levels):
            return ds

        #
        # Prepare stack.
        # ds comes usually from the status
        # It might be None of not yet initialized
        #

        ds = self._prepareStack(ds)

        #
        # Push members / groups
        # groups gota prefixed id  'group:'
        #

        i = 0
        for member_id in member_ids:
            try:
                ds.push(member_id, int(levels[i]))
                i += 1
            except IndexError:
                # wrong user input
                pass
        i = 0
        for group_id in group_ids:
            prefixed_group_id = 'group:'+group_id
            try:
                ds.push(prefixed_group_id, int(levels[i]))
                i += 1
            except IndexError:
                # wrong user input
                pass

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

    def _pop(self, ds, **kw):
        """pop delegatees
        """

        LOG("::SimpleStackDefinition.pop()::",
            DEBUG,
            str(kw))

        #
        # Check arguments in here.
        # Might be wrongly called
        #

        ids = kw.get('ids', ())
        if not ids:
            return ds

        #
        # Prepare stack.
        # ds comes usually from the status
        # It might be None of not yet initialized
        #

        ds = self._prepareStack(ds)

        #
        # Pop member / group given ids
        #

        for id in ids:
            level = int(id.split(',')[0])
            the_id = id.split(',')[1]
            ds.removeElement(the_id, int(level))

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

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

        for each in ds.getLevelContentValues():
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
        # Now let's cope with the first case when the stack is not et
        # intialized. We will grant the 'Owner' of the document and the people
        # having the same local role as the associated local roles of the stack
        #


        _granted_local_roles = ('Owner', self._master_role)

        if ds.getLevelContentValues() == []:
            if context is not None:
                member_roles = member.getRolesInContext(context)
                for lc in _granted_local_roles:
                    if lc in member_roles:
                        return 1

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

        for k, v in ds.getStackContent().items():
            for elt in v:
                for role_id in self.getManagedRoles():
                    if self._getExpressionForRole(role_id, ds, k):
                        mapping[elt] = mapping.get(elt, ()) + (role_id,)
        return mapping

    security.declareProtected(ModifyPortalContent, 'doIncLevel')
    def doIncLevel(self, ds):
        """Increase the stack level
        """

        # Prepare the ds
        ds = self._prepareStack(ds)

        # Increase level
        ds.doIncLevel()

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

    security.declareProtected(ModifyPortalContent, 'doDecLevel')
    def doDecLevel(self, ds):
        """Decrease the stack level
        """

        # Prepare the ds
        ds = self._prepareStack(ds)

        # Decrease level
        ds.doDecLevel()

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

    security.declareProtected(ModifyPortalContent, 'doDecLevel')
    def doReturnedUpDirection(self, ds):
        """Returned up the direction
        """

        # Prepare the ds
        ds = self._prepareStack(ds)

        # Inverse direction
        ds.returnUpDirection()

        #
        # For the workflow history.
        # Let's do a copy of the stack instance
        #

        ds = ds.getCopy()
        return ds

InitializeClass(HierarchicalStackDefinition)

#####################################################################
#####################################################################

WorkflowStackDefRegistry.register(SimpleStackDefinition)
WorkflowStackDefRegistry.register(HierarchicalStackDefinition)
