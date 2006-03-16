#!/usr/bin/python
# (C) Copyright 2004-2006 Nuxeo SAS <http://nuxeo.com>
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

import unittest
from zope.testing import doctest
from zope.interface.verify import verifyClass

from Products.CPSWorkflow.stack import Stack
from Products.CPSWorkflow.basicstacks import SimpleStack
from Products.CPSWorkflow.basicstacks import HierarchicalStack

from Products.CPSWorkflow.basicstackelements import UserStackElement
from Products.CPSWorkflow.basicstackelements import GroupStackElement

from Products.CPSWorkflow.interfaces import IWorkflowStack
from Products.CPSWorkflow.interfaces import ISimpleWorkflowStack
from Products.CPSWorkflow.interfaces import IHierarchicalWorkflowStack


class TestStack(unittest.TestCase):

    def test_interface(self):
        verifyClass(IWorkflowStack, Stack)


class TestSimpleStack(unittest.TestCase):

    def test_interface(self):
        verifyClass(IWorkflowStack, SimpleStack)
        verifyClass(ISimpleWorkflowStack, SimpleStack)

    def test_getCopy(self):
        stack1 = SimpleStack()
        self.assertEqual(stack1.meta_type, 'Simple Stack')
        stack2 = stack1.getCopy()
        self.assertEqual(stack2.meta_type, 'Simple Stack')

        self.assertNotEqual(stack2, None)
        self.assertNotEqual(stack1, stack2)

        self.assertEqual(stack1.getStackContent(context=self), [])
        self.assertEqual(stack2.getStackContent(context=self), [])

        self.assertEqual(stack1.getStackContent(context=self),
                         stack2.getStackContent(context=self))
        self.assertEqual(stack1.isFull(), stack2.isFull())
        self.assertEqual(stack1.isEmpty(), stack2.isEmpty())
        self.assertEqual(stack1.getSize(), stack2.getSize())

        stack1._push('elt1')
        stack2._push('elt2')
        self.assertEqual(stack1.getStackContent(context=self), ['elt1'])
        self.assertEqual(stack2.getStackContent(context=self), ['elt2'])

        self.assertNotEqual(stack1.getStackContent(context=self),
                            stack2.getStackContent(context=self))

    # XXX this test is too long, hard to maintain
    def test_NoMaxSize(self):
        # Test Base Stack with no initialization
        stack = SimpleStack()
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        code = stack._push('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        code = stack._push('elt1')
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding another element. (Allowed with this stack)
        code = stack._push('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop now
        code = stack._pop('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('fake')
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        code = stack._push('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Try to push a None element
        code = stack._push(None)
        self.assertEqual(code, 0)

    # XXX this test is too long, hard to maintain
    def test_WithMaxSize(self):
        # Test Base Stack with no initialization
        stack = SimpleStack(max_size=2)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        code = stack._push('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        code = stack._push('elt1')
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding another element.
        code = stack._push('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 1)

        # Pop now
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('fake')
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        code = stack._push('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Try to push a None element
        code = stack._push(None)
        self.assertEqual(code, 0)

    def test__getStackContent(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'])
        elements = [
            UserStackElement('user:elt1'),
            GroupStackElement('group:elt2'),
            ]
        self.assertEqual(stack._getStackContent(), elements)


    def test__getStackElementIndex(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'])
        self.assertEqual(stack._getStackElementIndex('user:elt1'), 0)
        self.assertEqual(stack._getStackElementIndex('group:elt2'), 1)


    def test__getManagers(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'])
        managers = [
            UserStackElement('user:elt1'),
            GroupStackElement('group:elt2'),
            ]
        self.assertEqual(stack._getManagers(), managers)

    def test_push(self):
        stack = SimpleStack()

        # Add a user
        stack.push(push_ids=['user:elt1'])
        elt = stack._getStackContent()[0]
        self.assertEqual(isinstance(elt, UserStackElement), True)
        self.assertEqual(elt, 'user:elt1')
        self.assertEqual(elt(), {'id': 'user:elt1'})

        # Add a group
        stack.push(push_ids=['group:elt2'])
        elt2 = stack._getStackContent()[1]
        self.assertEqual(isinstance(elt2, GroupStackElement), True)
        self.assertEqual(elt2, 'group:elt2')
        self.assertEqual(elt2(), {'id': 'group:elt2'})

    def test_push_with_data(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        elt = stack._getStackContent()[0]
        self.assertEqual(isinstance(elt, UserStackElement), True)
        self.assertEqual(elt, 'user:elt1')
        self.assertEqual(elt(), {'id': 'user:elt1',
                                 'comment': 'comment for 1'})
        elt2 = stack._getStackContent()[1]
        self.assertEqual(isinstance(elt2, GroupStackElement), True)
        self.assertEqual(elt2, 'group:elt2')
        self.assertEqual(elt2(), {'id': 'group:elt2',
                                 'comment': 'comment for 2'})

    def test_pop(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'])
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt1', 'group:elt2'])
        stack.pop(pop_ids=['group:elt2'])
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt1'])


    def test_pop_with_data(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt1', 'group:elt2'])
        stack.pop(pop_ids=['group:elt2'])
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt1'])

    def test_edit(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        content = [
            {'comment': 'comment for 1', 'id': 'user:elt1'},
            {'comment': 'comment for 2', 'id': 'group:elt2'},
            ]
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         content)
        stack.edit(edit_ids=['user:elt1', 'group:elt2'],
                   data_list=['comment'],
                   comment=['new comment for 1', 'new comment for 2 too'])
        content = [
            {'comment': 'new comment for 1', 'id': 'user:elt1'},
            {'comment': 'new comment for 2 too', 'id': 'group:elt2'},
            ]
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         content)

    def test_reset(self):
        simple = SimpleStack()
        self.assertEqual(simple.getMetaType(),
                         'Simple Stack')
        simple.push(push_ids=['elt1'])
        self.assertEqual(simple.getStackContent(context=self),
                         ['elt1'])
        simple.reset()
        self.assertEqual(simple.getMetaType(),
                         'Simple Stack')
        self.assertNotEqual(simple.getStackContent(context=self),
                            ['elt1'])
        self.assertEqual(simple.getStackContent(context=self),
                         [])

        simple.push(push_ids=['elt1'])
        self.assertEqual(simple.getStackContent(context=self),
                         ['elt1'])

    def test_reset_complex(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1'])
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt1'])

        # Reset with one (1) new user
        stack.reset(reset_ids=('user:elt2',))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('user:elt3', 'user:elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt3', 'user:elt4'])

        # Reset with one (1) new group
        stack.reset(reset_ids=('group:elt2',))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['group:elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['group:elt3', 'group:elt4'])

        # Reset with one new stack
        new_stack = SimpleStack()
        new_stack.push('new_elt')
        stack.reset(new_stack=new_stack)
        self.assertEqual(stack._getStackContent(),
                         new_stack._getStackContent())

        # Reset with a new stack, new users and new groups
        new_stack = SimpleStack()
        reset_ids = ('user:elt1', 'user:elt2', 'group:elt3', 'group:elt4')
        stack.reset(new_stack=new_stack, reset_ids=reset_ids)
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['user:elt1', 'user:elt2', 'group:elt3', 'group:elt4'])

    def test_getStackContent(self):
        stack = SimpleStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        # default: id
        self.assertEqual(stack.getStackContent(context=self),
                         ['user:elt1', 'group:elt2'])
        # without context: hidden
        self.assertEqual(stack.getStackContent(), ['hidden', 'hidden'])
        # str
        str_content = [
            "<UserStackElement {'comment': 'comment for 1', 'id': 'user:elt1'} >",
            "<GroupStackElement {'comment': 'comment for 2', 'id': 'group:elt2'} >",
            ]
        self.assertEqual(stack.getStackContent(type='str', context=self),
                         str_content)
        # call
        call_content = [
            {'comment': 'comment for 1', 'id': 'user:elt1'},
            {'comment': 'comment for 2', 'id': 'group:elt2'},
            ]
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         call_content)
        # role
        self.assertEqual(stack.getStackContent(type='role', context=self),
                         ['elt1', 'group:elt2'])
        # object (no check on stack element data for comparison)
        obj_content = [
            UserStackElement('user:elt1'),
            GroupStackElement('group:elt2'),
            ]
        self.assertEqual(stack.getStackContent(type='object', context=self),
                         obj_content)


class TestHierarchicalStack(unittest.TestCase):

    def test_interface(self):
        verifyClass(IWorkflowStack, HierarchicalStack)
        verifyClass(ISimpleWorkflowStack, HierarchicalStack)
        verifyClass(IHierarchicalWorkflowStack, HierarchicalStack)

    # XXX this test is too long, hard to maintain
    def test_NoMaxSize(self):

        #
        # This tests are all done at level 0 implicitly
        # They are the same as the one on the SimpleStack
        # The idea is to show it's possible the hierarchical stack
        # as a simple stack without having to care of the current level
        # It's just a validation of the implementation
        #

        # Test Base Stack with no initialization
        stack = HierarchicalStack()
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        code = stack._push('elt1', level=0)
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        code = stack._push('elt1', level=0)
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding same element, different level (allowed)
        code = stack._push('elt1', level=1)
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding another element.
        code = stack._push('elt2', level=0)
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 3)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop now, at current level
        code = stack._pop('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('fake')
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        code = stack._push('elt1', level=0)
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Try to push a None element
        code = stack._push(None)
        self.assertEqual(code, 0)

    # XXX this test is too long, hard to maintain
    def test_NoMaxSizeWithLevels(self):

        #
        # Now this tests test the levels
        #

        # Test Base Stack with no initialization
        stack = HierarchicalStack()

        self.assertEqual(stack.getSize(level=-1), 0)
        self.assertEqual(stack.getSize(level=0), 0)
        self.assertEqual(stack.getSize(level=1), 0)

        self.assertEqual(stack.isEmpty(level=-1), 1)
        self.assertEqual(stack.isEmpty(level=0), 1)
        self.assertEqual(stack.isEmpty(level=1), 1)

        self.assertEqual(stack.isFull(level=-1), 0)
        self.assertEqual(stack.isFull(level=0), 0)
        self.assertEqual(stack.isFull(level=1), 0)


        # Adding one element at level 0
        stack._push('elt1', level=0)

        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.getSize(level=0), 1)

        self.assertEqual(stack.getSize(level=1), 0)
        self.assertEqual(stack.getSize(level=-1), 0)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)

        self.assertEqual(stack.isEmpty(level=-1), 1)
        self.assertEqual(stack.isEmpty(level=1), 1)

        self.assertEqual(stack.isFull(), 0)
        self.assertEqual(stack.isFull(level=0), 0)

        self.assertEqual(stack.isFull(level=-1), 0)
        self.assertEqual(stack.isFull(level=1), 0)

        # Adding one element at level -1
        stack._push('elt-1', level=-1)
        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.getSize(level=0), 1)
        self.assertEqual(stack.getSize(level=1), 0)
        self.assertEqual(stack.getSize(level=-1), 1)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)

        self.assertEqual(stack.isEmpty(level=-1), 0)
        self.assertEqual(stack.isEmpty(level=1), 1)

        self.assertEqual(stack.isFull(), 0)
        self.assertEqual(stack.isFull(level=0), 0)

        self.assertEqual(stack.isFull(level=-1), 0)
        self.assertEqual(stack.isFull(level=1), 0)

        # Adding one element at level 1
        stack._push('elt11', level=1)

        self.assertEqual(stack.getSize(), 3)
        self.assertEqual(stack.getSize(level=0), 1)

        self.assertEqual(stack.getSize(level=1), 1)
        self.assertEqual(stack.getSize(level=-1), 1)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)

        self.assertEqual(stack.isEmpty(level=-1), 0)
        self.assertEqual(stack.isEmpty(level=1), 0)

        self.assertEqual(stack.isFull(), 0)
        self.assertEqual(stack.isFull(level=0), 0)

        self.assertEqual(stack.isFull(level=-1), 0)
        self.assertEqual(stack.isFull(level=1), 0)

        # Adding same element at each level  (Not allowed with this stack)

        # Level 0
        res = stack._push('elt1', level=0)
        self.assertEqual(res, 0)

        res = stack._push('elt-1', level=0)
        self.assertEqual(res, 1)

        res = stack._push('elt11', level=0)
        self.assertEqual(res, 1)

        # Level -1
        res = stack._push('elt-1', level=-1)
        self.assertEqual(res, 0 )

        res = stack._push('elt1', level=-1)
        self.assertEqual(res, 1)

        res = stack._push('elt11', level=-1)
        self.assertEqual(res, 1)

        # Level 1
        res = stack._push('elt11', level=1)
        self.assertEqual(res, 0 )

        res = stack._push('elt-1', level=1)
        self.assertEqual(res, 1)

        res = stack._push('elt1', level=1)
        self.assertEqual(res, 1)

        self.assertEqual(stack.getSize(), 9)
        self.assertEqual(stack.getSize(level=0), 3)
        self.assertEqual(stack.getSize(level=-1), 3)
        self.assertEqual(stack.getSize(level=1), 3)

        # Check level 0 (current level)
        self.assertEqual(stack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(stack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['elt11','elt-1','elt1'])

        # Dec Level
        clevel = stack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, stack.getCurrentLevel())

        # Check the level content
        self.assertEqual(stack.getLevelContent(context=self),
                         stack.getLevelContent(
            level=stack.getCurrentLevel(), context=self))
        self.assertEqual(stack.getLevelContent(context=self),
                         stack.getLevelContent(level=-1, context=self))
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt-1','elt1','elt11'])

        # Check the consistency of the rest
        self.assertEqual(stack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['elt11','elt-1','elt1'])

        # Increment now
        clevel = stack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, stack.getCurrentLevel())

        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(stack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['elt11','elt-1','elt1'])

        # Increment again
        clevel = stack.doIncLevel()
        self.assertEqual(clevel, 1)
        self.assertEqual(clevel, stack.getCurrentLevel())

        # Check the level content
        self.assertEqual(stack.getLevelContent(context=self),
                         stack.getLevelContent(level=stack.getCurrentLevel(),
                                                context=self))
        self.assertEqual(stack.getLevelContent(context=self),
                         stack.getLevelContent(level=1, context=self))
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt11','elt-1','elt1'])

        # Check levels
        self.assertEqual(stack.getAllLevels(), [-1, 0, 1])

        # Let's test the remove / pop API

        # Pop element at current level (1)
        self.assertEqual(stack.getCurrentLevel(), 1)
        self.assertEqual(stack.pop(pop_ids=('elt1',)), 1)

        # Let's check the consistency of the rest
        self.assertEqual(stack.getSize(), 8)
        self.assertEqual(stack.getSize(level=0), 3)
        self.assertEqual(stack.getSize(level=1), 2)
        self.assertEqual(stack.getSize(level=-1), 3)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)
        self.assertEqual(stack.isEmpty(level=-1), 0)
        self.assertEqual(stack.isEmpty(level=1), 0)

        # Pop element at level 0
        # not found
        self.assertEqual(stack.getCurrentLevel(), 1)
        self.assertEqual(stack.pop(pop_ids=['fake']), 0)

        # Let's check the consistency of the rest
        self.assertEqual(stack.getSize(level=0), 3)
        self.assertEqual(stack.getSize(), 8)
        self.assertEqual(stack.getSize(level=1), 2)
        self.assertEqual(stack.getSize(level=-1), 3)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)
        self.assertEqual(stack.isEmpty(level=-1), 0)
        self.assertEqual(stack.isEmpty(level=1), 0)

        # Pop element at level -1
        self.assertEqual(stack.getCurrentLevel(), 1)
        self.assertEqual(stack.pop(pop_ids=('1,elt11',)), 1)

        # Let's check the consistency of the rest
        self.assertEqual(stack.getSize(), 7)
        self.assertEqual(stack.getSize(level=0), 3)
        self.assertEqual(stack.getSize(level=1), 1)
        self.assertEqual(stack.getSize(level=-1), 3)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)
        self.assertEqual(stack.isEmpty(level=-1), 0)
        self.assertEqual(stack.isEmpty(level=1), 0)

        # Let's change level
        clevel = stack.doDecLevel()
        self.assertEqual(clevel, stack.getCurrentLevel())
        self.assertEqual(clevel, 0)

        # Let's check the consistency of the rest
        self.assertEqual(stack.getSize(), 7)
        self.assertEqual(stack.getSize(level=0), 3)
        self.assertEqual(stack.getSize(level=1), 1)
        self.assertEqual(stack.getSize(level=-1), 3)

        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isEmpty(level=0), 0)
        self.assertEqual(stack.isEmpty(level=-1), 0)
        self.assertEqual(stack.isEmpty(level=1), 0)

        # Check now the pop
        self.assertEqual(stack.pop(pop_ids=('XXX',)), 0)
        self.assertEqual(stack.pop(pop_ids=('89,elt1',)), 0)
        self.assertEqual(stack.pop(pop_ids=('elt1',)), 1)
        self.assertEqual(stack.getSize(), 6)
        self.assertEqual(stack.getSize(level=stack.getCurrentLevel()), 2)
        self.assertEqual(stack.getSize(level=0), 2)
        self.assertEqual(stack.pop(pop_ids=('elt1',)), 0)
        self.assertEqual(stack.pop(pop_ids=('elt-1', 'elt11')), 1)
        self.assertEqual(stack.getSize(), 4)
        self.assertEqual(stack.isEmpty(), False)

        # Check levels
        self.assertEqual(stack.getAllLevels(), [-1, 1])
        clevel = stack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, stack.getCurrentLevel())

        # Not possible to go back to level 0 (empty)
        clevel = stack.doIncLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, stack.getCurrentLevel())

        # Add an elemet to level 0
        self.assertEqual(stack._push(elt='elt1', level=0), 1)

        # Now possible to go back to level 0
        clevel = stack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, stack.getCurrentLevel())

        # Let's empty evrything at level -1
        clevel = stack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, stack.getCurrentLevel())
        self.assertEqual(stack.pop(pop_ids=('elt1', 'elt-1', 'elt11')), 1)
        # Empty now (-1)
        self.assertEqual(stack.isEmpty(level=-1), 1)

        # Go back to 0
        clevel = stack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, stack.getCurrentLevel())

        # Trying to go back to -1
        clevel = stack.doDecLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, stack.getCurrentLevel())
        # ... now way... let's pop the level 0

        self.assertEqual(stack.pop(pop_ids=['elt1']), 1)
        # Empty now at level (0)
        self.assertEqual(stack.isEmpty(level=0), 1)

        # Go to 1
        clevel = stack.doIncLevel()
        self.assertEqual(clevel, 1)
        self.assertEqual(clevel, stack.getCurrentLevel())

        self.assertEqual(stack.pop(pop_ids=('elt-1',)), 1)
        # Empty now (1)
        self.assertEqual(stack.isEmpty(), 1)

        # Check the status of the stack now
        self.assertEqual(stack.getAllLevels(), [])
        self.assertEqual(stack.getLevelContent(context=self), [])
        self.assertEqual(stack.getLevelContent(level=-1, context=self), [])
        self.assertEqual(stack.getLevelContent(level=0, context=self), [])
        self.assertEqual(stack.getLevelContent(level=1, context=self), [])

        # Check weird stuffs
        self.assertEqual(stack.getLevelContent(level=90000, context=self), [])
        self.assertEqual(stack.pop(pop_ids=('90000,weird',)), 0)

    # XXX this test is too long, hard to maintain
    def test_WithMaxSize(self):

        #
        # This tests are all done at level 0 implicitly
        # They are the same as the one on the SimpleStack
        # The idea is to show it's possible to use the hierarchical stack
        # as a simple stack without having to care of the current level
        # It's just a validation of the implementation
        #

        # Test Base Stack with no initialization
        stack = HierarchicalStack(max_size=2)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        stack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = stack._push('elt1')
        self.assertEqual(res, 0)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1']})

        # Adding another element.
        code = stack._push('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1','elt2']})

        self.assertEqual(stack.getSize(), 2)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 1)

        # Pop now
        code = stack._pop('elt2')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('fake')
        self.assertEqual(code, 0)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Adding one element
        stack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(stack.getSize(), 1)
        self.assertEqual(stack.isEmpty(), 0)
        self.assertEqual(stack.isFull(), 0)

        # Pop again
        code = stack._pop('elt1')
        self.assertEqual(code, 1)
        self.assertEqual(stack.getSize(), 0)
        self.assertEqual(stack.isEmpty(), 1)
        self.assertEqual(stack.isFull(), 0)

        # Try to push a None element
        code = stack._push(None)
        self.assertEqual(code, 0)

        stack = HierarchicalStack()

        # Test the pop() method
        self.assertEqual(stack.getStackContent(context=self), {})
        self.assertEqual(stack.pop(pop_ids=['elt1']), 0)
        stack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(stack.pop(pop_ids=['elt1']), 1)
        stack.push(push_ids=['elt1'], levels=[0])
        stack.push(push_ids=['elt2'], levels=[0])
        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1', 'elt2']})
        stack.push(push_ids=['elt3'], levels=[0])
        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1', 'elt2', 'elt3']})
        self.assertEqual(stack.pop(pop_ids=['elt2']), 1)
        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1', 'elt3']})

        stack.pop(pop_ids=['0,elt3'])
        stack.pop(pop_ids=['0,elt1'])
        self.assertEqual(stack.getStackContent(context=self), {})

    def test_getCopy(self):
        # check copy is not the same object
        stack1 = HierarchicalStack()
        self.assertEqual(stack1.meta_type, 'Hierarchical Stack')
        stack2 = stack1.getCopy()
        self.assertEqual(stack2.meta_type, 'Hierarchical Stack')

        self.assertNotEqual(stack2, None)
        self.assertNotEqual(stack1, stack2)

        self.assertEqual(stack1.getStackContent(context=self), {})
        self.assertEqual(stack2.getStackContent(context=self), {})

        self.assertEqual(stack1.getStackContent(context=self),
                         stack2.getStackContent(context=self))
        self.assertEqual(stack1.isFull(), stack2.isFull())
        self.assertEqual(stack1.isEmpty(), stack2.isEmpty())
        self.assertEqual(stack1.getSize(), stack2.getSize())

        stack1._push('elt1', level=0)
        stack2._push('elt2', level=0)
        self.assertEqual(stack1.getLevelContent(context=self), ['elt1'])
        self.assertEqual(stack2.getLevelContent(context=self), ['elt2'])

        self.assertNotEqual(stack1.getStackContent(context=self),
                            stack2.getStackContent(context=self))


    def test_getCopy_with_data(self):
        # check copy is not the same object, nor data
        stack1 = HierarchicalStack()
        self.assertEqual(stack1.meta_type, 'Hierarchical Stack')
        stack1._push('elt1', level=0, data={'comment': "comment for 1"})
        stack2 = stack1.getCopy()
        self.assertEqual(stack2.meta_type, 'Hierarchical Stack')

        self.assertNotEqual(stack2, None)
        self.assertNotEqual(stack1, stack2)

        self.assertEqual(stack1.getStackContent(context=self),
                         {0: ['elt1']})
        self.assertEqual(stack2.getStackContent(context=self),
                         {0: ['elt1']})

        self.assertEqual(stack1.getStackContent(context=self),
                         stack2.getStackContent(context=self))
        self.assertEqual(stack1.isFull(), stack2.isFull())
        self.assertEqual(stack1.isEmpty(), stack2.isEmpty())
        self.assertEqual(stack1.getSize(), stack2.getSize())

        stack2._push('elt2', level=0, data={'comment': "comment for 2"})
        self.assertEqual(stack1.getLevelContent(type='call', context=self),
                         [{'id': 'elt1', 'comment': 'comment for 1'}])
        self.assertEqual(stack2.getLevelContent(type='call', context=self),
                         [{'id': 'elt1', 'comment': 'comment for 1'},
                          {'id': 'elt2', 'comment': 'comment for 2'}])

        self.assertNotEqual(stack1.getStackContent(context=self),
                            stack2.getStackContent(context=self))


    def test__getManagers(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'], levels=[0, 1])
        # current level is 0
        managers = [
            UserStackElement('user:elt1'),
            ]
        self.assertEqual(stack._getManagers(), managers)

    def test__getLevelContent(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'], levels=[0, 1])
        # current level is 0
        self.assertEqual(stack._getLevelContent(),
                         [UserStackElement('user:elt1')])
        self.assertEqual(stack._getLevelContent(level=1),
                         [GroupStackElement('group:elt2')])

    def test__getStackContent(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'], levels=[0, 1])
        stack_content = {
            0: [UserStackElement('user:elt1')],
            1: [GroupStackElement('group:elt2')],
            }
        self.assertEqual(stack._getStackContent(), stack_content)

    def test__getStackElementIndex(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'user:elt2', 'user:elt2'],
                   levels=[0, 0, 1])
        self.assertEqual(stack._getStackElementIndex('user:elt1'), 0)
        self.assertEqual(stack._getStackElementIndex('user:elt2'), 1)
        self.assertEqual(stack._getStackElementIndex('user:elt2', level=1), 0)

    def test_push(self):
        stack = HierarchicalStack()

        # Add a user
        stack.push(push_ids=['elt1'], levels=[0])
        elt = stack._getStackContent()[0][0]
        self.assert_(isinstance(elt, UserStackElement))
        self.assert_(elt == 'elt1')

        # Add a group
        stack.push(push_ids=['group:elt2'], levels=[0])
        elt2 = stack._getStackContent()[0][1]
        self.assert_(isinstance(elt2, GroupStackElement))
        self.assert_(elt2 == 'group:elt2')

    def test_push_with_data(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   levels=[0, 1],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        elt = stack._getStackContent()[0][0]
        self.assertEqual(isinstance(elt, UserStackElement), True)
        self.assertEqual(elt, 'user:elt1')
        self.assertEqual(elt(), {'id': 'user:elt1',
                                 'comment': 'comment for 1'})
        elt2 = stack._getStackContent()[1][0]
        self.assertEqual(isinstance(elt2, GroupStackElement), True)
        self.assertEqual(elt2, 'group:elt2')
        self.assertEqual(elt2(), {'id': 'group:elt2',
                                 'comment': 'comment for 2'})

    def test_pop(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2', 'user:elt1'],
                   levels=[0, 0, 1],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2', 'other comment'])
        content = {
            0: [{'comment': 'comment for 1', 'id': 'user:elt1'},
                {'comment': 'comment for 2', 'id': 'group:elt2'}],
            1: [{'comment': 'other comment', 'id': 'user:elt1'}],
            }
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         content)
        stack.pop(pop_ids=['0,group:elt2', '1,user:elt1'])
        content = {
            0: [{'comment': 'comment for 1', 'id': 'user:elt1'}],
            }
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         content)


    def test_edit(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2', 'user:elt3'],
                   levels=[0, 0, 1],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2', 'other comment'])
        content = {
            0: [{'comment': 'comment for 1', 'id': 'user:elt1'},
                {'comment': 'comment for 2', 'id': 'group:elt2'}],
            1: [{'comment': 'other comment', 'id': 'user:elt3'}],
            }
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         content)
        stack.edit(edit_ids=['0,user:elt1', '1,user:elt3'],
                   data_list=['comment'],
                   comment=['new comment for 1', 'another great comment'])
        content = {
            0: [{'comment': 'new comment for 1', 'id': 'user:elt1'},
                {'comment': 'comment for 2', 'id': 'group:elt2'}],
            1: [{'comment': 'another great comment', 'id': 'user:elt3'}],
            }
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         content)

    def test_insertInBetweenLevels(self):
        stack = HierarchicalStack()
        self.assertEqual(stack.getStackContent(), {})

        # Normal
        stack._push('elt1', level=0)
        stack._push('elt3', level=1)
        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1'], 1:['elt3']})

        # Insert in between 0 and 1
        # current_level is 0
        self.assertEqual(stack.getCurrentLevel(), 0)
        stack._push('elt2', low_level=0, high_level=1)
        self.assertEqual(stack.getStackContent(context=self),
                         {0:['elt1'],
                          1:['elt2'],
                          2:['elt3'],
                          })
        # Change current level and try to insert
        # 0 is the edge level where we need to test
        stack.doIncLevel()
        self.assertEqual(stack.getCurrentLevel(), 1)
        stack._push('elt4', low_level=0, high_level=1)
        self.assertEqual(stack.getStackContent(context=self),
                         {-1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          })
        stack._push('elt5', low_level=2, high_level=3)
        self.assertEqual(stack.getStackContent(context=self),
                         {-1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        stack._push('elt6', low_level=-2, high_level=-1)
        self.assertEqual(stack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        stack._push('elt7', low_level=-4, high_level=-3)
        self.assertEqual(stack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        stack._push('elt7', low_level=4, high_level=5)
        self.assertEqual(stack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })

    def test_level_api(self):
        stack = HierarchicalStack()

        # no upper nor lower level here.
        self.assertEqual(stack.hasUpperLevel(), False)
        self.assertEqual(stack.hasLowerLevel(), False)

        # Add someone at level 0
        stack.push(push_ids=['base'], levels=[0])
        self.assertEqual(stack.hasUpperLevel(), False)
        self.assertEqual(stack.hasLowerLevel(), False)

        # Add someone at level 1
        stack.push(push_ids=['elt1'], levels=[1])
        self.assertEqual(stack.hasUpperLevel(), True)
        self.assertEqual(stack.hasLowerLevel(), False)

        # Add someone at level -1
        stack.push(push_ids=['elt2'], levels=[-1])
        self.assertEqual(stack.hasUpperLevel(), True)
        self.assertEqual(stack.hasLowerLevel(), True)

        # Dec level
        stack.doDecLevel()
        self.assertEqual(stack.getCurrentLevel(), -1)
        self.assertEqual(stack.hasUpperLevel(), True)
        self.assertEqual(stack.hasLowerLevel(), False)

        # Inc level
        stack.doIncLevel()
        self.assertEqual(stack.getCurrentLevel(), 0)
        self.assertEqual(stack.hasUpperLevel(), True)
        self.assertEqual(stack.hasLowerLevel(), True)

        # Inc level
        stack.doIncLevel()
        self.assertEqual(stack.getCurrentLevel(), 1)
        self.assertEqual(stack.hasUpperLevel(), False)
        self.assertEqual(stack.hasLowerLevel(), True)

        # Dec level
        stack.doDecLevel()
        self.assertEqual(stack.getCurrentLevel(), 0)

        # Remove elt2 at level -1
        stack.pop(pop_ids=['-1,elt2'])
        self.assertEqual(stack.hasUpperLevel(), True)
        self.assertEqual(stack.hasLowerLevel(), False)

        # Remove elt1 at level 1
        stack.pop(pop_ids=['1,elt1'])
        self.assertEqual(stack.hasUpperLevel(), False)
        self.assertEqual(stack.hasLowerLevel(), False)


    def test_getInsertLevels(self):
        stack = HierarchicalStack()
        levels = [0, 1, 2]
        for level in levels:
            stack._push('elt', level)
        self.assertEquals(stack.getInsertLevels(),
                          [-1, 0, '0_1', 1, '1_2', 2, 3])
        self.assertEquals(stack.getInsertLevels(between=False),
                          [-1, 0, 1, 2, 3])


    def test_getInsertLevels_with_empty(self):
        # with empty levels, e.g holes between levels
        stack = HierarchicalStack()
        levels = [0, 2, 3]
        for level in levels:
            stack._push('elt', level)
        self.assertEquals(stack.getInsertLevels(),
                          [-1, 0, 1, 2, '2_3', 3, 4])
        self.assertEquals(stack.getInsertLevels(between=False),
                          [-1, 0, 1, 2, 3, 4])


    def test_getInsertLevels_complex(self):
        # complicated with negative values :)
        stack = HierarchicalStack()
        levels = [-3, -2, -1, 0, 1, 4, 5, 6, 9]
        for level in levels:
            stack._push('elt', level)
        all_between_levels = [-4, -3, '-3_-2', -2, '-2_-1', -1, '-1_0', 0,
                              '0_1', 1, 2, 4, '4_5', 5, '5_6', 6, 7, 9, 10]
        self.assertEquals(stack.getInsertLevels(),
                          all_between_levels)
        all_levels = [-4, -3, -2, -1, 0, 1, 2, 4, 5, 6, 7, 9, 10]
        self.assertEquals(stack.getInsertLevels(between=False),
                          all_levels)


    def test_reset(self):
        hierarchical = HierarchicalStack()
        self.assertEqual(hierarchical.getMetaType(),
                         'Hierarchical Stack')
        self.assertEqual(hierarchical.getStackContent(context=self),
                         {})
        hierarchical.push(push_ids=['elt1'], levels=[0])
        self.assertNotEqual(hierarchical.getStackContent(context=self),
                            {})
        self.assertEqual(hierarchical.getLevelContent(context=self),
                         ['elt1'])
        hierarchical.reset()
        self.assertEqual(hierarchical.getStackContent(context=self),
                         {})
        self.assertEqual(hierarchical.getMetaType(),
                         'Hierarchical Stack')
        self.assertNotEqual(hierarchical.getLevelContent(context=self),
                            ['elt1'])
        self.assertEqual(hierarchical.getLevelContent(context=self),
                         [])

        hierarchical.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(hierarchical.getLevelContent(context=self),
                         ['elt1'])

    def test_reset_complex(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1'], levels=[0])
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['user:elt1']})

        # Reset with one (1) new user
        stack.reset(reset_ids=('user:elt2',))
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['user:elt2']})

        # Reset with two (2) new users
        stack.reset(reset_ids=('user:elt3', 'user:elt4'))
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['user:elt3', 'user:elt4']})

        # Reset with one (1) new group
        stack.reset(reset_ids=('group:elt2',))
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['group:elt2']})

        # Reset with two (2) new users and levels
        stack.reset(reset_ids=('group:elt3', 'group:elt4'), levels=[0, 1])
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['group:elt3'], 1: ['group:elt4']})

        # Reset with one new stack
        new_stack = HierarchicalStack()
        new_stack.push(push_ids=['user:elt1', 'user:elt2'], levels=[0, 1])
        new_stack.doIncLevel()
        self.assertEqual(stack.getCurrentLevel(), 0)
        self.assertEqual(new_stack.getCurrentLevel(), 1)
        stack.reset(new_stack=new_stack)
        self.assertEqual(stack._getStackContent(),
                         new_stack._getStackContent())
        self.assertEqual(stack.getCurrentLevel(),
                         new_stack.getCurrentLevel())

        # Reset with a new stack, new users and new groups
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1'], levels=[0])
        reset_ids = ('group:elt3', 'group:elt4')
        stack.reset(new_stack=new_stack, reset_ids=reset_ids)
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['user:elt1', 'group:elt3', 'group:elt4'],
                          1: ['user:elt2']})
        self.assertEqual(stack.getCurrentLevel(), 1)


    def test_getLevelContent(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        # default: id
        self.assertEqual(stack.getLevelContent(context=self),
                         ['user:elt1', 'group:elt2'])
        # without context: hidden
        self.assertEqual(stack.getLevelContent(), ['hidden', 'hidden'])
        # str
        str_content = [
            "<UserStackElement {'comment': 'comment for 1', 'id': 'user:elt1'} >",
            "<GroupStackElement {'comment': 'comment for 2', 'id': 'group:elt2'} >",
            ]
        self.assertEqual(stack.getLevelContent(type='str', context=self),
                         str_content)
        # call
        call_content = [
            {'comment': 'comment for 1', 'id': 'user:elt1'},
            {'comment': 'comment for 2', 'id': 'group:elt2'},
            ]
        self.assertEqual(stack.getLevelContent(type='call', context=self),
                         call_content)
        # role
        self.assertEqual(stack.getLevelContent(type='role', context=self),
                         ['elt1', 'group:elt2'])
        # object (no check on stack element data for comparison)
        obj_content = [
            UserStackElement('user:elt1'),
            GroupStackElement('group:elt2'),
            ]
        self.assertEqual(stack.getLevelContent(type='object', context=self),
                         obj_content)

    def test_getStackContent(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'],
                   levels = [0, 1],
                   data_list=['comment'],
                   comment=['comment for 1', 'comment for 2'])
        # default: id
        self.assertEqual(stack.getStackContent(context=self),
                         {0: ['user:elt1'], 1: ['group:elt2']})
        # without context: hidden
        self.assertEqual(stack.getStackContent(), {0: ['hidden'], 1: ['hidden']})
        # str
        str_content = {
            0: ["<UserStackElement {'comment': 'comment for 1', 'id': 'user:elt1'} >"],
            1: ["<GroupStackElement {'comment': 'comment for 2', 'id': 'group:elt2'} >"],
            }
        self.assertEqual(stack.getStackContent(type='str', context=self),
                         str_content)
        # call
        call_content = {
            0: [{'comment': 'comment for 1', 'id': 'user:elt1'}],
            1: [{'comment': 'comment for 2', 'id': 'group:elt2'}],
            }
        self.assertEqual(stack.getStackContent(type='call', context=self),
                         call_content)
        # role
        self.assertEqual(stack.getStackContent(type='role', context=self),
                        {0: ['elt1'], 1: ['group:elt2']})
        # object (no check on stack element data for comparison)
        obj_content = {
            0: [UserStackElement('user:elt1')],
            1: [GroupStackElement('group:elt2')],
            }
        self.assertEqual(stack.getStackContent(type='object', context=self),
                         obj_content)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStack))
    suite.addTest(unittest.makeSuite(TestSimpleStack))
    suite.addTest(unittest.makeSuite(TestHierarchicalStack))
    suite.addTest(doctest.DocFileTest('basicstacks.py',
                                      package='Products.CPSWorkflow',
                                      optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS))

    return suite

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
