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
from Testing.ZopeTestCase import ZopeTestCase
from Interface.Verify import verifyClass

from Products.CPSWorkflow.stack import Stack
from Products.CPSWorkflow.basicstacks import SimpleStack
from Products.CPSWorkflow.basicstacks import HierarchicalStack

from Products.CPSWorkflow.basicstackelements import UserStackElement
from Products.CPSWorkflow.basicstackelements import GroupStackElement

from Products.CPSWorkflow.interfaces import IWorkflowStack
from Products.CPSWorkflow.interfaces import ISimpleWorkflowStack
from Products.CPSWorkflow.interfaces import IHierarchicalWorkflowStack

class TestCPSWorkflowStacks(ZopeTestCase):

    def test_interface(self):

        verifyClass(IWorkflowStack, Stack)
        verifyClass(IWorkflowStack, SimpleStack)
        verifyClass(IWorkflowStack, HierarchicalStack)

        verifyClass(ISimpleWorkflowStack, SimpleStack)
        verifyClass(IHierarchicalWorkflowStack, HierarchicalStack)
        verifyClass(ISimpleWorkflowStack, HierarchicalStack)

    def test_SimpleStackNoMaxSize(self):

        # Test Base Stack with no initialization
        sstack = SimpleStack()
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push('elt1')
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = sstack.push('elt1')
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Adding another element. (Allowed with this stack)
        sstack.push('elt2')
        self.assertEqual(sstack.getSize(), 2)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop now
        elt = sstack.pop()
        self.assertEqual(elt, 1)
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        elt = sstack.pop()
        self.assertEqual(elt, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        elt = sstack.pop()
        self.assertEqual(elt, 0)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push('elt1')
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        elt = sstack.pop()
        self.assertEqual(elt, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Try to push a None element
        res = sstack.push(None)
        self.assertEqual(res, -1)

    def test_SimpleStackWithMaxSize(self):

        # Test Base Stack with no initialization
        sstack = SimpleStack(maxsize=2)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push('elt1')
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = sstack.push('elt1')
        self.assertEqual(res, -2)
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        self.assertEqual(sstack.getStackContent(), ['elt1'])

        # Adding another element.
        res = sstack.push('elt2')
        self.assertEqual(res, 1)

        self.assertEqual(sstack.getStackContent(), ['elt1','elt2'])

        self.assertEqual(sstack.getSize(), 2)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 1)

        # Pop now
        elt = sstack.pop()
        self.assertEqual(elt, 1)
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        elt = sstack.pop()
        self.assertEqual(elt, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        elt = sstack.pop()
        self.assertEqual(elt, 0)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Adding one element
        sstack.push('elt1')
        self.assertEqual(sstack.getSize(), 1)
        self.assertEqual(sstack.isEmpty(), 0)
        self.assertEqual(sstack.isFull(), 0)

        # Pop again
        elt = sstack.pop()
        self.assertEqual(elt, 1)
        self.assertEqual(sstack.getSize(), 0)
        self.assertEqual(sstack.isEmpty(), 1)
        self.assertEqual(sstack.isFull(), 0)

        # Try to push a None element
        res = sstack.push(None)
        self.assertEqual(res, -1)

        sstack = SimpleStack()

        # Test the pop() method
        self.assertEqual(sstack.getStackContent(), [])
        self.assertEqual(sstack.pop('elt1'), 0)
        sstack.push('elt1')
        self.assertEqual(sstack.pop('elt1'), 1)
        sstack.push('elt1')
        sstack.push('elt2')
        self.assertEqual(sstack.getStackContent(), ['elt1', 'elt2'])
        sstack.push('elt3')
        self.assertEqual(sstack.getStackContent(), ['elt1', 'elt2', 'elt3'])
        self.assertEqual(sstack.pop('elt2'), 1)
        self.assertEqual(sstack.getStackContent(), ['elt1', 'elt3'])

        sstack.pop('elt3')
        sstack.pop('elt1')
        self.assertEqual(sstack.getStackContent(), [])

    def test_simpleHierarchicalStackNoMaxSize(self):

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
        hstack.push('elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = hstack.push('elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Adding another element. (Allowed with this stack)
        hstack.push('elt2')
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop now
        elt = hstack.pop()
        self.assertEqual(elt(), 'elt2')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        elt = hstack.pop()
        self.assertEqual(elt(), 'elt1')
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        elt = hstack.pop()
        self.assertEqual(elt, 0)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Adding one element
        hstack.push('elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        elt = hstack.pop()
        self.assertEqual(elt(), 'elt1')
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Try to push a None element
        res = hstack.push(None)
        self.assertEqual(res, -1)

    def test_HierarchicalStackNoMaxSizeWithLevels(self):

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
        self.assertEqual(hstack.getLevelContent(level=0),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=0),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=-1),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=1),
                         ['elt11','elt-1','elt1'])

        # Dec Level
        clevel = hstack.doDecLevel()
        self.assertEqual(clevel, -1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Check the level content
        self.assertEqual(hstack.getLevelContent(),
                         hstack.getLevelContent(
            level=hstack.getCurrentLevel()))
        self.assertEqual(hstack.getLevelContent(),
                         hstack.getLevelContent(level=-1))
        self.assertEqual(hstack.getLevelContent(),
                         ['elt-1','elt1','elt11'])

        # Check the consistency of the rest
        self.assertEqual(hstack.getLevelContent(level=0),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=-1),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=1),
                         ['elt11','elt-1','elt1'])

        # Increment now
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 0)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        self.assertEqual(hstack.getLevelContent(),
                         ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=0), ['elt1','elt-1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=-1),
                         ['elt-1','elt1','elt11'])
        self.assertEqual(hstack.getLevelContent(level=1),
                         ['elt11','elt-1','elt1'])

        # Increment again
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        # Check the level content
        self.assertEqual(hstack.getLevelContent(),
                         hstack.getLevelContent(level=hstack.getCurrentLevel()))
        self.assertEqual(hstack.getLevelContent(),
                         hstack.getLevelContent(level=1))
        self.assertEqual(hstack.getLevelContent(),
                         ['elt11','elt-1','elt1'])

        # Check levels
        self.assertEqual(hstack.getAllLevels(), [-1, 0, 1])

        # Let's test the remove / pop API

        # Pop element at current level (1)
        self.assertEqual(hstack.getCurrentLevel(), 1)
        self.assertEqual(hstack.pop()(), 'elt1')

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
        self.assertEqual(hstack.pop(level=0), 1)

        # Let's check the consistency of the rest
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=0), 2)

        self.assertEqual(hstack.getSize(level=1), 2)
        self.assertEqual(hstack.getSize(level=-1), 3)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        # Pop element at level -1
        self.assertEqual(hstack.getCurrentLevel(), 1)
        self.assertEqual(hstack.pop(level=-1)(), 'elt11')

        # Let's check the consistency of the rest
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=0), 2)

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
        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.getSize(level=0), 2)

        self.assertEqual(hstack.getSize(level=1), 2)
        self.assertEqual(hstack.getSize(level=-1), 2)

        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isEmpty(level=0), 0)

        self.assertEqual(hstack.isEmpty(level=-1), 0)
        self.assertEqual(hstack.isEmpty(level=1), 0)

        # Check now the pop
        self.assertEqual(hstack.pop(elt='XXX'), -1)
        self.assertEqual(hstack.pop(level=89), 0)
        self.assertEqual(hstack.pop(elt='elt1', level=89), -1)
        self.assertEqual(hstack.pop(elt='elt1',)(), 'elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.getSize(level=hstack.getCurrentLevel()), 1)
        self.assertEqual(hstack.getSize(level=0), 1)
        self.assertEqual(hstack.pop(elt='elt1'), -1)
        self.assertEqual(hstack.pop(elt='elt-1')(), 'elt-1')
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
        self.assertEqual(hstack.pop()(), 'elt1')
        self.assertEqual(hstack.pop()(), 'elt-1')

        # Empty now (-1)
        self.assertEqual(hstack.pop(), 0)
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

        self.assertEqual(hstack.pop()(), 'elt1')
        # Empty now (0)
        self.assertEqual(hstack.pop(), 0)
        self.assertEqual(hstack.isEmpty(), 1)

        # Go to 1
        clevel = hstack.doIncLevel()
        self.assertEqual(clevel, 1)
        self.assertEqual(clevel, hstack.getCurrentLevel())

        self.assertEqual(hstack.pop()(), 'elt-1')
        self.assertEqual(hstack.pop()(), 'elt11')
        # Empty now (1)
        self.assertEqual(hstack.pop(), 0)
        self.assertEqual(hstack.isEmpty(), 1)

        # Check the status of the stack now
        self.assertEqual(hstack.getAllLevels(), [])
        self.assertEqual(hstack.getLevelContent(), [])
        self.assertEqual(hstack.getLevelContent(level=-1), [])
        self.assertEqual(hstack.getLevelContent(level=0), [])
        self.assertEqual(hstack.getLevelContent(level=1), [])

        # Check wiered stuffs
        self.assertEqual(hstack.getLevelContent(level=90000), [])
        self.assertEqual(hstack.pop(level=90000), 0)

    def test_simpleHierarchicalStackWithMaxSize(self):

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
        hstack.push('elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Adding same element. (Not allowed with this stack)
        res = hstack.push('elt1')
        self.assertEqual(res, -2)
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        self.assertEqual(hstack.getStackContent(),
                         {0:['elt1']})

        # Adding another element.
        res = hstack.push('elt2')
        self.assertEqual(res, 1)

        self.assertEqual(hstack.getStackContent(), {0:['elt1','elt2']})

        self.assertEqual(hstack.getSize(), 2)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 1)

        # Pop now
        elt = hstack.pop()
        self.assertEqual(elt(), 'elt2')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        elt = hstack.pop()
        self.assertEqual(elt(), 'elt1')
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        elt = hstack.pop()
        self.assertEqual(elt, 0)
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Adding one element
        hstack.push('elt1')
        self.assertEqual(hstack.getSize(), 1)
        self.assertEqual(hstack.isEmpty(), 0)
        self.assertEqual(hstack.isFull(), 0)

        # Pop again
        elt = hstack.pop()
        self.assertEqual(elt(), 'elt1')
        self.assertEqual(hstack.getSize(), 0)
        self.assertEqual(hstack.isEmpty(), 1)
        self.assertEqual(hstack.isFull(), 0)

        # Try to push a None element
        res = hstack.push(None)
        self.assertEqual(res, -1)

        hstack = HierarchicalStack()

        # Test the pop() method
        self.assertEqual(hstack.getStackContent(), {})
        self.assertEqual(hstack.pop('elt1'), -1)
        hstack.push('elt1')
        self.assertEqual(hstack.pop('elt1')(), 'elt1')
        hstack.push('elt1')
        hstack.push('elt2')
        self.assertEqual(hstack.getStackContent(),
                         {0:['elt1', 'elt2']})
        hstack.push('elt3')
        self.assertEqual(hstack.getStackContent(),
                         {0:['elt1', 'elt2', 'elt3']})
        self.assertEqual(hstack.pop('elt2')(), 'elt2')
        self.assertEqual(hstack.getStackContent(),
                         {0:['elt1', 'elt3']})

        hstack.pop('elt3')
        hstack.pop('elt1')
        self.assertEqual(hstack.getStackContent(), {})

    def test_SimpleStackCopy(self):
        # Test getCopy()

        sstack1 = SimpleStack()
        self.assertEqual(sstack1.meta_type, 'Simple Stack')
        sstack2 = sstack1.getCopy()
        self.assertEqual(sstack2.meta_type, 'Simple Stack')

        self.assertNotEqual(sstack2, None)
        self.assertNotEqual(sstack1, sstack2)

        self.assertEqual(sstack1.getStackContent(), [])
        self.assertEqual(sstack2.getStackContent(), [])

        self.assertEqual(sstack1.getStackContent(), sstack2.getStackContent())
        self.assertEqual(sstack1.isFull(), sstack2.isFull())
        self.assertEqual(sstack1.isEmpty(), sstack2.isEmpty())
        self.assertEqual(sstack1.getSize(), sstack2.getSize())

        sstack1.push('elt1')
        sstack2.push('elt2')
        self.assertEqual(sstack1.getStackContent(), ['elt1'])
        self.assertEqual(sstack2.getStackContent(), ['elt2'])

        self.assertNotEqual(sstack1.getStackContent(),
                            sstack2.getStackContent())

    def test_HierarchicalStackCopy(self):

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

        self.assertEqual(hstack1.getStackContent(), {})
        self.assertEqual(hstack2.getStackContent(), {})

        self.assertEqual(hstack1.getStackContent(), hstack2.getStackContent())
        self.assertEqual(hstack1.isFull(), hstack2.isFull())
        self.assertEqual(hstack1.isEmpty(), hstack2.isEmpty())
        self.assertEqual(hstack1.getSize(), hstack2.getSize())

        hstack1.push('elt1')
        hstack2.push('elt2')
        self.assertEqual(hstack1.getLevelContent(), ['elt1'])
        self.assertEqual(hstack2.getLevelContent(), ['elt2'])

        self.assertNotEqual(hstack1.getStackContent(),
                            hstack2.getStackContent())

    def test_reset_simple_wf_stack(self):

        #
        # Test the reset API
        #

        simple = SimpleStack()
        self.assertEqual(simple.getMetaType(),
                         'Simple Stack')
        simple.push('elt1')
        self.assertEqual(simple.getStackContent(),
                         ['elt1'])
        simple.reset()
        self.assertEqual(simple.getMetaType(),
                         'Simple Stack')
        self.assertNotEqual(simple.getStackContent(),
                            ['elt1'])
        self.assertEqual(simple.getStackContent(),
                         [])

        simple.push('elt1')
        self.assertEqual(simple.getStackContent(),
                         ['elt1'])

    def test_reset_hierarchical_wf_stack(self):

        #
        # Test the reset API
        #

        hierarchical = HierarchicalStack()
        self.assertEqual(hierarchical.getMetaType(),
                         'Hierarchical Stack')
        self.assertEqual(hierarchical.getStackContent(),
                         {})
        hierarchical.push('elt1')
        self.assertNotEqual(hierarchical.getStackContent(),
                            {})
        self.assertEqual(hierarchical.getLevelContent(),
                         ['elt1'])
        hierarchical.reset()
        self.assertEqual(hierarchical.getStackContent(),
                         {})
        self.assertEqual(hierarchical.getMetaType(),
                         'Hierarchical Stack')
        self.assertNotEqual(hierarchical.getLevelContent(),
                            ['elt1'])
        self.assertEqual(hierarchical.getLevelContent(),
                         [])

        hierarchical.push('elt1')
        self.assertEqual(hierarchical.getLevelContent(),
                         ['elt1'])

    #def test_bstack_elements(self):
    #    bstack = Stack()
    #
    #    # Add a user
    #    bstack.push('elt1')
    #    elt = bstack._getElementsContainer()[0]
    #    self.assert_(isinstance(elt, UserStackElement))
    #    self.assert_(elt == 'elt1')
    #
    #    # Add a group
    #    bstack.push('group:elt2')
    #    elt2 = bstack._getElementsContainer()[1]
    #    self.assert_(isinstance(elt2, GroupStackElement))
    #    self.assert_(elt2 == 'group:elt2')
    #
    #    # Remove the group
    #    bstack.pop()
    #    elt = bstack._getElementsContainer()[0]
    #    self.assert_(isinstance(elt, UserStackElement))
    #    self.assert_(elt == 'elt1')
    #
    #    bstack.pop()

    def test_sstack_elements(self):
        sstack = SimpleStack()

        # Add a user
        sstack.push('elt1')
        elt = sstack._getElementsContainer()[0]
        self.assert_(isinstance(elt, UserStackElement))
        self.assert_(elt == 'elt1')

        # Add a group
        sstack.push('group:elt2')
        elt2 = sstack._getElementsContainer()[1]
        self.assert_(isinstance(elt2, GroupStackElement))
        self.assert_(elt2 == 'group:elt2')

    def test_hstack_elements(self):
        hstack = HierarchicalStack()

        # Add a user
        hstack.push('elt1')
        elt = hstack._getElementsContainer()[0][0]
        self.assert_(isinstance(elt, UserStackElement))
        self.assert_(elt == 'elt1')

        # Add a group
        hstack.push('group:elt2')
        elt2 = hstack._getElementsContainer()[0][1]
        self.assert_(isinstance(elt2, GroupStackElement))
        self.assert_(elt2 == 'group:elt2')

    def test_level_api_for_hierarchical(self):
        hstack = HierarchicalStack()

        # no upper nor lower level here.
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Add someone at level 0
        hstack.push('base', level=0)
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Add someone at level 1
        hstack.push('elt1', level=1)
        self.assert_(hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Add someone at level -1
        hstack.push('elt2', level=-1)
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
        hstack.pop('elt2', level=-1)
        self.assert_(hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

        # Remove elt1 at level 1
        hstack.pop('elt1', level=1)
        self.assert_(not hstack.hasUpperLevel())
        self.assert_(not hstack.hasLowerLevel())

    #def test_ResetOnStack(self):
    #
    #    #
    #    # Test the reset behavior on the Stack class type
    #    #
    #
    #    stack = Stack()
    #    stack.push('elt1')
    #    self.assertEqual([x() for x in stack._getElementsContainer()],
    #                     ['elt1'])
    #
    #    # Reset with one (1) new user
    #    stack.reset(new_users=('elt2',))
    #    self.assertEqual([x() for x in stack._getElementsContainer()],
    #                     ['elt2'])
    #
    #    # Reset with two (2) new users
    #    stack.reset(new_users=('elt3', 'elt4'))
    #    self.assertEqual([x() for x in stack._getElementsContainer()],
    #                     ['elt3', 'elt4'])
    #
    #    # Reset with one (1) new group
    #    stack.reset(new_users=('group:elt2',))
    #    self.assertEqual([x() for x in stack._getElementsContainer()],
    #                     ['group:elt2'])
    #
    #    # Reset with two (2) new users
    #    stack.reset(new_users=('group:elt3', 'group:elt4'))
    #    self.assertEqual([x() for x in stack._getElementsContainer()],
    #                     ['group:elt3', 'group:elt4'])
    #
    #    # Reset with one new stack
    #    new_stack = Stack()
    #    new_stack.push('new_elt')
    #    stack.reset(new_stack=new_stack)
    #    self.assertEqual(stack._getElementsContainer(),
    #                     new_stack._getElementsContainer())
    #
    #    # Reset with a new stack, new users and new groups
    #    new_stack = Stack()
    #    stack.reset(new_stack=new_stack,
    #               new_users=('elt1', 'elt2'),
    #               new_groups=('group:elt3', 'group:elt4'))
    #    self.assertEqual([x() for x in stack._getElementsContainer()],
    #                     ['elt1', 'elt2', 'group:elt3', 'group:elt4'])

    def test_ResetOnSimpleStack(self):

        #
        # Test the reset behavior on the Stack class type
        #

        stack = SimpleStack()
        stack.push('elt1')
        self.assertEqual([x() for x in stack._getElementsContainer()],
                         ['elt1'])

        # Reset with one (1) new user
        stack.reset(reset_ids=('elt2',))
        self.assertEqual([x() for x in stack._getElementsContainer()],
                         ['elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('elt3', 'elt4'))
        self.assertEqual([x() for x in stack._getElementsContainer()],
                         ['elt3', 'elt4'])

        # Reset with one (1) new group
        stack.reset(reset_ids=('group:elt2',))
        self.assertEqual([x() for x in stack._getElementsContainer()],
                         ['group:elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('group:elt3', 'group:elt4'))
        self.assertEqual([x() for x in stack._getElementsContainer()],
                         ['group:elt3', 'group:elt4'])

        # Reset with one new stack
        new_stack = SimpleStack()
        new_stack.push('new_elt')
        stack.reset(new_stack=new_stack)
        self.assertEqual(stack._getElementsContainer(),
                         new_stack._getElementsContainer())

        # Reset with a new stack, new users and new groups
        new_stack = SimpleStack()
        stack.reset(new_stack=new_stack,
                   reset_ids=('elt1', 'elt2', 'group:elt3', 'group:elt4'))
        self.assertEqual([x() for x in stack._getElementsContainer()],
                         ['elt1', 'elt2', 'group:elt3', 'group:elt4'])


    def test_ResetOnHierarchicalStack(self):

        #
        # Test the reset behavior on the Stack class type
        #

        stack = HierarchicalStack()
        stack.push('elt1')
        self.assertEqual([x() for x in stack._getElementsContainer()[0]],
                         ['elt1'])

        # Reset with one (1) new user
        stack.reset(reset_ids=('elt2',))
        self.assertEqual([x() for x in stack._getElementsContainer()[0]],
                         ['elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('elt3', 'elt4'))
        self.assertEqual([x() for x in stack._getElementsContainer()[0]],
                         ['elt3', 'elt4'])

        # Reset with one (1) new group
        stack.reset(reset_ids=('group:elt2',))
        self.assertEqual([x() for x in stack._getElementsContainer()[0]],
                         ['group:elt2'])

        # Reset with two (2) new users
        stack.reset(reset_ids=('group:elt3', 'group:elt4'))
        self.assertEqual([x() for x in stack._getElementsContainer()[0]],
                         ['group:elt3', 'group:elt4'])

        # Reset with one new stack
        new_stack = HierarchicalStack()
        new_stack.push('new_elt')
        stack.reset(new_stack=new_stack)
        self.assertEqual(stack._getElementsContainer(),
                         new_stack._getElementsContainer())

        # Reset with a new stack, new users and new groups
        new_stack = HierarchicalStack()
        stack.reset(new_stack=new_stack,
                   reset_ids=('elt1', 'elt2', 'group:elt3', 'group:elt4'))
        self.assertEqual([x() for x in stack._getElementsContainer()[0]],
                         ['elt1', 'elt2', 'group:elt3', 'group:elt4'])

    def test_replaceOnSimpleStack(self):

        #
        # Test with strings
        #

        stack = SimpleStack()
        stack.push('elt1')
        stack.push('elt2')
        self.assertEqual(stack.getStackContent(), ['elt1', 'elt2'])
        stack.replace('elt2', 'elt4')
        self.assertEqual(stack.getStackContent(), ['elt1', 'elt4'])

        #
        # Test with elements objects
        #

        oelt = UserStackElement('string_elt')
        stack.replace('elt4', oelt)
        self.assertEqual(stack.getStackContent(), ['elt1', 'string_elt'])

    def test_replaceOnSHierarchicalStack(self):

        #
        # Test with strings
        #

        stack = HierarchicalStack()
        stack.push('elt1')
        stack.push('elt2')
        self.assertEqual(stack.getLevelContent(), ['elt1', 'elt2'])
        stack.replace('elt2', 'elt4')
        self.assertEqual(stack.getLevelContent(), ['elt1', 'elt4'])

        #
        # Test with elements objects
        #

        oelt = UserStackElement('string_elt')
        stack.replace('elt4', oelt)
        self.assertEqual(stack.getLevelContent(), ['elt1', 'string_elt'])

        #
        # Test with different levels
        #

        stack.push('string_elt', level=1)
        stack.push('string_elt', level=-1)
        self.assertEqual(stack.getLevelContent(), ['elt1', 'string_elt'])
        self.assertEqual(stack.getLevelContent(level=1), ['string_elt'])
        self.assertEqual(stack.getLevelContent(level=-1), ['string_elt'])

        stack.push('elt1', level=1)
        self.assertEqual(stack.getLevelContent(), ['elt1', 'string_elt'])
        self.assertEqual(stack.getLevelContent(level=1), ['string_elt',
                                                          'elt1'])
        self.assertEqual(stack.getLevelContent(level=-1), ['string_elt'])

        stack.replace('string_elt', 'string_elt2')
        self.assertEqual(stack.getLevelContent(), ['elt1', 'string_elt2'])
        self.assertEqual(stack.getLevelContent(level=1), ['string_elt2',
                                                          'elt1'])
        self.assertEqual(stack.getLevelContent(level=-1), ['string_elt2'])

        stack.replace('elt1', 'elt2')
        self.assertEqual(stack.getLevelContent(), ['elt2', 'string_elt2'])
        self.assertEqual(stack.getLevelContent(level=1), ['string_elt2',
                                                          'elt2'])
        self.assertEqual(stack.getLevelContent(level=-1), ['string_elt2'])

    def test_insertInBetweenLevelsWithHierarchical(self):

        hstack = HierarchicalStack()
        self.assertEqual(hstack.getStackContent(), {})

        # Normal 
        hstack.push('elt1')
        hstack.push('elt3', level=1)
        self.assertEqual(hstack.getStackContent(), {0:['elt1'],
                                                    1:['elt3']})

        # Insert in between 0 and 1
        # current_level is 0
        self.assertEqual(hstack.getCurrentLevel(), 0)
        hstack.push('elt2', low_level=0, high_level=1)
        self.assertEqual(hstack.getStackContent(), {0:['elt1'],
                                                    1:['elt2'],
                                                    2:['elt3'],
                                                    })
        # Change current level and try to insert
        # 0 is the edge level where we need to test
        hstack.doIncLevel()
        self.assertEqual(hstack.getCurrentLevel(), 1)
        hstack.push('elt4', low_level=0, high_level=1)
        self.assertEqual(hstack.getStackContent(), {-1:['elt1'],
                                                    0:['elt4'],
                                                    1:['elt2'],
                                                    2:['elt3'],
                                                    })
        hstack.push('elt5', low_level=2, high_level=3)
        self.assertEqual(hstack.getStackContent(), {-1:['elt1'],
                                                    0:['elt4'],
                                                    1:['elt2'],
                                                    2:['elt3'],
                                                    3:['elt5'],
                                                    })
        hstack.push('elt6', low_level=-2, high_level=-1)
        self.assertEqual(hstack.getStackContent(), {-2:['elt6'],
                                                    -1:['elt1'],
                                                    0:['elt4'],
                                                    1:['elt2'],
                                                    2:['elt3'],
                                                    3:['elt5'],
                                                    })
        hstack.push('elt7', low_level=-4, high_level=-3)
        self.assertEqual(hstack.getStackContent(), {-2:['elt6'],
                                                    -1:['elt1'],
                                                    0:['elt4'],
                                                    1:['elt2'],
                                                    2:['elt3'],
                                                    3:['elt5'],
                                                    })
        hstack.push('elt7', low_level=4, high_level=5)
        self.assertEqual(hstack.getStackContent(), {-2:['elt6'],
                                                    -1:['elt1'],
                                                    0:['elt4'],
                                                    1:['elt2'],
                                                    2:['elt3'],
                                                    3:['elt5'],
                                                    })
        
        
def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestCPSWorkflowStacks)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
