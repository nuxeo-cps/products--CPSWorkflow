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

"""CPS Workflow Stack Definitions

This module contains all CPS Stack definitions
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.CMFCorePermissions import View, ModifyPortalContent

from interfaces.IWorkflowStackDefinition import IWorkflowStackDefinition

class BaseWorkflowStackDefinition(SimpleItem):
    """BaseWorkflowStackConfiguration

    Holds the basis configuration for a stack
    """

    meta_type = 'Base Workflow Stack Definition'

    __implements__ = IWorkflowStackDefinition

    security = ClassSecurityInfo()

    def __init__(self,
                 stack_ds_type,
                 wf_var_id,
                 **kw
                 ):
        """Constructor

        stack_ds_type   : Data Structure type holding the deleggatees
        wf_var_id       : Workflow variable holding the ds instance
        ass_local_role  : Local role assigned to members of the DS
        """
        self.stack_ds_type = stack_ds_type
        self.wf_var_id = wf_var_id

        for k, v in kw.items():
            setattr(self, k, v)

        #
        # This information has to be on the stackdef since the data structure
        # doesn't need to care about that
        #

        self._isLocked = 0

    security.declareProtected(View, 'getStackDataStructureType')
    def getStackDataStructureType(self):
        """Returns the id of the stack data structure the stack definition is
        hodling
        """
        return self.stack_ds_type

    security.declareProtected(View, 'getStackDataStructureType')
    def getStackWorkflowVariableId(self):
        """Returns the workflow variable id mapping this configuration
        """
        return self.wf_var_id

    security.declareProtected(View, 'getAssociatedLocalRole')
    def getAssociatedLocalRole(self):
        """Returns the workflow variable id mapping this configuration
        """
        return self.ass_local_role

    security.declareProtected(View, 'getGrantedLocalRole')
    def getGrantedLocalRolesForManage(self):
        """Returns the local roles granted to manage the stack.
        It's in use when the
        """
        raise NotImplementedError

    security.declareProtected(View, 'isLocked')
    def isLocked(self):
        """Is the stack locked
        """
        return self._isLocked

    security.declareProtected(ModifyPortalContent, 'doLockStack')
    def doLockStack(self):
        """Lock the stack
        """
        self._isLocked = 1

    security.declareProtected(ModifyPortalContent, 'doUnLockStack')
    def doUnLockStack(self):
        """UnLock stack
        """
        self._isLocked = 0

    security.declareProtected(ModifyPortalContent, 'push')
    def push(self, ds, **kw):
        """Push delegatees

        This method has to be implemented by a child class
        """
        raise NotImplementedError

    security.declareProtected(ModifyPortalContent, 'pop')
    def pop(self, ds, **kw):
        """Pop delegatees

        This method has to be implemented by a child class
        """
        raise NotImplementedError

    security.declareProtected(View, 'listLocalRoles')
    def listLocalRoles(self, ds):
        """Give the local roles mapping for the member / group ids within the
        stack
        """
        raise NotImplementedError

    security.declareProtected(View, 'getFormerLocalRolesMapping')
    def getFormerLocalRolesMapping(self, ds):
        """Give the former local roles mapping for the member / group ids
        within the stack
        """
        raise NotImplementedError

    security.declarePublic('canManageStack')
    def canManageStack(self, ds, aclu, mtool, context, **kw):
        """Can the current member manage the stack ?

        It will depend on the stack data structure.  We need the acl_users in
        use and the member_ship tool since I don't want to explicit acquicition
        in here
        """
        raise NotImplementedError

    security.declarePublic('getManagerStackIds')
    def getManagerStackIds(self):
        """Returns the ids of other stacks for which the people within those
        can manage this stack. For instance in the common use case members
        within the 'Pilots' stack can manage 'Associates' and 'Watchers'
        stacks.
        """
        raise NotImplementedError

    security.declarePrivate('_prepareStack')
    def _prepareStack(self, ds):
        """Prepare stack on wich we gonna work one

        ds is the data structure holding the delegatees
        """
        raise NotImplementedError

    security.declareProtected(ModifyPortalContent, 'resetStack')
    def resetStack(self, ds, **kw):
        """Reset stack contained within ds.
        """
        ds = self._prepareStack(ds)
        ds.reset()
        return ds

InitializeClass(BaseWorkflowStackDefinition)

