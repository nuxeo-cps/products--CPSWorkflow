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

""" (Workflow) Stack definitions

Thus, these classes cope with a data structure and the how to store
elements within.

They are public objects right now. The access will be made through the
WorkfloStackDefinitions.
"""

import copy

from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from ZODB.PersistentMapping import PersistentMapping
from ZODB.PersistentList import PersistentList

from interfaces import IWorkflowStack
from interfaces import ISimpleWorkflowStack
from interfaces import IHierarchicalWorkflowStack


DATA_STRUCT_STACK_TYPE_LIFO = 201
DATA_STRUCT_STACK_TYPE_HIERARCHICAL = 202

data_struct_types_export_dict = {
    DATA_STRUCT_STACK_TYPE_LIFO : 'lifo_stack',
    DATA_STRUCT_STACK_TYPE_HIERARCHICAL : 'hierarchical_stack',
    }

################################################################
##############################################################

class BaseStack(SimpleItem):
    """Base Stack

    Stack Implementation. Generic storage. LIFO

    Posssiblity to specify a maximum size for the Stack.

    The container is a simple list type.
    """

    meta_type = 'Base Stack'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __implements__ = IWorkflowStack

    def __init__(self, maxsize=None):
        """ Possiblity to specify a maximum size
        """
        self.max_size = maxsize
        self.container = []

        #
        # We need that for being able to perform diffs on the previous local
        # roles mapping and the current one and thus being able to update the
        # local roles according to that.
        # XXX I'd like to see this moving somewhere else and being accessible
        # from the stackdef.
        #

        self._former_localroles_mapping = {}

    def getMetaType(self):
        """Returns the meta_type of the class
        """
        return self.meta_type

    def getSize(self):
        """ Return the current size of the Stack
        """
        return len(self.container)

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

    def push(self, elt=None):
        """Push an element in the queue

        1  : ok
        0  : queue id full
        -1 : elt is None
        """
        if elt is None:
            return -1
        if self.isFull():
            return 0
        self.container += [elt]
        return 1

    def pop(self):
        """Get the first element of the queue

        0 : empty
        1 : ok
        """
        if self.isEmpty():
            return 0
        last_elt_index = self.getSize() - 1
        res = self.container[last_elt_index]
        del self.container[last_elt_index]
        return res

    #
    # XXX Former local roles are recorded in here for the moment I would like
    # to see this somewhere else and accessible from the stackdef
    #

    def getFormerLocalRolesMapping(self):
        """Return the former local roles mapping

        So that we can make diff and update local roles.
        """
        return getattr(self, '_former_localroles_mapping', {})

    def setFormerLocalRolesMapping(self, mapping):
        """Set the former local roles mapping information

        So that we can make diff and update local roles.
        """
        setattr(self, '_former_localroles_mapping', mapping)

    #################################################################

    def reset(self):
        """Reset the stack

        Call the constructor
        """
        self.__init__()

InitializeClass(BaseStack)

