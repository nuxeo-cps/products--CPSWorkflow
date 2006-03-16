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

""" Stack Type definition

Base stack type definition. It does :

  + store stack element instances
  + have a render() method linked to a given template within the skins
  + have a _prepareElement() that construct stack element instances
  before the storage
"""

import copy

from ZODB.PersistentMapping import PersistentMapping
from ZODB.PersistentList import PersistentList

from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from zope.interface import implements

from stackregistries import WorkflowStackRegistry as StackRegistry
from stackregistries import WorkflowStackElementRegistry as ElementRegistry

from Products.CPSWorkflow.interfaces import IWorkflowStack

class Stack(SimpleItem):
    """Base Stack Type Definition
    """

    implements(IWorkflowStack)

    meta_type = 'Stack'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    _elements_container = None
    render_method = ''

    #
    # Boring accessors
    #

    def getMetaType(self):
        """Returns the meta_type of the class

        Needs to be public for non restricted code
        """
        return self.meta_type

    #
    # Private API
    #

    def _getElementsContainer(self):
        """Returns the stack elements container

        This is PersistentList type
        """
        return self._elements_container

    def _prepareElement(self, elt_str=None, **kw):
        """Prepare the element.

        Usual format : <prefix : id>
        Call the registry to construct an instance according to the prefix
        Check WorkflowStackElementRegistry
        """
        elt = None
        if isinstance(elt_str, str):
            if ':' in elt_str:
                prefix = elt_str.split(':')[0]
            else:
                # XXX compatibility
                prefix = 'user'
            elt_meta_type = ElementRegistry.getMetaTypeForPrefix(prefix)
            if elt_meta_type is not None:
                elt = ElementRegistry.makeWorkflowStackElementTypeInstance(
                    elt_meta_type, elt_str, **kw)
                return elt
        return elt_str

    def _getManagers(self):
        """Return stack elements representing stack managers.
        """
        raise NotImplementedError


    #
    # API TO BE IMPLEMENTED WITHIN THE CHILD CLASSES
    #

    def push(self, elt=None):
        """Push elt in the queue
        """
        raise NotImplementedError

    def pop(self, elt=None):
        """Remove elt from within the queue

        If elt is None then remove the last one
        """
        raise NotImplementedError

    def reset(self, **kw):
        """Reset the stack
        """
        raise NotImplementedError

    def getStackContent(self, type='id', **kw):
        """Return the actual content of the stack.

        It has to supports at least three types of returned values:

         + id
         + str
         + role
         + call
        """
        raise NotImplementedError

    #
    # MISC
    #

    def render(self, context, mode, **kw):
        """Render in mode

        context is te context. var_id is the wokkflow variable holding this
        stack
        """
        meth = getattr(context, self.render_method, None)
        if meth is None:
            raise RuntimeError(
                "Unknown Render method %s for stack type %s"
                    %(self.render_method, self.meta_type))
        return meth(context=context, mode=mode, stack=self, **kw)

    #
    # COPY
    #

    def getCopy(self):
        """Duplicate self

        Return a new object instance of the same type
        """
        return copy.deepcopy(self)

    def __deepcopy__(self, ob):
        """Deep copy. Just to call a clean API while calling getCopy()

        Cope with mutable attrs to break reference, and deep copy stack
        elements too.
        """

        # Create a new instance of a stack given the meta_type of self
        _copy = StackRegistry.makeWorkflowStackTypeInstance(self.getMetaType())

        for attr, value in self.__dict__.items():
            new_ref = None

            # Check if we need to break the reference for a mutable type
            if isinstance(value, (list, tuple)):
                new_ref = []
            elif isinstance(value, dict):
                new_ref = {}
            elif isinstance(value, PersistentList):
                new_ref = PersistentList()
            elif isinstance(value, PersistentMapping):
                new_ref = PersistentMapping()

            # Now copy the elements if possible.
            if new_ref is not None:
                if isinstance(new_ref, (list, PersistentList)):
                    for each in value:
                        new_ref.append(each.getCopy())
                    _copy.__dict__[attr] = new_ref
                if isinstance(new_ref, (dict, PersistentMapping)):
                    for key in value.keys():
                        new_key_value = [x.getCopy() for x in value[key]]
                        new_ref[key] = new_key_value
                    _copy.__dict__[attr] = new_ref
            else:
                _copy.__dict__[attr] = value
        return _copy

InitializeClass(Stack)
