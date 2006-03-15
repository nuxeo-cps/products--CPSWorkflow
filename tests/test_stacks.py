#!/usr/bin/python
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

import unittest

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

    def test_NoMaxSize(self):
        # Test Base Stack with no initialization
        sstack = SimpleStack()
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Adding another element. (Allowed with this stack)
        sstack.push(push_ids=['elt2'])
        self.assertEqual(sstack.getSize(), 2)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop now
        code = sstack.pop(pop_ids=('elt2',))
        self.assertEqual(code, 1)
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        code = sstack.pop(pop_ids=('elt1',))
        self.assertEqual(code, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        code = sstack.pop(pop_ids=('fake',))
        self.assertEqual(code, 0)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        code = sstack.pop(pop_ids=('elt1',))
        self.assertEqual(code, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Try to push a None element
        code = sstack.push(None)
        self.assertEqual(code, -1)

    def test_WithMaxSize(self):
        # Test Base Stack with no initialization
        sstack = SimpleStack(maxsize=2)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        self.assertEqual(sstack.getStackContent(context=self),
                         ['elt1'])

        # Adding another element.
        res = sstack.push(push_ids=['elt2'])

        self.assertEqual(sstack.getStackContent(context=self),
                         ['elt1','elt2'])

        self.assertEqual(sstack.getSize(), 2)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 1)

        # Pop now
        code = sstack.pop(pop_ids=('elt1',))
        self.assertEqual(code, 1)
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        code = sstack.pop(pop_ids=('elt2',))
        self.assertEqual(code, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        code = sstack.pop(pop_ids=('fake',))
        self.assertEqual(code, 0)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        code = sstack.pop(pop_ids=('elt1',))
        self.assertEqual(code, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Try to push a None element
        res = sstack.push(None)
        self.assertEqual(res, -1)

        sstack = SimpleStack()

        # Test the pop() method
        self.assertEqual(sstack.getStackContent(context=self), [])
        self.assertEqual(sstack.pop(pop_ids=['elt1']), 0)
        sstack.push(push_ids=['elt1'])
        self.assertEqual(sstack.pop(pop_ids=['elt1']), 1)
        sstack.push(push_ids=['elt1'])
        sstack.push(push_ids=['elt2'])
        self.assertEqual(sstack.getStackContent(context=self),
                         ['elt1', 'elt2'])
        sstack.push(push_ids=['elt3'])
        self.assertEqual(sstack.getStackContent(context=self),
                         ['elt1', 'elt2', 'elt3'])
        self.assertEqual(sstack.pop(pop_ids=('elt2',)), 1)
        self.assertEqual(sstack.getStackContent(context=self),
                         ['elt1', 'elt3'])

        sstack.pop(pop_ids=['elt3'])
        sstack.pop(pop_ids=['elt1'])
        self.assertEqual(sstack.getStackContent(context=self), [])

    def test_getCopy(self):
        sstack1 = SimpleStack()
        self.assertEqual(sstack1.meta_type, 'Simple Stack')
        sstack2 = sstack1.getCopy()
        self.assertEqual(sstack2.meta_type, 'Simple Stack')

        self.assertNotEqual(sstack2, None)
        self.assertNotEqual(sstack1, sstack2)

        self.assertEqual(sstack1.getStackContent(context=self), [])
        self.assertEqual(sstack2.getStackContent(context=self), [])

        self.assertEqual(sstack1.getStackContent(context=self),
                         sstack2.getStackContent(context=self))
        self.assertEqual(sstack1.isFull(), sstack2.isFull())
        self.assertEqual(sstack1.isEmpty(), sstack2.isEmpty())
        self.assertEqual(sstack1.getSize(), sstack2.getSize())

        sstack1.push('elt1')
        sstack2.push('elt2')
        self.assertEqual(sstack1.getStackContent(context=self), ['elt1'])
        self.assertEqual(sstack2.getStackContent(context=self), ['elt2'])

        self.assertNotEqual(sstack1.getStackContent(context=self),
                            sstack2.getStackContent(context=self))

    def test_push(self):
        sstack = SimpleStack()

        # Add a user
        sstack.push(push_ids=['elt1'])
        elt = sstack._getStackContent()[0]
        self.assert_(isinstance(elt, UserStackElement))
        self.assert_(elt == 'elt1')

        # Add a group
        sstack.push(push_ids=['group:elt2'])
        elt2 = sstack._getStackContent()[1]
        self.assert_(isinstance(elt2, GroupStackElement))
        self.assert_(elt2 == 'group:elt2')

    def test_getManagers(self):
        sstack = SimpleStack()
        sstack.push(push_ids=['user:elt1', 'group:elt2'])
        managers = [
            UserStackElement('user:elt1'),
            GroupStackElement('group:elt2'),
            ]
        self.assertEqual(sstack._getManagers(), managers)

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

        #
        # Test the reset behavior on the Stack class type
        #

        stack = SimpleStack()
        stack.push(push_ids=['elt1'])
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['elt1'])

        # Reset with one (1) new user
        stack.reset(reset_ids=('elt2',))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('elt3', 'elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['elt3', 'elt4'])

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
        stack.reset(new_stack=new_stack,
                   reset_ids=('elt1', 'elt2', 'group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()],
                         ['elt1', 'elt2', 'group:elt3', 'group:elt4'])

    def test_replace(self):
        #
        # Test with strings
        #

        stack = SimpleStack()
        stack.push(push_ids=['elt1'])
        stack.push(push_ids=['elt2'])
        self.assertEqual(stack.getStackContent(context=self), ['elt1', 'elt2'])
        stack.replace('elt2', 'elt4')
        self.assertEqual(stack.getStackContent(context=self), ['elt1', 'elt4'])

        #
        # Test with elements objects
        #

        oelt = UserStackElement('string_elt')
        stack.replace('elt4', oelt)
        self.assertEqual(stack.getStackContent(context=self), ['elt1', 'string_elt'])


class TestHierarchicalStack(unittest.TestCase):

    def test_interface(self):
        verifyClass(IWorkflowStack, HierarchicalStack)
        verifyClass(ISimpleWorkflowStack, HierarchicalStack)
        verifyClass(IHierarchicalWorkflowStack, HierarchicalStack)

    def test_NoMaxSize(self):

        #
        # This tests are all done at level 0 implicitly
        # They are the same as the one on the SimpleStack
        # The idea is to show it's possible the hierarchical stack
        # as a simple stack without having to care of the current level
        # It's just a validation of the implementation
        #

        # Test Base Stack with no initialization
        hstack = HierarchicalStack()
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Adding one element
        hstack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = hstack.push('elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Adding another element. (Allowed with this stack)
        hstack.push(push_ids=['elt2'], levels=[0])
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop now
        code = hstack.pop(pop_ids=('elt2',))
        self.assertEqual(code, 1)
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        code = hstack.pop(pop_ids=['elt1'])
        self.assertEqual(code, 1)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        code = hstack.pop(pop_ids=('fake',))
        self.assertEqual(code, 0)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Adding one element
        hstack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        code = hstack.pop(pop_ids=('elt1',))
        self.assertEqual(code, 1)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Try to push a None element
        res = hstack._push(None)
        self.assertEqual(res, -1)

    def test_NoMaxSizeWithLevels(self):

        #
        # Now this tests test the levels
        #

        # Test Base Stack with no initialization
        hstack = HierarchicalStack()

        self.assertEqual(hstack.getSize(level=-1), 0)
        self.assertEqual(hstack.getSize(level=0), 0)
        self.assertEqual(hstack.getSize(level=1), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 1)
        self.assertEqual(hstack.isEmpty(level=0), 1)
        self.assertEqual(hstack.isEmpty(level=1), 1)

        self.assertEqual(hstack.isFull(level=-1), 0)
        self.assertEqual(hstack.isFull(level=0), 0)
        self.assertEqual(hstack.isFull(level=1), 0)


        # Adding one element at level 0
        hstack.push('elt1', level=0)

        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.getSize(level=0), 1)

        self.assertEqual(hstack.getSize(level=1), 0)
        self.assertEqual(hstack.getSize(level=-1), 0)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 1)
        self.assertEqual(hstack.isEmpty(level=1), 1)

        self.assertEqual(hstack.isFull(), 0)
        self.assertEqual(hstack.isFull(level=0), 0)

        self.assertEqual(hstack.isFull(level=-1), 0)
        self.assertEqual(hstack.isFull(level=1), 0)

        # Adding one element at level -1
        hstack.push('elt-1', level=-1)

        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.getSize(level=0), 1)

        self.assertEqual(hstack.getSize(level=1), 0)
        self.assertEqual(hstack.getSize(level=-1), 1)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 1)

        self.assertEqual(hstack.isFull(), 0)
        self.assertEqual(hstack.isFull(level=0), 0)

        self.assertEqual(hstack.isFull(level=-1), 0)
        self.assertEqual(hstack.isFull(level=1), 0)

        # Adding one element at level 1
        hstack.push('elt11', level=1)

        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.getSize(level=0), 1)

        self.assertEqual(hstack.getSize(level=1), 1)
        self.assertEqual(hstack.getSize(level=-1), 1)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        self.assertEqual(hstack.isFull(), 0)
        self.assertEqual(hstack.isFull(level=0), 0)

        self.assertEqual(hstack.isFull(level=-1), 0)
        self.assertEqual(hstack.isFull(level=1), 0)

        # Adding same element at each level  (Not allowed with this stack)

        # Level 0
        res = hstack.push('elt1', level=0)
        self.assertEqual(res, -2)

        res = hstack.push('elt-1', level=0)
        self.assertEqual(res, 1)

        res = hstack.push('elt11', level=0)
        self.assertEqual(res, 1)

        # Level -1
        res = hstack.push('elt-1', level=-1)
        self.assertEqual(res, -2)

        res = hstack.push('elt1', level=-1)
        self.assertEqual(res, 1)

        res = hstack.push('elt11', level=-1)
        self.assertEqual(res, 1)

        # Level 1
        res = hstack.push('elt11', level=1)
        self.assertEqual(res, -2)

        res = hstack.push('elt-1', level=1)
        self.assertEqual(res, 1)

        res = hstack.push('elt1', level=1)
        self.assertEqual(res, 1)

        self.assertEqual(hstack.getSize(), 3)
        self.assertEqual(hstack.getSize(level=0), 3)
        self.assertEqual(hstack.getSize(level=-1), 3)
        self.assertEqual(hstack.getSize(level=1), 3)

        # Check level 0 (current level)
        self.assertEqual(hstack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=-1, context=self),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=1, context=self),
                         ['elt11','elt-1','elt1'])

        # Dec Level
        clevel = hstack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Check the level content
        self.assertEqual(hstack.getLevelContent(context=self),
                         hstack.getLevelContent(
            level=hstack.getCurrentLevel(), context=self))
        self.assertEqual(hstack.getLevelContent(context=self),
                         hstack.getLevelContent(level=-1, context=self))
        self.assertEqual(hstack.getLevelContent(context=self),
                         ['elt-1','elt1','elt11'])

        # Check the consistency of the rest
        self.assertEqual(hstack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=-1, context=self),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=1, context=self),
                         ['elt11','elt-1','elt1'])

        # Increment now
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        self.assertEqual(hstack.getLevelContent(context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=0, context=self),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=-1, context=self),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=1, context=self),
                         ['elt11','elt-1','elt1'])

        # Increment again
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Check the level content
        self.assertEqual(hstack.getLevelContent(context=self),
                         hstack.getLevelContent(level=hstack.getCurrentLevel(),
                                                context=self))
        self.assertEqual(hstack.getLevelContent(context=self),
                         hstack.getLevelContent(level=1, context=self))
        self.assertEqual(hstack.getLevelContent(context=self),
                         ['elt11','elt-1','elt1'])

        # Check levels
        self.assertEqual(hstack.getAllLevels(), [-1, 0, 1])

        # Let's test the remove / pop API

        # Pop element at current level (1)
        self.assertEqual(hstack.getCurrentLevel(), 1)
        self.assertEqual(hstack.pop(pop_ids=('elt1',)), 1)

        # Let's check the consistency of the rest
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=0), 3)

        self.assertEqual(hstack.getSize(level=1), 2)
        self.assertEqual(hstack.getSize(level=-1), 3)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        # Pop element at level 0
        # not found
        self.assertEqual(hstack.getCurrentLevel(), 1)
        self.assertEqual(hstack.pop(pop_ids=['fake'],level=0), 0)

        # Let's check the consistency of the rest
        self.assertEqual(hstack.getSize(level=0), 3)

        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=1), 2)
        self.assertEqual(hstack.getSize(level=-1), 3)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        # Pop element at level -1
        self.assertEqual(hstack.getCurrentLevel(), 1)
        self.assertEqual(hstack.pop(pop_ids=('elt11',),level=-1), 1)

        # Let's check the consistency of the rest
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=0), 3)

        self.assertEqual(hstack.getSize(level=1), 2)
        self.assertEqual(hstack.getSize(level=-1), 2)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        # Let's change level
        clevel = hstack.doDecLevel()
        self.assertEqual(clevel, hstack.getCurrentLevel())
        self.assertEqual(clevel, 0)

        # Let's check the consistency of the rest
        self.assertEqual(hstack.getSize(), 3)
        self.assertEqual(hstack.getSize(level=0), 3)

        self.assertEqual(hstack.getSize(level=1), 2)
        self.assertEqual(hstack.getSize(level=-1), 2)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        # Check now the pop
        self.assertEqual(hstack.pop(pop_ids=('XXX',)), 0)
        self.assertEqual(hstack.pop(pop_ids=('elt1',), level=89), 0)
        self.assertEqual(hstack.pop(pop_ids=('elt1',),), 1)
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=hstack.getCurrentLevel()), 2)
        self.assertEqual(hstack.getSize(level=0), 2)
        self.assertEqual(hstack.pop(pop_ids=('elt1',)), 0)
        self.assertEqual(hstack.pop(pop_ids=('elt-1', 'elt11')), 1)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)

        # Check levels
        self.assertEqual(hstack.getAllLevels(), [-1, 1])
        clevel = hstack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Not possible to go back to level 0 (empty)
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Add an elemet to level 0
        self.assertEqual(hstack.push(elt='elt1', level=0), 1)

        # Now possible to go back to level 0
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Let's empty evrything
        clevel = hstack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, hstack.getCurrentLevel())
        self.assertEqual(hstack.pop(pop_ids=('elt1', 'elt-1')), 1)

        # Empty now (-1)
        self.assertEqual(hstack.isEmpty(), 1)

        # Go back to 0
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Trying to go back to -1
        clevel = hstack.doDecLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, hstack.getCurrentLevel())
        # ... now way... let's pop the level 0

        self.assertEqual(hstack.pop(pop_ids=['elt1']), 1)
        # Empty now (0)
        self.assertEqual(hstack.isEmpty(), 1)

        # Go to 1
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        self.assertEqual(hstack.pop(pop_ids=('elt-1', 'elt11')), 1)
        # Empty now (1)
        self.assertEqual(hstack.isEmpty(), 1)

        # Check the status of the stack now
        self.assertEqual(hstack.getAllLevels(), [])
        self.assertEqual(hstack.getLevelContent(context=self), [])
        self.assertEqual(hstack.getLevelContent(level=-1, context=self), [])
        self.assertEqual(hstack.getLevelContent(level=0, context=self), [])
        self.assertEqual(hstack.getLevelContent(level=1, context=self), [])

        # Check wiered stuffs
        self.assertEqual(hstack.getLevelContent(level=90000, context=self), [])
        self.assertEqual(hstack.pop(pop_ids=('wiered',), level=90000), 0)

    def test_WithMaxSize(self):

        #
        # This tests are all done at level 0 implicitly
        # They are the same as the one on the SimpleStack
        # The idea is to show it's possible to use the hierarchical stack
        # as a simple stack without having to care of the current level
        # It's just a validation of the implementation
        #

        # Test Base Stack with no initialization
        hstack = HierarchicalStack(maxsize=2)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Adding one element
        hstack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = hstack.push('elt1')
        self.assertEqual(res, -2)
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1']})

        # Adding another element.
        res = hstack.push('elt2')
        self.assertEqual(res, 1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1','elt2']})

        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 1)

        # Pop now
        code = hstack.pop(pop_ids=['elt2'])
        self.assertEqual(code, 1)
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        code = hstack.pop(pop_ids=['elt1'])
        self.assertEqual(code, 1)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        code = hstack.pop(pop_ids=['fake'])
        self.assertEqual(code, 0)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Adding one element
        hstack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        code = hstack.pop(pop_ids=['elt1'])
        self.assertEqual(code, 1)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Try to push a None element
        res = hstack.push(None)
        self.assertEqual(res, -1)

        hstack = HierarchicalStack()

        # Test the pop() method
        self.assertEqual(hstack.getStackContent(context=self), {})
        self.assertEqual(hstack.pop(pop_ids=['elt1']), 0)
        hstack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual(hstack.pop(pop_ids=['elt1']), 1)
        hstack.push(push_ids=['elt1'], levels=[0])
        hstack.push(push_ids=['elt2'], levels=[0])
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1', 'elt2']})
        hstack.push(push_ids=['elt3'], levels=[0])
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1', 'elt2', 'elt3']})
        self.assertEqual(hstack.pop(pop_ids=['elt2']), 1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1', 'elt3']})

        hstack.pop(pop_ids=['0,elt3'])
        hstack.pop(pop_ids=['0,elt1'])
        self.assertEqual(hstack.getStackContent(context=self), {})

    def test_getCopy(self):

        #
        # Test getCopy()
        # Goal is to prove the copy is not same object
        #

        hstack1 = HierarchicalStack()
        self.assertEqual(hstack1.meta_type, 'Hierarchical Stack')
        hstack2 = hstack1.getCopy()
        self.assertEqual(hstack2.meta_type, 'Hierarchical Stack')

        self.assertNotEqual(hstack2, None)
        self.assertNotEqual(hstack1, hstack2)

        self.assertEqual(hstack1.getStackContent(context=self), {})
        self.assertEqual(hstack2.getStackContent(context=self), {})

        self.assertEqual(hstack1.getStackContent(context=self),
                         hstack2.getStackContent(context=self))
        self.assertEqual(hstack1.isFull(), hstack2.isFull())
        self.assertEqual(hstack1.isEmpty(), hstack2.isEmpty())
        self.assertEqual(hstack1.getSize(), hstack2.getSize())

        hstack1.push('elt1')
        hstack2.push('elt2')
        self.assertEqual(hstack1.getLevelContent(context=self), ['elt1'])
        self.assertEqual(hstack2.getLevelContent(context=self), ['elt2'])

        self.assertNotEqual(hstack1.getStackContent(context=self),
                            hstack2.getStackContent(context=self))

    def test_push(self):
        hstack = HierarchicalStack()

        # Add a user
        hstack.push(push_ids=['elt1'], levels=[0])
        elt = hstack._getStackContent()[0][0]
        self.assert_(isinstance(elt, UserStackElement))
        self.assert_(elt == 'elt1')

        # Add a group
        hstack.push(push_ids=['group:elt2'], levels=[0])
        elt2 = hstack._getStackContent()[0][1]
        self.assert_(isinstance(elt2, GroupStackElement))
        self.assert_(elt2 == 'group:elt2')

    def test_level_api(self):
        hstack = HierarchicalStack()

        # no upper nor lower level here.
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Add someone at level 0
        hstack.push(push_ids=['base'], levels=[0])
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Add someone at level 1
        hstack.push(push_ids=['elt1'], levels=[1])
        self.assert_(hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Add someone at level -1
        hstack.push(push_ids=['elt2'], levels=[-1])
        self.assert_(hstack.hasUpperLevel())
        self.assert_(hstack.hasLowerLevel())

        # Dec level
        hstack.doDecLevel()
        self.assertEqual(hstack.getCurrentLevel(), -1)
        self.assert_(hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Inc level
        hstack.doIncLevel()
        self.assertEqual(hstack.getCurrentLevel(), 0)
        self.assert_(hstack.hasUpperLevel())
        self.assert_(hstack.hasLowerLevel())

        # Inc level
        hstack.doIncLevel()
        self.assertEqual(hstack.getCurrentLevel(), 1)
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(hstack.hasLowerLevel())

        # Dec level
        hstack.doDecLevel()
        self.assert_(hstack.getCurrentLevel() == 0)

        # Remove elt2 at level -1
        hstack.pop(pop_ids=['-1,elt2'])
        self.assert_(hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Remove elt1 at level 1
        hstack.pop(pop_ids=['1,elt1'])
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

    def test_getManagers(self):
        stack = HierarchicalStack()
        stack.push(push_ids=['user:elt1', 'group:elt2'], levels=[0, 1])
        # current level is 0
        managers = [
            UserStackElement('user:elt1'),
            ]
        self.assertEqual(stack._getManagers(), managers)

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

        #
        # Test the reset behavior on the Stack class type
        #

        stack = HierarchicalStack()
        stack.push(push_ids=['elt1'], levels=[0])
        self.assertEqual([x.getId() for x in stack._getStackContent()[0]],
                         ['elt1'])

        # Reset with one (1) new user
        stack.reset(reset_ids=('elt2',))
        self.assertEqual([x.getId() for x in stack._getStackContent()[0]],
                         ['elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('elt3', 'elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()[0]],
                         ['elt3', 'elt4'])

        # Reset with one (1) new group
        stack.reset(reset_ids=('group:elt2',))
        self.assertEqual([x.getId() for x in stack._getStackContent()[0]],
                         ['group:elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()[0]],
                         ['group:elt3', 'group:elt4'])

        # Reset with one new stack
        new_stack = HierarchicalStack()
        new_stack.push('new_elt')
        stack.reset(new_stack=new_stack)
        self.assertEqual(stack._getStackContent(),
                         new_stack._getStackContent())

        # Reset with a new stack, new users and new groups
        new_stack = HierarchicalStack()
        stack.reset(new_stack=new_stack,
                   reset_ids=('elt1', 'elt2', 'group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getStackContent()[0]],
                         ['elt1', 'elt2', 'group:elt3', 'group:elt4'])


    def test_replace(self):

        #
        # Test with strings
        #

        stack = HierarchicalStack()
        stack.push(push_ids=['elt1'], levels=[0])
        stack.push(push_ids=['elt2'], levels=[0])
        self.assertEqual(stack.getLevelContent(context=self), ['elt1', 'elt2'])
        stack.replace('elt2', 'elt4')
        self.assertEqual(stack.getLevelContent(context=self), ['elt1', 'elt4'])

        #
        # Test with elements objects
        #

        oelt = UserStackElement('string_elt')
        stack.replace('elt4', oelt)
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt1', 'string_elt'])

        #
        # Test with different levels
        #

        stack.push('string_elt', level=1)
        stack.push('string_elt', level=-1)
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt1', 'string_elt'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['string_elt'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['string_elt'])

        stack.push('elt1', level=1)
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt1', 'string_elt'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['string_elt', 'elt1'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['string_elt'])

        stack.replace('string_elt', 'string_elt2')
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt1', 'string_elt2'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['string_elt2', 'elt1'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['string_elt2'])

        stack.replace('elt1', 'elt2')
        self.assertEqual(stack.getLevelContent(context=self),
                         ['elt2', 'string_elt2'])
        self.assertEqual(stack.getLevelContent(level=1, context=self),
                         ['string_elt2', 'elt2'])
        self.assertEqual(stack.getLevelContent(level=-1, context=self),
                         ['string_elt2'])

    def test_insertInBetweenLevels(self):

        hstack = HierarchicalStack()
        self.assertEqual(hstack.getStackContent(), {})

        # Normal
        hstack.push(push_ids=['elt1'], levels=[0])
        hstack.push(push_ids=['elt3'], levels=[1])
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1'], 1:['elt3']})

        # Insert in between 0 and 1
        # current_level is 0
        self.assertEqual(hstack.getCurrentLevel(), 0)
        hstack.push('elt2', low_level=0, high_level=1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1'],
                          1:['elt2'],
                          2:['elt3'],
                          })
        # Change current level and try to insert
        # 0 is the edge level where we need to test
        hstack.doIncLevel()
        self.assertEqual(hstack.getCurrentLevel(), 1)
        hstack.push('elt4', low_level=0, high_level=1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          })
        hstack.push('elt5', low_level=2, high_level=3)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        hstack.push('elt6', low_level=-2, high_level=-1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        hstack.push('elt7', low_level=-4, high_level=-3)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        hstack.push('elt7', low_level=4, high_level=5)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStack))
    suite.addTest(unittest.makeSuite(TestSimpleStack))
    suite.addTest(unittest.makeSuite(TestHierarchicalStack))
    return suite

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
