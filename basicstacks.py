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

""" Stack type definitions
"""


from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_parent, aq_inner

from ZODB.PersistentList import PersistentList
from ZODB.PersistentMapping import PersistentMapping

from stack import Stack
from stackregistries import WorkflowStackRegistry
from stackregistries import WorkflowStackElementRegistry as ElementReg

from interfaces import IWorkflowStack
from interfaces import ISimpleWorkflowStack
from interfaces import IHierarchicalWorkflowStack

class SimpleStack(Stack):
    """Simple Stack

    Base Stack extended :
      - Removals wherever in the stack
      - Don't allow having duplicata within the stack

    Notice :  No Hierachy in this structure
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
        self.max_size = kw.get('maxsize')
        self._elements_container = PersistentList()

    #
    # BORING ACCESSRORS
    #

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
    # PRIVATE API
    #

    def _getStackElementIndex(self, id):
        i = 0
        for each in self._getElementsContainer():
            if id == each.getId():
                return i
            i += 1
        return -1

    def _push(self, elt=None, **kw):
        """Push an element in the queue

        1  : ok
        0  : queue id full
        -1 : elt is None
        -2 : already in here
        """
        if self.isFull():
            return 0
        if elt not in self.getStackContent():
            elt = self._prepareElement(elt, **kw)
            if elt is None:
                return -1
            self._getElementsContainer().append(elt)
            return 1
        return -2

    def _pop(self, element=None, **kw):
        """Remove a given element

        O : failed
        1 : sucsess
        """
        if self.isEmpty():
            return 0
        if element is not None:
            index = self._getStackElementIndex(element)
            if index >= 0:
                try:
                    del self._getElementsContainer()[index]
                    return 1
                except IndexError:
                    pass
        else:
            last_elt_index = self.getSize() - 1
            res = self._getElementsContainer()[last_elt_index]
            del self._getElementsContainer()[last_elt_index]
            return res
        return 0

    #
    # API
    #

    def push(self, elt=None, **kw):
        """Public push
        """

        # XXX kws are prefixed by 'push_' because in a transition with
        # push and pop flags, _executeTransition will perform both pop
        # and push actions (and with the same kws ids, pop and push
        # actions could cancel each others)
        push_ids = kw.get('push_ids', ())

        # XXX case where a single element is passed (compatibility)
        if not push_ids:
            return self._push(elt, **kw)

        # Push elements
        # Ids in push_ids have to be prefixed so the registry can find out the
        # element type (exp: groups got a prefixed id 'group:')
        for push_id in push_ids:
            self._push(push_id, **kw)


    def pop(self, elt=None, **kw):
        """Public pop
        """

        # XXX kws are prefixed by 'pop_' because in a transition with push and
        # pop flags, _executeTransition will perform both pop and push actions
        # (and with the same kws ids, pop and push actions could cancel each
        # others).
        pop_ids = kw.get('pop_ids', ())

        # XXX case where a single element is passed (compatibility)
        if not pop_ids:
            return self._pop(elt, **kw)

        # pop_ids have to be prefixed
        for pop_id in pop_ids:
            self._pop(pop_id, **kw)

    def getStackContent(self, type='id', level=None,
                        context=None, **kw):
        """Return the stack content

        context is the context in which will check the
        security on the element.
        """
        res = []
        for each in self._getElementsContainer():
            if (context is not None and
                not each.isVisible(sm=getSecurityManager(), stack=self,
                                   context=context)):
                each = ElementReg.makeWorkflowStackElementTypeInstance(
                    each.getHiddenMetaType(), 'hidden'
                    )
            if type == 'id':
                res.append(each.getId())
            elif type == 'str':
                res.append(str(each))
            elif type == 'call':
                res.append(each())
            elif type == 'role':
                res.append(each.getIdForRoleSettings())
            elif type == 'object':
                res.append(each)
            else:
                emsg = "getStackContent(). Wrong type specified"
                raise ValueError, emsg
        return res

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

    def reset(self, **kw):
        """Reset the stack

        new_stack  : stack that might be a substitute of self
        reset_ids  : new elements to add to the stack
        """
        new_stack = kw.get('new_stack')

        # Translate for push()
        kw['push_ids'] = kw.get('reset_ids', ())

        # Replace the stack container
        if new_stack is not None:
            self._elements_container = new_stack._getElementsContainer()
        else:
            self.__init__()

        # Push the elements if needed
        self.push(**kw)

        return self

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
        self._level = 0

    #
    # PRIVATE API
    #

    def _getStackElementIndex(self, elt, level=None):
        """Find the index of the given element within the stack at a
        given level given the elt itself or its id. It supports both
        since the __cmp__ method of stackelement supports the
        operation.
        """
        if level is None:
            level = self.getCurrentLevel()
        i = 0
        for each in self.getLevelContent(level=level, type='object'):
            if elt == each:
                return i
            i += 1
        return -1

    def _push(self, elt=None, level=0, **kw):
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

        # Prepare the element
        prepared_elt = self._prepareElement(elt, **kw)

        # Simply insert a new elt at a given level
        if level is not None:
            index = self._getStackElementIndex(elt, level)
            if index == -1:
                # element not found in level
                content_level = self.getLevelContent(level, type='object')
                content_level.append(prepared_elt)
                self._getElementsContainer()[level] = content_level
            else:
                # element already here
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
                    container[low_level] = [prepared_elt]
                else:
                    clevels = [x for x in levels if x > low_level]
                    clevels.reverse()
                    for clevel in clevels:
                        container[clevel+1] = container[clevel]
                    container[low_level+1] = [prepared_elt]
        return 1

    def _pop(self, elt=None, level=None, **kw):
        """Remove elt at given level

        -1 : not found
        elt  : ok
        """

        if level is None:
            level = self.getCurrentLevel()
        levelc = self._getLevelContentValues(level=level)

        if elt is None:
            last = None
            if len(levelc) > 0:
                last = levelc[len(levelc)-1]
                if last is not None:
                    elt = last()

        if elt is None:
            return 0

        index = self._getStackElementIndex(elt, level)
        if index >= 0:
            try:
                elt_obj = self.getLevelContent(level=level,
                                               type='object')[index]
                del self._getElementsContainer()[level][index]
                return elt_obj
            except KeyError:
                pass
        return -1

    #
    # API
    #

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

    def getStackContent(self, type='id', context=None, **kw):
        """Return the stack content
        """
        res = {}
        for clevel in self.getAllLevels():
            res[clevel] = self.getLevelContent(level=clevel, type=type,
                                               context=context, **kw)
        return res

    def getCurrentLevel(self):
        """Return the current level
        """
        return self._level

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
            self._level += 1
        return self._level

    def doDecLevel(self):
        """Decrement the level value

        The level has to exist and host elts
        """
        new_level = self.getCurrentLevel() - 1
        if new_level in self.getAllLevels():
            self._level -= 1
        return self._level

    def _getLevelContentValues(self, level=None):
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

    def getLevelContent(self, level=None, type='id', context=None, **kw):
        content = self._getLevelContentValues(level)
        res = []
        for each in content:
            if (context is not None and
                not each.isVisible(sm=getSecurityManager(), stack=self,
                                   context=context)):
                each = ElementReg.makeWorkflowStackElementTypeInstance(
                    each.getHiddenMetaType()
                    )
            if type == 'id':
                res.append(each.getId())
            elif type == 'str':
                res.append(str(each))
            elif type == 'call':
                res.append(each())
            elif type == 'role':
                res.append(each.getIdForRoleSettings())
            elif type == 'object':
                res.append(each)
            else:
                emsg = "getStackContent(). Wrong type specified"
                raise ValueError, emsg
        return res

    def getAllLevels(self):
        """Return all the existing levels with elts

        It's returned sorted
        """
        returned = []
        for k, v in self._getElementsContainer().items():
            if v != []:
                returned.append(k)
        returned.sort()
        return returned

    ###################################################

    def push(self, elt=None, level=None, **kw):
        """Push element
        """

        # XXX kws are prefixed by 'push_' because in a transition with push and
        # pop flags, _executeTransition will perform both pop and push actions
        # (and with the same kws ids, pop and push actions could cancel each
        # others).
        push_ids = kw.get('push_ids', ())
        levels = kw.get('levels', ())

        # XXX case where a single element is passed (compatibility)
        if not (push_ids and levels):
            if level is None:
                level = 0
            return self._push(elt, level, **kw)

        # Push elements
        # Ids in push_ids have to be prefixed so the registry can find out the
        # element type (exp: groups got a prefixed id 'group:')
        i = 0
        for push_id in push_ids:
            try:
                self._push(push_id, int(levels[i]), **kw)
                i += 1
            except IndexError:
                # wrong user input
                pass

    def pop(self, elt=None, level=None, **kw):
        """Pop element
        """

        # XXX kws are prefixed by 'pop_' because in a transition with push and
        # pop flags, _executeTransition will perform both pop and push actions
        # (and with the same kws ids, pop and push actions could cancel each
        # others).
        # Check arguments in here.
        pop_ids = kw.get('pop_ids', ())
        if not pop_ids:
            return self._pop(elt, level, **kw)

        # Pop member / group given ids
        for pop_id in pop_ids:
            # Convention used: 'level,prefix:elt_id'
            # pop_id example: '1,user:toto' or '2,group:titi'
            split = pop_id.split(',')
            level = int(split[0])
            the_id = split[1]
            self._pop(elt=the_id, level=level, **kw)


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

    def reset(self, **kw):
        """Reset the stack

        new_stack  : stack that might be a substitute of self
        reset_ids  : new elements to add at current level
        """
        # Replace the stack container

        new_stack = kw.get('new_stack')
        if new_stack is not None:
            self._elements_container = new_stack._getElementsContainer()
        else:
            self.__init__()

        # Translate for push
        new_elts  = kw['push_ids'] = kw.get('reset_ids', ())

        if kw.get('levels') is None:
            # init with level 0
            kw['levels'] = len(new_elts)*[0]

        # Push elements
        self.push(**kw)

        return self

InitializeClass(HierarchicalStack)

#####################################################################
#####################################################################

WorkflowStackRegistry.register(SimpleStack)
WorkflowStackRegistry.register(HierarchicalStack)
