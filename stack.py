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
  + implement a default LIFO
  + have a render() method linked to a given template within the skins
"""

from types import StringType

from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from ZODB.PersistentList import PersistentList

from stackregistries import WorkflowStackElementRegistry as ElementRegistry

from interfaces import IWorkflowStack

class Stack(SimpleItem):
    """Base Stack Type Definition
    """

    meta_type = 'Stack'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __implements__ = IWorkflowStack

    render_method = ''

    def __init__(self, maxsize=None):
        """ Possiblity to specify a maximum size
        """
        self.max_size = maxsize
        self._elements_container = PersistentList()

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
        if isinstance(elt_str, StringType):
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

    #
    # Accessors
    #

    def getMetaType(self):
        """Returns the meta_type of the class

        Needs to be public for non restricted code
        """
        return self.meta_type
    
    def getSize(self):
        """ Return the current size of the Stack
        """
        return len(self._getElementsContainer())

    def isFull(self):
        """Is the queue Full ?

        Used in the case of max size is specified
        """
        if self.max_size is not None:
            return self.getSize() >= self.max_size
        return 0

    def isEmpty(self):
        """Is the Stack empty ?
        """
        return self.getSize() == 0

    #
    # API
    #

    def push(self, elt=None):
        """Push an element in the queue

        1  : ok
        0  : queue id full
        -1 : elt is None
        """

        # Construct a stack element instance
        elt = self._prepareElement(elt)

        if elt is None:
            return -1
        if self.isFull():
            return 0

        # ok we push
        self._getElementsContainer().append(elt)
        return 1

    def pop(self):
        """Get the first element of the queue

        0 : empty
        1 : ok
        """

        if self.isEmpty():
            return 0

        last_elt_index = self.getSize() - 1
        res = self._getElementsContainer()[last_elt_index]
        del self._getElementsContainer()[last_elt_index]
        return res

    # XXX give **kw to push
    def reset(self, **kw):
        """Reset the stack

        new_stack  : stack that might be a substitute of self
        new_users  : users to add at current level
        new_groups : groups to add ar current level
        """
        new_stack = kw.get('new_stack')
        new_users = kw.get('new_users', ())
        new_groups = kw.get('new_groups', ())

        if new_stack is not None:
            self._elements_container = new_stack._getElementsContainer()
        else:
            self.__init__()

        for new_user in new_users:
            self.push(new_user)
        for new_group in new_groups:
            self.push(new_group)

        return self
        
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
        return meth(mode=mode, stack=self)

InitializeClass(Stack)
