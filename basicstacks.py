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

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from ZODB.PersistentMapping import PersistentMapping
from ZODB.PersistentList import PersistentList

from stack import BaseStack
from stackregistries import WorkflowStackRegistry

from interfaces import IWorkflowStack
from interfaces import ISimpleWorkflowStack
from interfaces import IHierarchicalWorkflowStack

class SimpleStack(BaseStack):
    """Simple Stack

    Base Stack extended :
      - Removals wherever in the stack
      - Don't allow having duplicata within the stack

    Notice :  No Hierachy in this struture
    The container is a simple list with acessors.
    """

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    meta_type = 'Simple Stack'

    __implements__ = (IWorkflowStack, ISimpleWorkflowStack,)

    def __init__(self, **kw):
        """Default constructor
        """
        BaseStack.__init__(self, **kw)
        self.container = []

    def __deepcopy__(self, ob):
        """Deep copy. Just to call a clean API while calling getCopy()
        """
        copy = SimpleStack()
        for attr, value in self.__dict__.items():
            if attr == 'container':
                # Break reference with mutable structure
                new_container_ref = []
                for each in value:
                    new_container_ref.append(each)
                copy.__dict__[attr] = new_container_ref
            elif attr == '_former_localroles_mapping':
                new_mapping = {}
                for k,v in value.items():
                    new_mapping[k] = v
                copy.__dict__[attr] = new_mapping
            else:
                copy.__dict__[attr] = value
        return copy

    ####################################################################

    def push(self, elt=None):
        """Push an element in the queue

        1  : ok
        0  : queue id full
        -1 : elt is None
        -2 : already in here
        """
        if elt not in self.getStackContent():
            return BaseStack.push(self, elt)
        else:
            return -2

    def removeElement(self, element=None):
        """Remove a given element

        O : failed
        1 : sucsess
        """
        if element is not None:
            try:
                index = self.container.index(element)
                del self.container[index]
                return 1
            except ValueError:
                pass
        return 0

    def getStackContent(self, level=None):
        """Return the stack content
        """
        return self.container

    def getCopy(self):
        """Duplicate self

        Return a new object instance of the same type
        """
        return copy.deepcopy(self)

InitializeClass(SimpleStack)

###########################################################
###########################################################

class HierarchicalStack(SimpleStack):
    """Stack where the level (index) within the stack matters
    """

    meta_type = 'Hierarchical Stack'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    __implements__ = (IWorkflowStack,
                      ISimpleWorkflowStack,
                      IHierarchicalWorkflowStack,)

    def __init__(self,  **kw):
        """CPSSimpleStack constructor

        Default level is 0
        Direction :
          - -1 up
          - 0 don't move
          - 1 down
        """
        SimpleStack.__init__(self, **kw)
        self.container = {}
        self.level = 0
        self.direction = 1

    def __deepcopy__(self, ob):
        """Deep copy. Just to call a clean API while calling getCopy()
        """
        copy = HierarchicalStack()
        for attr, value in self.__dict__.items():
            if attr == 'container':
                # Break reference with mutable structure
                new_container_ref = {}
                for key in value.keys():
                    new_container_ref[key] = value[key]
                copy.__dict__[attr] = new_container_ref
            elif attr == '_former_localroles_mapping':
                new_mapping = {}
                for k,v in value.items():
                    new_mapping[k] = v
                copy.__dict__[attr] = new_mapping
            else:
                copy.__dict__[attr] = value
        return copy

    ##################################################

    def getDirection(self):
        """Get the direction.
        """
        return self.direction

    def setDirectionDown(self):
        """Set the direction below
        """
        self.direction = 1
        return self.direction

    def setDirectionUp(self):
        """Set the directionn above
        """
        self.direction = -1
        return self.direction

    def blockDirection(self):
        """Intermediate situation in between the 1 and 0
        """
        self.direction = 0
        return self.direction

    def returnedUpDirection(self):
        """Returned up direction
        """
        self.direction = -(self.direction)
        return self.direction

    ###################################################

    def getSize(self, level=None):
        """Return the size of a given level
        """
        if level is None:
            level = self.getCurrentLevel()
        return len(self.getLevelContent(level=level))

    def isEmpty(self, level=None):
        """Is level empty ?
        """
        if level is None:
            level = self.getCurrentLevel()
        return len(self.getLevelContent(level=level)) == 0

    def isFull(self, level=None):
        """Is level Full ?

        If maxsize has been specified
        """
        if level is None:
            level = self.getCurrentLevel()
        if self.max_size is not None:
            return len(self.getLevelContent(level=level)) >= self.max_size
        return 0

    ###################################################

    def getCurrentLevel(self):
        """Return the current level
        """
        return self.level

    def doIncLevel(self):
        """Increment the level value

        The level has to exist and host elts
        """
        new_level = self.getCurrentLevel() + 1
        if new_level in self.getAllLevels():
            self.level += 1
        return self.level

    def doDecLevel(self):
        """Decrement the level value

        The level has to exist and host elts
        """
        new_level = self.getCurrentLevel() - 1
        if new_level in self.getAllLevels():
            self.level -= 1
        return self.level

    def getLevelContent(self, level=None):
        """Return  the content of the level given as parameter

        If not specified let's return the current level content
        """
        if level is not None:
            try:
                value = self.container[level]
            except KeyError:
                value = []
        else:
            value = self.getLevelContent(level=self.getCurrentLevel())
        return value

    def getAllLevels(self):
        """Return all the existing levels with elts

        It's returned sorted
        """
        returned = []
        levels = self.container.keys()
        for level in levels:
            levelc = self.getLevelContent(level=level)
            if levelc != []:
                returned.append(level)
        returned.sort()
        return returned

    ###################################################

    def push(self, elt=None, level=0):
        """Push elt at given level
         1  : ok
        0  : queue id full
        -1 : elt is None
        """
        if elt is None:
            return -1
        if self.isFull():
            return 0

        content_level = self.getLevelContent(level)
        if elt not in content_level:
            content_level.append(elt)
        else:
            return -2

        self.container[level] = content_level

        return 1

    def pop(self, level=None):
        """Pop last element of current level

        If level is None we work at current level
        """

        if level is None:
            level = self.getCurrentLevel()

        levelc = self.getLevelContent(level=level)
        last = None
        if len(levelc) > 0:
            last = levelc[len(levelc)-1]
        return self.removeElement(elt=last, level=level)

    def removeElement(self, elt=None, level=None):
        """Remove elt at given level

        -1 : not found
        elt  : ok
        0 : not found
        """
        if elt is None:
            return 0
        if level is None:
            level = self.getCurrentLevel()
        try:
            index = self.getLevelContent(level=level).index(elt)
            del self.getLevelContent(level=level)[index]
            return elt
        except ValueError:
            pass
        return -1

    ################################################################

    def getCopy(self):
        """Duplicate self

        Return a new object instance of the same type
        """
        return copy.deepcopy(self)

InitializeClass(HierarchicalStack)

#####################################################################
#####################################################################

WorkflowStackRegistry.register(SimpleStack)
WorkflowStackRegistry.register(HierarchicalStack)

