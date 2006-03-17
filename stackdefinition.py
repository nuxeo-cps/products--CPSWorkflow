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

A stack definition is instantiated within a State object. It holds the basic
configuration for a stack.

A stack definition is defined by :

 - the stack type the stack def will be able to manage
 - the id of the workflow variable where the stack instance will be stored
 - the managed roles. They are roles that the stack def can cope with.  roles
 have an associated tales expression evaluated within the stackdef context that
 defined the policy for the given role.

c.f : doc/stackdefinition.txt

"""

from DateTime import DateTime
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_parent, aq_inner
from OFS.SimpleItem import SimpleItem
from ZODB.PersistentMapping import PersistentMapping

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression, getEngine
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.permissions import ManagePortal

from stackdefinitionguard import StackDefinitionGuard as Guard

from stackregistries import WorkflowStackRegistry

from zope.interface import implements
from Products.CPSWorkflow.interfaces import IWorkflowStackDefinition

class StackDefinition(SimpleItem):
    """Stack Definition base class
    """

    implements(IWorkflowStackDefinition)

    meta_type = 'Stack Definition'

    security = ClassSecurityInfo()

    # List of other stacks whose managers can manage the current stack.
    manager_stack_ids = []
    # List of roles that will be able to manage current stack.
    manager_stack_roles = []

    _empty_stack_manage_guard = None
    _edit_stack_element_guard = None
    _view_stack_element_guard = None

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

        # Managed role expressions
        self._managed_role_exprs = PersistentMapping()
        # Fetch from the kw the argument we are interested in
        for k, v in kw.items():
            if k == 'managed_role_exprs':
                if isinstance(v, dict):
                    for role, expr in v.items():
                        self.addManagedRole(role, expr)
            if k == 'manager_stack_ids':
                setattr(self, k, v)
            if k == 'manager_stack_roles':
                setattr(self, k, v)
            if k == 'empty_stack_manage_guard':
                self.setEmptyStackManageGuard(**v)

    #
    # Guards
    #

    def getEmptyStackManageGuard(self):
        """ Get the empty stack manage guard

        This Guard defines the manage policy on the stack when nobody
        is stored within
        """
        if self._empty_stack_manage_guard is None:
            self._empty_stack_manage_guard  = Guard()
        return self._empty_stack_manage_guard

    def setEmptyStackManageGuard(self, guard_permissions='',
                                 guard_roles='', guard_groups='',
                                 guard_expr='', stackdef_id='', REQUEST=None):
        """ Set the empty stack manage guard

        This Guard defines the manage policy on the stack when nobody
        is stored within
        """
        self._empty_stack_manage_guard = None
        _props = {'guard_permissions':guard_permissions,
                  'guard_roles':guard_roles,
                  'guard_groups':guard_groups,
                  'guard_expr':guard_expr,
                  }
        self.getEmptyStackManageGuard().changeFromProperties(_props)
        if REQUEST is not None:
            url = aq_parent(aq_inner(self)).absolute_url() + \
                  '/manage_stackdefinition?stackdef_id=%s'%stackdef_id
            REQUEST.RESPONSE.redirect(url)

    def getEditStackElementGuard(self):
        """ """
        if self._edit_stack_element_guard is None:
            self._edit_stack_element_guard  = Guard()
        return self._edit_stack_element_guard

    def setEditStackElementGuard(self, guard_permissions=None,
                                 guard_roles=None, guard_groups=None,
                                 guard_expr=None):
        """ """
        _props = {'guard_permissions':guard_permissions,
                  'guard_roles':guard_roles,
                  'guard_groups':guard_groups,
                  'guard_expr':guard_expr,
                  }
        self._edit_stack_element_guard = None
        self.getEditStackElementGuard().changeFromProperties(_props)

    def getViewStackElementGuard(self):
        """ """
        if self._view_stack_element_guard is None:
            self._view_stack_element_guard  = Guard()
        return self._view_stack_element_guard

    def setViewStackElementGuard(self, guard_permissions=None,
                                 guard_roles=None, guard_groups=None,
                                 guard_expr=None):
        """ """
        _props = {'guard_permissions':guard_permissions,
                  'guard_roles':guard_roles,
                  'guard_groups':guard_groups,
                  'guard_expr':guard_expr,
                  }
        self._view_stack_element_guard = None
        self.getViewStackElementGuard().changeFromProperties(_props)

    #
    # Boring accessors
    #

    def _getWorkflowDefinition(self):
        statedef = aq_parent(aq_inner(self))
        states = aq_parent(aq_inner(statedef))
        return aq_parent(aq_inner(states))

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

    security.declarePublic('getManagerStackIds')
    def getManagerStackIds(self):
        """Returns ids of other stacks whose managers can manage this stack.

        This is useful when we want managers of the 'Pilots' stack to be able
        to manage the 'Associates' and 'Watchers' stacks.
        """
        return self.manager_stack_ids

    security.declarePublic('getManagerStackRoles')
    def getManagerStackRoles(self):
        """Returns roles of people who can manage the stack

        This is useful to set a 'Manager' bypass for instance.
        """
        return self.manager_stack_roles


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
    def addManagedRole(self, role_id, expression='python:1'):
        """Add a role to to the list of role this stack definition can cope
        with

        Check _createExpressionNS() for the available namespace variables you
        may use within your TALES expression
        """
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
        - elt : the current element (StackElement call result)
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
    # PRIVATE API
    #

    def _prepareStack(self, ds):
        """Prepare stack on wich we gonna work one

        ds is the data structure holding the delegatees
        """
        if ds is not None:
            if ds.meta_type != self.getStackDataStructureType():
                ds = None
        if ds is None:
            ds = WorkflowStackRegistry.makeWorkflowStackTypeInstance(
                self.getStackDataStructureType())
        return ds

    def _push(self, ds, **kw):
        """Push delegatees

        This method has to be implemented by a child class
        """
        ds = self._prepareStack(ds)
        ds.push(**kw)
        ds = ds.getCopy()
        return ds

    def _pop(self, ds, **kw):
        """Pop delegatees
        """
        ds = self._prepareStack(ds)
        ds.pop(**kw)
        ds = ds.getCopy()
        return ds

    def _edit(self, ds, **kw):
        """Edit delegatees
        """
        ds = self._prepareStack(ds)
        ds.edit(**kw)
        ds = ds.getCopy()
        return ds

    def _reset(self, ds, **kw):
        """Reset stack contained within ds.
        """
        ds = self._prepareStack(ds)
        ds.reset(**kw)
        return ds

    #
    # To be implemented within child class definitions
    #

    def _getLocalRolesMapping(self, ds):
        """Give the local roles mapping for the member / group ids within the
        stack
        """
        raise NotImplementedError

    def _canManageStack(self, ds, aclu, mtool, context, **kw):
        """Check if the current authenticated member can manage stack

        If a user is in the stack managers, it can manage it.

        ds is the stack, aclu is the acl_users, mtool is the membership tool,
        and context is needed if the stack is not yet intialized
        """
        if mtool.isAnonymousUser():
            return 0

        # Prepare the ds
        ds = self._prepareStack(ds)

        # Find the member_id. It can be passed within the kw parameter as
        # 'member_id'.

        member_id = kw.get('member_id')
        if member_id is None:
            member = mtool.getAuthenticatedMember()
            member_id = member.getMemberId()
        else:
            member = mtool.getMemberById(member_id)

        # Check if member is granted because of its role.
        manager_roles = self.getManagerStackRoles()
        if manager_roles:
            user_roles = member.getRolesInContext(context)
            for manager_role in manager_roles:
                if manager_role in user_roles:
                    return 1

        # Check if member is granted because of its position within the stack
        # content
        for elt in ds._getManagers():
            if elt.holdsUser(member_id, aclu):
                return 1

        # If stack is empty, check its empty guard.
        if ds.isEmpty():
            wf_def = self._getWorkflowDefinition()
            return self.getEmptyStackManageGuard().check(
                getSecurityManager(), wf_def, context)

        return 0


InitializeClass(StackDefinition)
