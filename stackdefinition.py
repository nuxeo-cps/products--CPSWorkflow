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

"""Stack Definition

StackDefinition is the base class for the StackDefinition type.

To be able to register your own class within the WorkflowStackDefRegistry you
need to sub-class this bare definition and implement the
IWorkflowStackDefinition interface. (Check basicstackdefinitions.py)

A stack definition is instancied wthin a State object. It holds the basic
configuration for a stack.

A stack definition is defined by :

 - the stack type the stack def will be able to manage
 - the id of the workflow variable where the stack instance will be stored
 - the managed roles. They are roles that the stack def can cope with.  roles
 have an associated tales expression evaluated within the stackdef context that
 defined the policy for the given role.

c.f : doc/stackdefinition.txt

"""

from types import StringType

from DateTime import DateTime
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from ZODB.PersistentMapping import PersistentMapping

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression, getEngine
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.permissions import ManagePortal

from interfaces import IWorkflowStackDefinition

class StackDefinition(SimpleItem):
    """Stack Definition base class
    """

    meta_type = 'Stack Definition'

    __implements__ = (IWorkflowStackDefinition, )

    security = ClassSecurityInfo()

    _isLocked = 0
    manager_stack_ids = []

    def __init__(self,
                 stack_type,
                 wf_var_id,
                 **kw):
        """Constructor

        stack_type   : Data Structure type holding the deleggatees
        wf_var_id       : Workflow variable holding the ds instance
        """
        self.stack_type = stack_type
        self.wf_var_id = wf_var_id

        # Fetch from the kw the argument we are interested in
        for k, v in kw.items():
            if k == 'manager_stack_ids':
                setattr(self, k, v)

        # Managed Roles
        self._managed_role_exprs = PersistentMapping()

        # XXX change this for a guard
        self._master_role = 'Manager'

    #
    # Boring accessors
    #

    security.declareProtected(View, 'getStackDataStructureType')
    def getStackDataStructureType(self):
        """Returns the id of the stack data structure the stack definition is
        hodling
        """
        return self.stack_type

    security.declareProtected(View, 'getStackDataStructureType')
    def getStackWorkflowVariableId(self):
        """Returns the workflow variable id mapping this configuration
        """
        return self.wf_var_id

    security.declareProtected(View, 'getMasterRole')
    def getMasterRole(self):
        """Returns the master role for this stack definition.

        The master role is the role
        """
        return self._master_role

    security.declareProtected(ManagePortal, 'setMasterRole')
    def setMasterRole(self, role_id):
        """Set the master role for this stack definition.
        """
        if isinstance(role_id, StringType):
            self._master_role = role_id

    #
    # API : Lock / Unlock
    #

    security.declareProtected(View, 'isLocked')
    def isLocked(self):
        """Is the stack locked
        """
        return self._isLocked

    security.declareProtected(ManagePortal, 'doLockStack')
    def doLockStack(self):
        """Lock the stack
        """
        self._isLocked = 1

    security.declareProtected(ManagePortal, 'doUnLockStack')
    def doUnLockStack(self):
        """UnLock stack
        """
        self._isLocked = 0

    #
    # API : Reinitialization
    #

    security.declareProtected(ManagePortal, 'resetStack')
    def resetStack(self, ds, **kw):
        """Reset stack contained within ds.
        """
        ds = self._prepareStack(ds)
        ds.reset()
        return ds

    #
    # API : Managed roles
    #

    security.declareProtected(ModifyPortalContent, 'getManagedRoles')
    def getManagedRoles(self):
        """Returns all the roles tha stack will cope with.

        A managed role is a role that might be assigned to an element of the
        stack in a given context (context here means the location of the
        elements within the stack and meta information about the stack itself)

        It's under the stack definition policy
        """
        return self._managed_role_exprs.keys()

    security.declareProtected(ManagePortal, 'addManagedRole')
    def addManagedRole(self, role_id, expression='python:1', master_role=0):
        """Add a role to to the list of role this stack definition can cope
        with

        master_role is the role that will be considered as a manager role if
        the stack dosen't contain any elts

        Check _createExpressionNS() for the available namespace variables you
        may use within your TALES expression
        """
        if master_role:
            self.setMasterRole(role_id)
        self._managed_role_exprs[role_id] = expression

    security.declareProtected(ManagePortal, 'delManagedRole')
    def delManagedRole(self, role_id):
        """Delete a role from the list of managed roles
        """
        if role_id in self.getManagedRoles():
            del self._managed_role_exprs[role_id]

    def _addExpressionForRole(self, role_id, expression):
        """Add a TALES expression for a given role

        The expression should return a boolean value and reply to the question
        : 'Is the elt at level X stored within stack granted with this role ?'
        """
        if role_id in self.getManagedRoles():
            self._managed_role_exprs[role_id] = expression

    def _createExpressionNS(self, role_id, stack, level, elt):
        """Create an expression context for expression evaluation

        - stack : the current stack
        - stackdef : the stack definition where the stack is defined
        - elt : the current element (UserElement child)
        - level : the level given as an argument where the elt is
        - role : the role we want to check
        - portal : the portal itself

        Check the documentation within the doc sub-folder of this component
        """
        # Standalone case
        portal = None
        utool = getToolByName(self, 'portal_url', None)
        if utool is not None:
            portal = utool.getPortalObject()
        mapping = {'stack': stack,
                   'role' : role_id,
                   'stackdef' : self,
                   'level'  : level,
                   'elt'    : elt,
                   'portal' : portal,
                   'DateTime': DateTime,
                   'nothing': None,
                   }
        return getEngine().getContext(mapping)

    def _getExpressionForRole(self, role_id, stack, level=0, elt=None):
        """Compute the expression according to the parameters for a given role.

        Typically, the use case is : 'Is the elt at level X stored within
        stack granted with this role  ?'

        This is an internal function used while constructing role mappings
        within listLocalRoles() (Check basicstackdefinitions.py)
        """
        _expression_c = Expression(self._managed_role_exprs.get(role_id,
                                                                'python:1'))
        expr_context = self._createExpressionNS(role_id, stack, level, elt)
        return _expression_c(expr_context)

    #
    # To be implemented within child class definitions
    #

    security.declarePrivate('_prepareStack')
    def _prepareStack(self, ds):
        """Prepare stack on wich we gonna work one

        ds is the data structure holding the delegatees
        """
        raise NotImplementedError

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

InitializeClass(StackDefinition)
