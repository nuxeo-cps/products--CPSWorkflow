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
from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_parent, aq_inner

from ZODB.PersistentList import PersistentList
from ZODB.PersistentMapping import PersistentMapping

from stack import Stack
from stackregistries import WorkflowStackRegistry

from interfaces import IWorkflowStack
from interfaces import ISimpleWorkflowStack
from interfaces import IHierarchicalWorkflowStack

class SimpleStack(Stack):
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

    render_method = 'stack_simple_method'

    def __init__(self, **kw):
        """Default constructor
        """
        Stack.__init__(self, **kw)

    def __deepcopy__(self, ob):
        """Deep copy. Just to call a clean API while calling getCopy()
        """
        copy = SimpleStack()
        for attr, value in self.__dict__.items():
            if attr == '_elements_container':
                # Break reference with mutable structure
                new_container_ref = PersistentList()
                for each in value:
                    new_container_ref.append(each)
                copy.__dict__[attr] = new_container_ref
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
            return Stack.push(self, elt)
        else:
            return -2

    def _getStackElementIndex(self, id):
        i = 0
        for each in self._getElementsContainer():
            if id == each():
                return i
            i += 1
        return -1

    def removeElement(self, element=None):
        """Remove a given element

        O : failed
        1 : sucsess
        """
        if element is not None:
            index = self._getStackElementIndex(element)
            if index >= 0:
                try:
                    del self._getElementsContainer()[index]
                    return 1
                except IndexError:
                    pass
        return 0

    def getStackContent(self, level=None):
        """Return the stack content

        It returns strings but not objects
        """
        res = []
        for each in self._getElementsContainer():
            if each.getGuard().check(getSecurityManager(),
                                     None, aq_parent(aq_inner(self))):
                res.append(each())
            else:
                res.append('not_visible')
        return res

    def getStackContentForRoleSettings(self):
        """Return the stack content for role settings
        """
        res = []
        for each in self._getElementsContainer():
            if each.getGuard().check(getSecurityManager(),
                                     None, aq_parent(aq_inner(self))):
                res.append(each.getIdForRoleSettings())
            else:
                res.append('not_visible')
        return res

    def getCopy(self):
        """Duplicate self

        Return a new object instance of the same type
        """
        return copy.deepcopy(self)

    def replace(self, old, new):
        """Replace old with new within the elements container

        It supports both string and element objects as input
        """
        new_elt = self._prepareElement(new)
        old_elt = self._prepareElement(old)
        try:
            old_elt_index = self.getStackContent().index(old_elt())
            self._elements_container[old_elt_index] = new_elt
        except ValueError:
            pass

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

    render_method = 'stack_hierarchical_method'

    def __init__(self,  **kw):
        """CPSSimpleStack constructor

        Default level is 0
        Direction :
          - -1 up
          - 0 don't move
          - 1 down
        """
        SimpleStack.__init__(self, **kw)
        self._elements_container = PersistentMapping()
        self.level = 0
        self.direction = 1

    def __deepcopy__(self, ob):
        """Deep copy. Just to call a clean API while calling getCopy()
        """
        copy = HierarchicalStack()
        for attr, value in self.__dict__.items():
            if attr == '_elements_container':
                # Break reference with mutable structure
                new_container_ref = PersistentMapping()
                for key in value.keys():
                    new_container_ref[key] = value[key]
                copy.__dict__[attr] = new_container_ref
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

    def getStackContent(self):
        """Return the stack content
        """
        res = {}
        for clevel in self.getAllLevels():
            res[clevel] = self.getLevelContentValues(level=clevel)
        return res

    def getStackContentForRoleSettings(self):
        """Return the stack content for role settings
        """
        res = {}
        for clevel in self.getAllLevels():
            res[clevel] = self.getLevelContentValuesForRoleSettings(level=clevel)
        return res

    def getCurrentLevel(self):
        """Return the current level
        """
        return self.level

    def hasUpperLevel(self):
        """Has the stack a level upper than current level
        """
        return (self.getCurrentLevel() + 1) in self.getAllLevels()

    def hasLowerLevel(self):
        """Has the stack a level lower than the current level
        """
        return (self.getCurrentLevel() - 1) in self.getAllLevels()

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
        if level is None:
            level=self.getCurrentLevel()
        try:
            value = self._getElementsContainer()[level]
        except KeyError:
            value = []

        return value

    def getLevelContentValues(self, level=None):
        content = self.getLevelContent(level)
        res = []
        for each in content:
            res.append(each())

        return res

    def getLevelContentValuesForRoleSettings(self, level=None):
        content = self.getLevelContent(level)
        res = []
        for each in content:
            res.append(each.getIdForRoleSettings())

        return res

    def getAllLevels(self):
        """Return all the existing levels with elts

        It's returned sorted
        """
        returned = []
        levels = self._getElementsContainer().keys()
        for level in levels:
            levelc = self.getLevelContent(level=level)
            if levelc != []:
                returned.append(level)
        returned.sort()
        return returned

    ###################################################

    def push(self, elt=None, level=0, **kw):
        """Push elt at given level or in between two levels

        Coderrors are :

           1  : ok
           0  : queue id full
          -1  : elt is None
          -2  : elt already within the stack
        """

        if elt is None:
            return -1
        if self.isFull():
            return 0

        low_level = kw.get('low_level', None)
        high_level = kw.get('high_level', None)

        # Compatibility
        if (low_level is not None and
            high_level is not None):
            level = None

        # Simply insert a new elt at a given level
        if level is not None:
            content_level = self.getLevelContent(level)
            content_level_values = self.getLevelContentValues(level)
            if elt not in content_level_values:
                elt = self._prepareElement(elt)
                content_level.append(elt)
                self._getElementsContainer()[level] = content_level
            else:
                return -2

        #
        # Check if this is an insertion in between two levels either
        # the high_level and low_level are equal and then this is the
        # same as a regular insertion at a given level, either it's an
        # insertion in between two levels and then we need to inset
        # and change levels. The current level is invariant
        #

        elif (low_level is not None and
              high_level is not None and
              abs(low_level - high_level) <= 1):
            levels = self.getAllLevels()
            if low_level == high_level:
                self.push(elt, level=low_level)
            elif (low_level not in levels and
                  abs(min(levels) - low_level) <= 1):
                self.push(elt, level=low_level)
            elif (high_level not in levels and
                  abs(max(levels) - high_level) <= 1):
                self.push(elt, level=high_level)
            elif (low_level in levels and
                    high_level in levels):
                container = self._getElementsContainer()
                if low_level < self.getCurrentLevel():
                    clevels = [x for x in levels if x <= low_level]
                    for clevel in clevels:
                        container[clevel-1] = container[clevel]
                    container[low_level] = [self._prepareElement(elt)]
                else:
                    clevels = [x for x in levels if x > low_level]
                    clevels.reverse()
                    for clevel in clevels:
                        container[clevel+1] = container[clevel]
                    container[low_level+1] = [self._prepareElement(elt)]
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

        if last is not None:
            last = last()
        return self.removeElement(elt=last, level=level)

    def _getStackElementIndex(self, id, level=None):
        if level is None:
            level = self.getCurrentLevel()
        i = 0
        for each in self.getLevelContent(level=level):
            if id == each():
                return i
            i += 1
        return -1

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
        index = self._getStackElementIndex(elt, level)
        if index >= 0:
            try:
                elt_obj = self.getLevelContent(level=level)[index]
                del self.getLevelContent(level=level)[index]
                return elt_obj
            except KeyError:
                pass
        return -1

    def replace(self, old, new):
        """Replace old with new within the elements container

        It supports both string and element objects as input
        """
        new_elt = self._prepareElement(new)
        old_elt = self._prepareElement(old)
        for level in self.getAllLevels():
            try:
                index_level = self.getLevelContent(
                    level=level).index(old_elt())
                self._elements_container[level][index_level] = new_elt
            except ValueError:
                pass

    def insert(self, elt, low_level=0, high_level=0):
        """Insert an element in between two levels.

        If low_level and high_level are equal then just insert at this
        given level
        """
        if low_level == high_level:
            self.push(elt, level=low_level)
        elif (low_level in self.getAllLevels() and
              high_level in self.getAllLevels()):
            pass

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
