# (C) Copyright 2004-2006 Nuxeo SAZ <http://nuxeo.com>
# Authors:
# - Julien Anguenot <ja@nuxeo.com>
# - Anahide Tchertchian <at@nuxeo.com>
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

from warnings import warn
from logging import getLogger

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager

from ZODB.PersistentList import PersistentList
from ZODB.PersistentMapping import PersistentMapping

from stack import Stack
from stackregistries import WorkflowStackRegistry
from stackregistries import WorkflowStackElementRegistry as ElementReg

from zope.interface import implements
from Products.CPSWorkflow.interfaces import IWorkflowStack
from Products.CPSWorkflow.interfaces import ISimpleWorkflowStack
from Products.CPSWorkflow.interfaces import IHierarchicalWorkflowStack

class SimpleStack(Stack):
    """Simple Stack

    Base Stack extended :
      - Removals wherever in the stack
      - Don't allow having duplicata within the stack

    Notice :  No Hierachy in this structure
    The container is a simple list with acessors.

    The stack is created by the stack definition given its configuration.

    Usage:
    >>> from Products.CPSWorkflow.basicstacks import SimpleStack

    """

    implements(IWorkflowStack, ISimpleWorkflowStack)

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    meta_type = 'Simple Stack'

    render_method = 'stack_simple_method'

    logger = getLogger('SimpleStack')

    def __init__(self, **kw):
        """Default constructor
        """
        self.max_size = kw.get('max_size')
        self._elements_container = PersistentList()
        render_method = kw.get('render_method')
        if render_method:
            self.render_method = render_method

    #
    # ACCESSORS
    #

    def getSize(self):
        """Return the current size of the Stack

        >>> stack = SimpleStack()
        >>> stack.getSize()
        0
        >>> stack.push(push_ids=['user:test'])
        1
        >>> stack.getSize()
        1

        """
        return len(self._getElementsContainer())

    def isEmpty(self):
        """Is the Stack empty ?

        >>> stack = SimpleStack()
        >>> stack.isEmpty()
        1
        >>> stack.push(push_ids=['user:test'])
        1
        >>> stack.isEmpty()
        0

        """
        return self.getSize() == 0

    def isFull(self):
        """Is the queue Full ?

        Used in the case of max size is specified

        >>> stack = SimpleStack(max_size=2)
        >>> stack.isFull()
        0
        >>> stack.push(push_ids=['user:test1', 'user:test2'])
        1
        >>> stack.getSize()
        2
        >>> stack.isFull()
        1

        """
        if self.max_size is not None:
            return self.getSize() >= self.max_size
        return 0


    #
    # PRIVATE API
    #

    def _push(self, elt=None, data={}, **kw):
        """Push an element in the queue

        data and additional keywords are passed to the stack element
        constructor.

        Return a code error:
        0 : failure (element is None or already here, or stack is full)
        1 : success

        >>> stack = SimpleStack(max_size=2)
        >>> stack._push('user:test')
        1
        >>> stack._push('user:test')
        0
        >>> stack._push(None)
        0
        >>> stack._push('user:test2')
        1
        >>> stack._push('user:test3') # stack is full
        0

        """
        if self.isFull():
            return 0
        if elt not in self._getElementsContainer():
            elt = self._prepareElement(elt, data=data, **kw)
            if elt is None:
                return 0
            self._getElementsContainer().append(elt)
            return 1
        return 0

    def _pop(self, elt=None, **kw):
        """Remove a given element

        Additional keywords are not used right now.

        Return a code error:
        O : failure (element not found)
        1 : success

        >>> stack = SimpleStack()
        >>> stack._push('user:test')
        1
        >>> stack._pop('user:test')
        1
        >>> stack._pop('user:fake')
        0

        """
        if self.isEmpty():
            return 0
        if elt is not None:
            index = self._getStackElementIndex(elt)
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


    def _edit(self, elt=None, data={}, **kw):
        """Edit a given element

        data is used for element update.

        Return a code error:
        O : failure (element not found)
        1 : success

        >>> stack = SimpleStack()
        >>> stack._push('user:test', data={'comment': 'This is a test'})
        1
        >>> [x() for x in stack._getStackContent()]
        [{'comment': 'This is a test', 'id': 'user:test'}]
        >>> stack._edit('user:test', data={'comment': 'This is another test'})
        1
        >>> [x() for x in stack._getStackContent()]
        [{'comment': 'This is another test', 'id': 'user:test'}]

        """
        index = self._getStackElementIndex(elt)
        if index == -1:
            res = 0
        else:
            elt = self._getElementsContainer()[index]
            elt.update(data)
            res = 1
        return res

    def _getStackContent(self):
        """Return stack content, no check on permissions
        """
        return list(self._getElementsContainer())


    def _getStackElementIndex(self, id):
        """Get stack element index in stack

        >>> stack = SimpleStack()
        >>> stack._push('user:test1')
        1
        >>> stack._getStackElementIndex('user:test1')
        0
        >>> stack._push('user:test2')
        1
        >>> stack._getStackElementIndex('user:test2')
        1

        """
        i = 0
        for each in self._getElementsContainer():
            if id == each:
                return i
            i += 1
        return -1


    def _getManagers(self):
        """Get stack elements representing stack managers.

        All elements are managers.

        >>> stack = SimpleStack()
        >>> stack._push('user:test')
        1
        >>> [x.getId() for x in stack._getManagers()]
        ['user:test']

        """
        return self._getStackContent()

    #
    # API
    #

    def push(self, push_ids=(), **kw):
        """Public push

        Return a code error:
        0 : failure on one of the pushes
        1 : success on all pushes

        Additional keywords will be used to pass additional data for each
        element to push.

        push_ids and kw come from the wftool.doActionFor method keywords.

        >>> stack = SimpleStack()
        >>> push_ids = ['user:test1', 'user:test2']
        >>> comment = ['comment for test1', 'comment for test2']
        >>> stack.push(push_ids, data_list=['comment'], comment=comment)
        1
        >>> [x() for x in stack._getStackContent()]
        [{'comment': 'comment for test1', 'id': 'user:test1'}, {'comment':
        'comment for test2', 'id': 'user:test2'}]

        """
        code = 1

        # find out data keys and corresponding data lists
        data_list = kw.get('data_list', ())
        data_info = dict((key, kw.get(key, [])) for key in data_list)

        for index, push_id in enumerate(push_ids):
            data = {}
            for key, values in data_info.items():
                try:
                    data[key] = values[index]
                except IndexError:
                    pass
            code = code and self._push(push_id, data=data)

        return code


    def pop(self, pop_ids=(), **kw):
        """Public pop

        Return a code error:
        0 : failure on one of the pops
        1 : success on all pops

        pop_ids and kw come from the wftool.doActionFor method keywords.

        >>> stack = SimpleStack()
        >>> push_ids = ['user:test1', 'user:test2']
        >>> stack.push(push_ids)
        1
        >>> [x.getId() for x in stack._getStackContent()]
        ['user:test1', 'user:test2']
        >>> pop_ids = ['user:test1']
        >>> stack.pop(pop_ids)
        1
        >>> [x.getId() for x in stack._getStackContent()]
        ['user:test2']

        """
        code = 1

        for pop_id in pop_ids:
            code = code and self._pop(pop_id, **kw)

        return code

    def edit(self, edit_ids=(), **kw):
        """Public edit

        Return a code error:
        0 : failure on one of the edits
        1 : success on all edits

        Additional keywords will be used to pass additional data for each
        element to edit.

        edit_ids and kw come from the wftool.doActionFor method keywords.

        >>> stack = SimpleStack()
        >>> push_ids = ['user:test1', 'user:test2']
        >>> comment = ['comment for test1', 'comment for test2']
        >>> stack.push(push_ids, data_list=['comment'], comment=comment)
        1
        >>> [x() for x in stack._getStackContent()]
        [{'comment': 'comment for test1', 'id': 'user:test1'}, {'comment':
        'comment for test2', 'id': 'user:test2'}]
        >>> edit_ids = ['user:test1', 'user:test2']
        >>> comment = ['new comment for test1', 'new comment for test2 too']
        >>> stack.edit(edit_ids, data_list=['comment'], comment=comment)
        1
        >>> [x() for x in stack._getStackContent()]
        [{'comment': 'new comment for test1', 'id': 'user:test1'}, {'comment':
        'new comment for test2 too', 'id': 'user:test2'}]

        """
        code = 1

        # find out data keys and corresponding data lists
        data_list = kw.get('data_list', ())
        data_info = dict((key, kw.get(key, [])) for key in data_list)

        for index, edit_id in enumerate(edit_ids):
            data = {}
            for key, values in data_info.items():
                try:
                    data[key] = values[index]
                except IndexError:
                    pass
            code = code and self._edit(edit_id, data=data)

        return code


    def reset(self, **kw):
        """Reset the stack and return it.

        kw comes from the wftool.doActionFor method keywords:
        new_stack  : stack that might be a substitute of self
        reset_ids  : new elements to add to the stack

        Additional keywords will be used by the push method.
        """
        # Replace the stack container
        new_stack = kw.get('new_stack')
        if new_stack is not None:
            self._elements_container = new_stack._getElementsContainer()
        else:
            self.__init__()

        # Translate for push()
        kw['push_ids'] = kw.get('reset_ids', ())
        self.push(**kw)

        return self


    def getStackContent(self, type='id', context=None, **kw):
        """Return the stack content

        type can either be: id, str, call, role or object.
        context is the context in which will check the security on the element.
        """
        res = []
        for each in self._getStackContent():
            if (context is None or
                not each.isVisible(sm=getSecurityManager(), stack=self,
                                   context=context)):
                each = ElementReg.makeWorkflowStackElementTypeInstance(
                    each.getHiddenMetaType(), 'hidden')
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


InitializeClass(SimpleStack)

###########################################################
###########################################################

class HierarchicalStack(Stack):
    """Stack where the level (index) within the stack matters
    """

    implements(IWorkflowStack, ISimpleWorkflowStack,
               IHierarchicalWorkflowStack)

    meta_type = 'Hierarchical Stack'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    render_method = 'stack_hierarchical_method'

    logger = getLogger('HierarchicalStack')

    def __init__(self,  **kw):
        """Constructor, default current level is 0

        Usage:
        >>> from Products.CPSWorkflow.basicstacks import HierarchicalStack

        """
        self.max_size = kw.get('max_size')
        self._elements_container = PersistentMapping()
        self._level = 0
        render_method = kw.get('render_method')
        if render_method:
            self.render_method = render_method


    #
    # ACCESSORS
    #

    def getSize(self, level=None):
        """Return the size of a given level

        If level is None, return size of all the stack

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._push('group:test2', level=1)
        1
        >>> stack.getSize(level=1)
        1
        >>> stack.getSize()
        2

        """
        if level is None:
            size = 0
            for k, v in self._getElementsContainer().items():
                size += len(v)
        else:
            size = len(self._getElementsContainer().get(level, ()))
        return size

    def isEmpty(self, level=None):
        """Return True if given level is empty

        If level is None, return True if stack is empty

        >>> stack = HierarchicalStack()
        >>> stack.isEmpty()
        True
        >>> stack._push('user:test1', level=0)
        1
        >>> stack.isEmpty()
        False

        """
        return self.getSize(level=level) == 0

    def isFull(self, level=None):
        """Return True if given level is full

        max_size keyword has to be passed to constructor
        if level is None, use current level.

        >>> stack = HierarchicalStack(max_size=1)
        >>> stack.isFull()
        False
        >>> stack._push('user:test1', level=0)
        1
        >>> stack.isFull()
        True
        >>> stack.isFull(level=1)
        False
        >>> stack._push('user:test2', level=1)
        1
        >>> stack.isFull(level=1)
        True

        """
        if level is None:
            level = self.getCurrentLevel()
        if self.max_size is not None:
            return len(self.getLevelContent(level=level)) >= self.max_size
        return 0

    def getCurrentLevel(self):
        """Return the current level

        >>> stack = HierarchicalStack()
        >>> stack.getCurrentLevel()
        0

        """
        return self._level

    def hasUpperLevel(self):
        """Has the stack a level upper than current level

        >>> stack = HierarchicalStack(max_size=1)
        >>> stack._push('user:test1', level=0)
        1
        >>> stack.hasUpperLevel()
        False
        >>> stack._push('user:test2', level=1)
        1
        >>> stack.hasUpperLevel()
        True

        """
        return (self.getCurrentLevel() + 1) in self.getAllLevels()

    def hasLowerLevel(self):
        """Has the stack a level lower than the current level

        >>> stack = HierarchicalStack(max_size=1)
        >>> stack._push('user:test1', level=0)
        1
        >>> stack.hasLowerLevel()
        False
        >>> stack._push('user:test2', level=-1)
        1
        >>> stack.hasLowerLevel()
        True

        """
        return (self.getCurrentLevel() - 1) in self.getAllLevels()

    def getAllLevels(self):
        """Return all non-empty levels

        It's returned sorted

        >>> stack = HierarchicalStack(max_size=1)
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._push('user:test2', level=1)
        1
        >>> stack.getAllLevels()
        [0, 1]

        """
        returned = []
        for k, v in self._getElementsContainer().items():
            if v:
                returned.append(k)
        returned.sort()
        return returned


    def getInsertLevels(self, between=True):
        """Return all levels where elements can be pushed or inserted

        If between is True, also return levels between two existing levels.
        The list is returned sorted.

        >>> stack = HierarchicalStack(max_size=1)
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._push('user:test2', level=1)
        1
        >>> stack.getInsertLevels()
        [-1, 0, '0_1', 1, 2]
        >>> stack.getInsertLevels(between=False)
        [-1, 0, 1, 2]

        """
        res = []
        all_levels = self.getAllLevels() # already sorted

        if len(all_levels) == 0:
            res.append(0)
        else:
            start = all_levels[0] - 1
            res.append(start)

            # find all consecutive integers in this list
            # init with two first elements
            index = 0
            current = all_levels[index]
            while index < len(all_levels) - 1:
                res.append(current)
                index += 1
                next = all_levels[index]
                if (current + 1 == next):
                    if between:
                        # add intermediate level
                        res.append(str(current) + '_' + str(next))
                else:
                    # there is a hole between two existing levels, add only one
                    # empty level
                    missing_level = current + 1
                    res.append(missing_level)
                current = next
            res.append(current)

            end = all_levels[-1] + 1
            res.append(end)

        return res


    #
    # PRIVATE API
    #

    def _push(self, elt=None, level=None,
              low_level=None, high_level=None, **kw):
        """Push elt at given level or in between two levels

        If level is None, push at current level.
        If low_level ang high_level are set, push in between.
        Additional keywords are passed to the stack element constructor.

        Return a code error:
        0 : failure (element is None or already here, or stack is full)
        1 : success

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test1')
        1
        >>> stack._push('user:test1', level=0)
        0
        >>> stack._push(None)
        0
        >>> stack._push('user:test2', level=1)
        1
        >>> stack._getStackContent()
        {0: [<UserStackElement at user:test1>], 1: [<UserStackElement at user:test2>]}
        >>> stack._push('user:test3', low_level=0, high_level=1)
        1
        >>> stack._getStackContent()
        {0: [<UserStackElement at user:test1>], 1: [<UserStackElement at
        user:test3>], 2: [<UserStackElement at user:test2>]}

        """
        if elt is None:
            return 0

        # Compatibility
        if (low_level is not None and
            high_level is not None):
            level = None
        elif level is None:
            level = self.getCurrentLevel()

        # Prepare the element
        prepared_elt = self._prepareElement(elt, **kw)

        # Simply insert a new elt at a given level
        if level is not None:
            if self.isFull(level=level):
                return 0
            index = self._getStackElementIndex(elt, level)
            if index == -1:
                # element not found in level
                content_level = self._getLevelContent(level)
                content_level.append(prepared_elt)
                self._getElementsContainer()[level] = content_level
            else:
                # element already here
                return 0

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
            if self.isFull(level=low_level):
                return 0
            levels = self.getAllLevels()
            if low_level == high_level:
                self._push(elt, level=low_level)
            elif (low_level not in levels and
                  abs(min(levels) - low_level) <= 1):
                self._push(elt, level=low_level)
            elif (high_level not in levels and
                  abs(max(levels) - high_level) <= 1):
                self._push(elt, level=high_level)
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

        If level is None, pop at current level.
        Additional keywords are not used right now.

        Return a code error:
        O : failure (element not found)
        1 : success

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._pop('user:test1')
        1
        >>> stack._pop('user:fake')
        0

        """
        if elt is None:
            return 0
        if level is None:
            level = self.getCurrentLevel()

        index = self._getStackElementIndex(elt, level)
        if index >= 0:
            try:
                del self._getElementsContainer()[level][index]
                return 1
            except KeyError:
                pass
        return 0

    def _edit(self, elt=None, level=None, data={}, **kw):
        """Edit a given element

        data is used for element update.
        If level is None, pop at current level.
        Additional keywords are not used right now.

        Return a code error:
        O : failure (element not found)
        1 : success

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test', level=0, data={'comment': 'This is a test'})
        1
        >>> for level, content in stack._getStackContent().items():
        ...     print level, [x() for x in content]
        0 [{'comment': 'This is a test', 'id': 'user:test'}]
        >>> stack._edit('user:test', level=0, data={'comment': 'This is another test'})
        1
        >>> for level, content in stack._getStackContent().items():
        ...     print level, [x() for x in content]
        0 [{'comment': 'This is another test', 'id': 'user:test'}]

        """
        if elt is None:
            return 0
        if level is None:
            level = self.getCurrentLevel()

        index = self._getStackElementIndex(elt, level)
        if index >= 0:
            try:
                elt = self._getElementsContainer()[level][index]
                elt.update(data)
                return 1
            except KeyError:
                pass
        return 0


    def _getManagers(self):
        """Get stack elements representing stack managers.

        All elements at current level are managers.

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._push('user:test2', level=1)
        1
        >>> [x.getId() for x in stack._getManagers()]
        ['user:test1']

        """
        current_level = self.getCurrentLevel()
        return self._getLevelContent(current_level)


    def _getLevelContent(self, level=None):
        """Return content of given level

        If level is None, use current level

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._getLevelContent()
        [<UserStackElement at user:test1>]

        """
        if level is None:
            level = self.getCurrentLevel()
        try:
            value = self._getElementsContainer()[level]
        except KeyError:
            value = []

        return value

    # BBB
    def _getLevelContentValues(self, level=None):
        """Return content of given level, deprecated
        """
        warn("_getLevelContentValues is deprecated, use _getLevelContent instead")
        return self._getLevelContent(level=level)

    def _getStackContent(self, type='id', context=None, **kw):
        """Return the stack content, no permissions check
        """
        res = {}
        for level in self.getAllLevels():
            res[level] = self._getLevelContent(level=level)
        return res

    def _getStackElementIndex(self, elt, level=None):
        """Get stack element index in stack at given level

        If level is None, use current level.

        elt can either be a stack element or its id since stack element
        comparison says that's equivalent.

        >>> stack = HierarchicalStack()
        >>> stack._push('user:test1', level=0)
        1
        >>> stack._push('user:test2', level=0)
        1
        >>> stack._getStackElementIndex('user:test1', level=0)
        0
        >>> stack._getStackElementIndex('user:test2', level=0)
        1

        """
        if level is None:
            level = self.getCurrentLevel()
        i = 0
        for each in self._getLevelContent(level=level):
            if elt == each:
                return i
            i += 1
        return -1


    #
    # API
    #

    def setCurrentLevel(self, level):
        """Set the current level

        level has to hold elements

        >>> stack = HierarchicalStack()
        >>> stack.getCurrentLevel()
        0
        >>> stack.setCurrentLevel(1)
        >>> stack.getCurrentLevel() # 1 is empty
        0
        >>> stack._push('user:test1', level=1)
        1
        >>> stack.setCurrentLevel(1)
        >>> stack.getCurrentLevel()
        1

        """
        if level in self.getAllLevels():
            self._level = level

    def doIncLevel(self):
        """Increment the current level value, return new current level

        The new level has to hold elements

        >>> stack = HierarchicalStack()
        >>> stack.getCurrentLevel()
        0
        >>> stack.doIncLevel() # 1 is empty
        0
        >>> stack.getCurrentLevel()
        0
        >>> stack._push('user:test1', level=1)
        1
        >>> stack.doIncLevel()
        1
        >>> stack.getCurrentLevel()
        1

        """
        new_level = self.getCurrentLevel() + 1
        self.setCurrentLevel(new_level)
        return self.getCurrentLevel()

    def doDecLevel(self):
        """Decrement the current level value, return new current level

        The new level has to hold elements

        >>> stack = HierarchicalStack()
        >>> stack.getCurrentLevel()
        0
        >>> stack.doDecLevel() # -1 is empty
        0
        >>> stack.getCurrentLevel()
        0
        >>> stack._push('user:test1', level=-1)
        1
        >>> stack.doDecLevel()
        -1
        >>> stack.getCurrentLevel()
        -1

        """
        new_level = self.getCurrentLevel() - 1
        self.setCurrentLevel(new_level)
        return self.getCurrentLevel()

    def push(self, push_ids=(), levels=(), **kw):
        """Public push

        Return a code error:
        0 : failure on one of the pushes
        1 : success on all pushes

        Additional keywords will be used to pass additional data for each
        element to push.
        If levels are not given, push at current level.

        push_ids, levels and kw come from the wftool.doActionFor method
        keywords.
        strings are accepted for level values.

        >>> stack = HierarchicalStack()
        >>> push_ids = ['user:test1', 'user:test2']
        >>> levels = [0, '-1']
        >>> comment = ['comment for test1', 'comment for test2']
        >>> stack.push(push_ids, levels, data_list=['comment'], comment=comment)
        1
        >>> for level, content in stack._getStackContent().items():
        ...     print level, [x() for x in content]
        0 [{'comment': 'comment for test1', 'id': 'user:test1'}]
        -1 [{'comment': 'comment for test2', 'id': 'user:test2'}]

        """
        code = 1

        # find out data keys and corresponding data lists
        data_list = kw.get('data_list', ())
        data_info = dict((key, kw.get(key, [])) for key in data_list)

        current_level = self.getCurrentLevel()

        for index, push_id in enumerate(push_ids):
            # data
            data = {}
            for key, values in data_info.items():
                try:
                    data[key] = values[index]
                except IndexError:
                    pass
            # level
            level = current_level
            if levels:
                try:
                    level = levels[index]
                except IndexError:
                    pass
            try:
                level = int(level)
            except ValueError:
                # mid level
                pass
            if isinstance(level, int):
                code = code and self._push(push_id, level=level, data=data)
            else:
                # find out low and high level
                split = str(level).split('_')
                try:
                    low_level = int(split[0])
                    high_level = int(split[1])
                except (IndexError, ValueError):
                    # wrong user input
                    continue
                code = code and self._push(push_id, low_level=low_level,
                                           high_level=high_level, data=data)

        return code


    def pop(self, pop_ids=(), **kw):
        """Public pop

        Return a code error:
        0 : failure on one of the pops
        1 : success on all pops

        Convention used for pop_ids: 'level,prefix:elt_id'. Examples:
        '1,user:toto' or '2,group:titi'. If level is omitted, use current
        level.

        pop_ids and kw come from the wftool.doActionFor method keywords.

        >>> stack = HierarchicalStack()
        >>> push_ids = ['user:test1', 'user:test2', 'user:test1']
        >>> levels = [0, 0, 1]
        >>> stack.push(push_ids, levels)
        1
        >>> stack._getStackContent()
        {0: [<UserStackElement at user:test1>, <UserStackElement at
        user:test2>], 1: [<UserStackElement at user:test1>]}
        >>> pop_ids = ['0,user:test2', '1,user:test1']
        >>> stack.pop(pop_ids)
        1
        >>> stack._getStackContent()
        {0: [<UserStackElement at user:test1>]}

        """
        code = 1
        current_level = self.getCurrentLevel()
        for pop_id in pop_ids:
            sep = pop_id.find(',')
            if sep != -1:
                level = int(pop_id[:sep])
                the_id = pop_id[sep+1:]
            else:
                level = current_level
                the_id = pop_id
            code = code and self._pop(elt=the_id, level=level, **kw)

        return code


    def edit(self, edit_ids=(), **kw):
        """Public edit

        Return a code error:
        0 : failure on one of the edits
        1 : success on all edits

        Additional keywords will be used to pass additional data for each
        element to edit.

        Convention used for edit_ids: 'level,prefix:elt_id'. Examples:
        '1,user:toto' or '2,group:titi'. If level is omitted, use current
        level.

        edit_ids and kw come from the wftool.doActionFor method keywords.

        >>> stack = HierarchicalStack()
        >>> push_ids = ['user:test1', 'user:test2']
        >>> levels = [0, 1]
        >>> comment = ['comment for test1', 'comment for test2']
        >>> stack.push(push_ids, levels, data_list=['comment'], comment=comment)
        1
        >>> for level, content in stack._getStackContent().items():
        ...     print level, [x() for x in content]
        0 [{'comment': 'comment for test1', 'id': 'user:test1'}]
        1 [{'comment': 'comment for test2', 'id': 'user:test2'}]
        >>> edit_ids = ['0,user:test1', '1,user:test2']
        >>> comment = ['new comment for test1', 'new comment for test2 too']
        >>> stack.edit(edit_ids, data_list=['comment'], comment=comment)
        1
        >>> for level, content in stack._getStackContent().items():
        ...     print level, [x() for x in content]
        0 [{'comment': 'new comment for test1', 'id': 'user:test1'}]
        1 [{'comment': 'new comment for test2 too', 'id': 'user:test2'}]

        """
        code = 1

        # find out data keys and corresponding data lists
        data_list = kw.get('data_list', ())
        data_info = dict((key, kw.get(key, [])) for key in data_list)

        current_level = self.getCurrentLevel()

        for index, edit_id in enumerate(edit_ids):
            # data
            data = {}
            for key, values in data_info.items():
                try:
                    data[key] = values[index]
                except IndexError:
                    pass
            # level
            sep = edit_id.find(',')
            if sep != -1:
                level = int(edit_id[:sep])
                the_id = edit_id[sep+1:]
            else:
                level = current_level
                the_id = edit_id
            code = code and self._edit(the_id, level=level, data=data)
        return code

    def reset(self, **kw):
        """Reset the stack and return it.

        kw comes from the wftool.doActionFor method keywords:
        new_stack  : stack that might be a substitute of self
        reset_ids  : new elements to add to the stack
        levels : levels where new elements are added, defaults to current
        level.

        Additional keywords will be used by the push method.
        """
        new_stack = kw.get('new_stack')
        if new_stack is not None:
            # replace the stack container
            self._elements_container = new_stack._getElementsContainer()
            self.setCurrentLevel(new_stack.getCurrentLevel())
        else:
            self.__init__()

        # translate for push
        new_elts  = kw['push_ids'] = kw.get('reset_ids', ())
        if kw.get('levels') is None:
            # init with level 0
            kw['levels'] = len(new_elts)*[0]
        self.push(**kw)

        return self

    def getLevelContent(self, level=None, type='id', context=None, **kw):
        """Return content of given level

        If level is None, use current level.
        type can either be: id, str, call, role or object.
        context is the context in which will check the security on the element.
        """
        res = []
        content = self._getLevelContent(level)
        for each in content:
            if (context is None or
                not each.isVisible(sm=getSecurityManager(), stack=self,
                                   context=context)):
                each = ElementReg.makeWorkflowStackElementTypeInstance(
                    each.getHiddenMetaType(), 'hidden')
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

    def getStackContent(self, type='id', context=None, **kw):
        """Return the stack content

        type can either be: id, str, call, role or object.
        context is the context in which will check the security on the element.
        """
        res = {}
        for level in self.getAllLevels():
            res[level] = self.getLevelContent(level=level, type=type,
                                              context=context, **kw)
        return res



InitializeClass(HierarchicalStack)

#####################################################################
#####################################################################

WorkflowStackRegistry.register(SimpleStack)
WorkflowStackRegistry.register(HierarchicalStack)
