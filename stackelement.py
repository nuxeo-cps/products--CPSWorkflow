# -*- coding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
"""Stack Element

A Stack ELement is an element stored within a stack type.
"""

from copy import deepcopy

from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from ZODB.PersistentMapping import PersistentMapping
from zope.interface import implements

from Products.CMFCore.utils import getToolByName

from Products.CPSWorkflow.stackregistries import \
     WorkflowStackElementRegistry as ElementRegistry
from Products.CPSWorkflow.stackdefinitionguard import \
     StackDefinitionGuard as Guard

from Products.CPSWorkflow.interfaces import IStackElement


class StackElement(SimpleItem):
    """Stack Element
    """
    implements(IStackElement)

    meta_type = 'Stack Element'
    prefix = ''
    hidden_meta_type = ''

    view_guard = None
    edit_guard = None

    _data = None
    # list of editable attributes - when set to None, no check is done.
    _allowed_attributes = None

    def __init__(self, id, **kw):
        self.id = id
        self._data = PersistentMapping()
        self.update(kw.get('data', {}))

    #
    # PRIVATE
    #

    def __cmp__(self, other):
        # compare only on id
        if isinstance(other, StackElement):
            return cmp(self.getId(), other.getId())
        elif isinstance(other, str):
            return cmp(self.getId(), other)
        return 0

    def __call__(self):
        info = {
            'id': self.getId(),
            }
        info.update(self.getData())
        return info

    def __str__(self):
        info_str = "<%s %s >" %(self.__class__.__name__, self(),)
        return info_str

    def __deepcopy__(self, ob):
        """Deep copy. Just to call a clean API while calling getCopy()
        """
        copy = ElementRegistry.makeWorkflowStackElementTypeInstance(
            self.meta_type, self.getId())
        for k, v in self.__dict__.items():
            # dereference persistent mapping
            setattr(copy, k, deepcopy(v))
        return copy

    # dict like access to data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if key == 'id':
            return
        if (self._allowed_attributes is None
            or key in self._allowed_attributes):
            self._data[key] = value


    #
    # API
    #

    def getPrefix(self):
        """Returns the prefix for this stack element
        """
        return self.prefix

    def getIdWithoutPrefix(self):
        """Return the group id without the 'group:' prefix
        """
        prefix = self.getPrefix()
        id = self.getId()
        if prefix:
            # ':' is a separator
            id = id[len(self.getPrefix())+1:]
        return id

    def getHiddenMetaType(self):
        return self.hidden_meta_type

    def getCopy(self):
        """Duplicate self

        Return a new object instance of the same type
        """
        return deepcopy(self)

    def getData(self):
        return dict(self._data)

    def get(self, key, default=None):
        if not self._data.has_key(key):
            return default
        else:
            return self[key]

    def set(self, key, value):
        self[key] = value

    def update(self, data):
        # special key
        if data.has_key('id'):
            del data['id']
        if self._allowed_attributes is not None:
            for key, value in data.items():
                if key not in self._allowed_attributes:
                    del data[key]
        self._data.update(data)

    #
    # SECURITY
    #

    def isVisible(self, sm, stack, context):
        """Is the entry visible by the user

        returns a boolean
        """

        # Standalone elt
        if stack is None or context is None:
            return 1

        wftool = getToolByName(context, 'portal_workflow', None)
        if wftool is None:
            # No workflow tool thus standalone
            return 1

        # XXX CPS assumptions
        wf_def = wftool.getWorkflowsFor(context)[0]

        # First check if there's an override
        if self.getViewGuard():
            return self.getViewGuard().check(sm, wf_def, context)

        # Evaluate the default guard for view of the stackdef within
        # the stack context
        else:
            for k, v in wftool.getStacks(context).items():
                if v == stack:
                    stackdef = wftool.getStackDefinitionFor(context, k)
                    guard = stackdef.getViewStackElementGuard()
                    return guard.check(sm, wf_def, context)
        return 1

    def isEditable(self, sm, stack, context):
        """Is the entry editable by the user

        returns a boolean
        """

        # Standalone elt
        if stack is None or context is None:
            return 1

        wftool = getToolByName(context, 'portal_workflow', None)
        if wftool is None:
            # No workflow tool thus standalone
            return 1

        # XXX CPS assumptions
        wf_def = wftool.getWorkflowsFor(context)[0]

        # First check if there's an override
        if self.getViewGuard():
            return self.getViewGuard().check(sm, wf_def, context)

        # Evaluate the default guard for view of the stackdef within
        # the stack context
        else:
            # XXX
            for k, v in wftool.getStacks(context).items():
                if v == stack:
                    stackdef = wftool.getStackDefinitionFor(context, k)
                    guard = stackdef.getEditStackElementGuard()
                    return guard.check(sm, wf_def, context)
        return 1


    #
    # GUARDS
    #

    def getViewGuard(self):
        return self.view_guard

    def setViewGuard(self, guard_permissions='', guard_roles='',
                     guard_groups='', guard_expr=''):
        self.view_guard = Guard()
        _props = {'guard_permissions':guard_permissions,
                  'guard_roles':guard_roles,
                  'guard_groups':guard_groups,
                  'guard_expr':guard_expr,
                  }
        self.getViewGuard().changeFromProperties(_props)

    def getEditGuard(self):
        return self.edit_guard

    def setEditGuard(self, guard_permissions='', guard_roles='',
                     guard_groups='', guard_expr=''):
        self.edit_guard = Guard()
        _props = {'guard_permissions':guard_permissions,
                  'guard_roles':guard_roles,
                  'guard_groups':guard_groups,
                  'guard_expr':guard_expr,
                  }
        self.getEditGuard().changeFromProperties(_props)


InitializeClass(StackElement)
