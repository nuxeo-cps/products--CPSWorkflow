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
from zope.testing import doctest

from AccessControl.SecurityManagement import newSecurityManager

from Products.CMFCore.tests.base.testcase import SecurityRequestTest

from Products.CPSWorkflow.basicstacks import SimpleStack
from Products.CPSWorkflow.basicstacks import HierarchicalStack

from Products.CPSWorkflow.basicstackdefinitions import StackDefinition
from Products.CPSWorkflow.basicstackdefinitions import SimpleStackDefinition
from Products.CPSWorkflow.basicstackdefinitions import \
     HierarchicalStackDefinition

from Products.CPSWorkflow.interfaces import IWorkflowStackDefinition

#######################################################################
# Fake a User Folder with groups
#######################################################################

class FakeGroup:
    def __init__(self, users):
        self._users = users
    def getUsers(self):
        return self._users

class FakeUserFolderWithGroups:
    _groups = {'group1': FakeGroup(['user1']),
               'group2': FakeGroup(['user1', 'user2'])}
    _users = {}
    def getGroupById(self, id):
        # KeyError if not found as PUF
        # so that we'll be able to test
        return self._groups[id]
    def setUser(self, member_id, member_instance):
        self._users[member_id] = member_instance
    def getUser(self, member_id):
        return self._users.get(member_id)

########################################################################
# Fake a portal_membership tool
########################################################################

class FakeMember:
    def __init__(self, id, roles=()):
        self._userid = id
        self._roles = roles
    def getMemberId(self):
        return self._userid
    def getRolesInContext(self, context):
        return self._roles

class FakeMembershipTool:
    _users = {'user3' : FakeMember('user3', ('Owner', 'WorkspaceReader')),
              'user1' : FakeMember('user1', ('WorkspaceManager',)),
              'user2' : FakeMember('user1', ('WorkspaceMember',)),
             }
    _authenticated_user = _users['user3']
    def getAuthenticatedMember(self):
        return self._authenticated_user
    def getMemberById(self, member_id):
        return self._users.get(member_id)
    def isAnonymousUser(self):
        return 0

#######################################################################

class TestCPSWorkflowStackDefinition(SecurityRequestTest):

    def login(self, member_id, roles=()):
        aclu = FakeUserFolderWithGroups()
        self.acl_users = aclu
        self.acl_users.setUser(member_id, FakeMember(member_id, roles))
        newSecurityManager(None, self.acl_users.getUser(member_id))

    def test_interface(self):
        from zope.interface.verify import verifyClass
        verifyClass(IWorkflowStackDefinition, StackDefinition)
        verifyClass(IWorkflowStackDefinition, SimpleStackDefinition)
        verifyClass(IWorkflowStackDefinition, HierarchicalStackDefinition)

    def test_StackDefinition(self):
        base = StackDefinition('Simple Stack',
                               'toto')

        # Basics
        self.assertEqual(base.meta_type, 'Stack Definition')
        self.assertEqual(base.getStackDataStructureType(), 'Simple Stack')
        self.assertEqual(base.getStackWorkflowVariableId(), 'toto')

        # Not implemented methods
        self.assertRaises(NotImplementedError, base._getLocalRolesMapping,
                          None)

    def test_SimpleStackDefinition(self):
        self.login('user1', ('Owner',))
        simple = SimpleStackDefinition('Simple Stack',
                                       'toto')
        simple.setEmptyStackManageGuard(guard_roles='Owner; WorkspaceManager')

        # Add expressions
        simple.addManagedRole('WorkspaceManager', 'python:1')

        # Basics
        self.assertEqual(simple.meta_type, 'Simple Stack Definition')
        self.assertEqual(simple.getStackDataStructureType(), 'Simple Stack')
        self.assertEqual(simple.getStackWorkflowVariableId(), 'toto')

        # Stack ds preparation

        # No given stack
        ds = simple._prepareStack(ds=None)
        self.assertEqual(ds.meta_type, 'Simple Stack')

        # A given SimpleStack
        sstack = SimpleStack()
        ds = simple._prepareStack(ds=sstack)
        self.assertEqual(ds.meta_type, 'Simple Stack')
        self.assertEqual(ds, sstack)

        # A wrong type given as ds
        # Will change it for a SimpleStack
        hstack = HierarchicalStack()
        ds = simple._prepareStack(ds=hstack)
        self.assertEqual(ds.meta_type, 'Simple Stack')
        self.assertNotEqual(ds, hstack)

        #
        # push
        #

        sstack = SimpleStack()

        # Push one guy in it
        new_stack = simple._push(sstack, push_ids=['user:user1'])

        # Not the same instance since it's a copy
        self.assertNotEqual(new_stack, sstack)

        # Check meta_type
        self.assertEqual(new_stack.meta_type, 'Simple Stack')

        # Check local roles
        self.assertEqual(simple._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceManager',)})

        # Try to remove the user1

        # get a copy of the initial stack
        self.assertNotEqual(new_stack, simple._pop(new_stack, pop_ids=['user:user1']))
        self.assertEqual(new_stack.getStackContent(context=self), [])
        self.assertEqual(new_stack.meta_type, 'Simple Stack')
        self.assertEqual(simple._getLocalRolesMapping(new_stack),
                         {})

        # Check an empty push.
        # We get back an empty stack
        new_stack = simple._push(new_stack)
        self.assertNotEqual(new_stack, None)
        self.assertEqual(new_stack.getStackContent(context=self), [])
        self.assertEqual(new_stack.meta_type, 'Simple Stack')

        # Local roles (current / former)
        self.assertEqual(simple._getLocalRolesMapping(new_stack),
                         {})

        # Push again
        new_stack = simple._push(new_stack,
                                 push_ids=['user:user1', 'user:user2'])
        self.assertNotEqual(new_stack, None)
        self.assertEqual(new_stack.meta_type, 'Simple Stack')
        self.assertEqual(new_stack.getStackContent(context=self),
                         ['user:user1', 'user:user2'])

        # Local Roles
        self.assertEqual(simple._getLocalRolesMapping(new_stack),
                         {'user1':('WorkspaceManager',),
                          'user2':('WorkspaceManager',)})

        # Add a fake acl_users to the instance
        aclu = self.acl_users
        # Add a fake membership tool
        mtool = FakeMembershipTool()
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user3',
                                               context=self),
                         0)
        # No id specified gonna ask the authenticated member (user3)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         0)
        # Add user3 wich is the one authenticated within the fake tool
        new_stack = simple._push(new_stack, push_ids=['user:user3'])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)
        # Remove user1 and user2
        new_stack = simple._pop(new_stack, pop_ids=['user:user1', 'user:user2'])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         0)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         0)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

        # Add group group1 where user1 is a user
        new_stack = simple._push(new_stack, push_ids=['group:group1'])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         0)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

        # Add a group in the stack that doesn't exist
        new_stack = simple._push(new_stack, push_ids=['group:group3'])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         0)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

        # user1 and user2 defined within group2
        new_stack = simple._push(new_stack, push_ids=['group:group2'])
        self.assertEqual(new_stack.getStackContent(context=self),
                         ['user:user3', 'group:group1', 'group:group3',
                          'group:group2'])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

        # Remove group1 and group3
        new_stack = simple._pop(new_stack, pop_ids=['group:group1',
                                               'group:group3',])
        self.assertEqual(new_stack.getStackContent(context=self),
                         ['user:user3', 'group:group2'])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         1)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

        # Remove group2
        # User 1 stil within the stack by himself
        new_stack = simple._pop(new_stack, pop_ids=['group:group2'])
        self.assertEqual(new_stack.getStackContent(context=self),
                         ['user:user3',])
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         0)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         0)
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

        # Remove user1
        new_stack = simple._pop(new_stack, pop_ids=['user:user3'])
        self.assertEqual(new_stack.getStackContent(context=self), [])


        #
        # Here user1 is WorkspaceManager wich is the associated local roles and
        # because the stack is empty it's granted
        #

        member_user1 = mtool.getMemberById('user1')
        user1_roles = member_user1.getRolesInContext(self)
        self.assertEqual('WorkspaceManager' in user1_roles, 1)

        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               member_id='user1',
                                               context=self),
                         1)

        self.login('user2', ('Member',))
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=self.acl_users,
                                               mtool=mtool,
                                               member_id='user2',
                                               context=self),
                         0)

        #
        # Here user3 is the Authenticated Member because the stack is empty
        # it's granted
        #

        auth_member = mtool.getAuthenticatedMember()
        self.assertEqual(auth_member.getMemberId(), 'user3')
        auth_roles = auth_member.getRolesInContext(self)
        self.assertEqual('Owner' in auth_roles, 1)

        self.login('user3', ('Owner',))
        self.assertEqual(simple._canManageStack(ds=new_stack,
                                               aclu=aclu,
                                               mtool=mtool,
                                               context=self),
                         1)

    def test_HierarchicalStackDefinitionCurrentLevel(self):
        hierarchical = HierarchicalStackDefinition(
            'Hierarchical Stack',
            'toto')
        hierarchical.setEmptyStackManageGuard(
            guard_roles='Owner;WorkspaceManager')

        # Add expressions
        hierarchical.addManagedRole(
            'WorkspaceManager',
            "python:level == stack.getCurrentLevel() and 1 or nothing")
        hierarchical.addManagedRole(
            'WorkspaceMember',
            "python:level < stack.getCurrentLevel() and 1 or nothing")
        hierarchical.addManagedRole(
            'WorkspaceReader',
            "python:level > stack.getCurrentLevel() and 1 or nothing")

        # Basics
        self.assertEqual(hierarchical.meta_type,
                         'Hierarchical Stack Definition')
        self.assertEqual(
            hierarchical.getStackDataStructureType(), 'Hierarchical Stack')
        self.assertEqual(hierarchical.getStackWorkflowVariableId(), 'toto')

        # Stack ds preparation
        ds = hierarchical._prepareStack(ds=None)
        self.assertEqual(ds.meta_type, 'Hierarchical Stack')

        # A given HierarchicalStack
        hstack = HierarchicalStack()
        ds = hierarchical._prepareStack(ds=hstack)
        self.assertEqual(ds.meta_type, 'Hierarchical Stack')
        self.assertEqual(ds, hstack)

        # A wrong type given as ds
        # Will change it for a HierarchicalStack
        sstack = SimpleStack()
        ds = hierarchical._prepareStack(ds=sstack)
        self.assertEqual(ds.meta_type, 'Hierarchical Stack')
        self.assertNotEqual(ds, sstack)

        #
        # push
        #

        hstack = HierarchicalStack()

        # Push one guy in it
        new_stack = hierarchical._push(hstack,
                                      push_ids=['user:user1'],
                                      levels=[0])

        # Not the same instance since it's a copy
        self.assertNotEqual(new_stack, hstack)

        # Check meta_type
        self.assertEqual(new_stack.meta_type, 'Hierarchical Stack')

        # Check local roles

        # No former local roles mapping
        # Push the guy in it


        self.assertEqual(new_stack.getCurrentLevel(), 0)
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceManager',)})

        # Try to remove the user1

        # get a copy of the initial stack
        self.assertNotEqual(new_stack, hierarchical._pop(
            new_stack, pop_ids=['0,user:user1',]))
        self.assertEqual(new_stack.getLevelContent(context=self), [])
        self.assertEqual(new_stack.meta_type, 'Hierarchical Stack')
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {})

        # Check an empty push.
        # We get back an empty stack
        new_stack = hierarchical._push(new_stack)
        self.assertNotEqual(new_stack, None)
        self.assertEqual(new_stack.getLevelContent(context=self), [])
        self.assertEqual(new_stack.meta_type, 'Hierarchical Stack')

        # Local roles (current / former)
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {})

        # Push again
        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user1', 'user:user2'],
                                      levels=[0,0])
        self.assertNotEqual(new_stack, None)
        self.assertEqual(new_stack.meta_type, 'Hierarchical Stack')
        self.assertEqual(new_stack.getLevelContent(context=self),
                         ['user:user1', 'user:user2'])

        # Local Roles
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1':('WorkspaceManager',),
                          'user2':('WorkspaceManager',)})

        # Add a fake acl_users to the instance
        aclu = FakeUserFolderWithGroups()
        # Add a fake membership tool
        mtool = FakeMembershipTool()
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user3',
                                                     context=self),
                         0)
        # No id specified gonna ask the authenticated member (user3)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         0)
        # Add user3 wich is the one authenticated within the fake tool
        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user3'],
                                      levels=[0])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)
        # Remove user1 and user2
        new_stack = hierarchical._pop(new_stack,
                                     pop_ids=['0,user:user1', '0,user:user2'])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         0)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         0)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

        # Add group group1 where user1 is a user
        new_stack = hierarchical._push(new_stack,
                                      push_ids=['group:group1'],
                                      levels=[0])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         0)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

        # Add a group in the tack that doesn't exist
        new_stack = hierarchical._push(new_stack,
                                      push_ids=['group:group3'],
                                      levels=[0])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         0)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

        # user1 and user2 defined within group2
        new_stack = hierarchical._push(new_stack,
                                      push_ids=['group:group2'],
                                      levels=[0])
        self.assertEqual(new_stack.getLevelContent(context=self),
                         ['user:user3', 'group:group1', 'group:group3',
                          'group:group2'])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

        # Remove group1 and group3
        new_stack = hierarchical._pop(new_stack,
                                     pop_ids=['0,group:group1', '0,group:group3',])
        self.assertEqual(new_stack.getLevelContent(context=self),
                         ['user:user3', 'group:group2'])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         1)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

        # Remove group2
        # User 1 stil within the stack by himself
        new_stack = hierarchical._pop(new_stack,
                                     pop_ids=['0,group:group2'])
        self.assertEqual(new_stack.getLevelContent(context=self),
                         ['user:user3',])
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         0)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         0)
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

        # Remove user1
        new_stack = hierarchical._pop(new_stack,
                                     pop_ids=['0,user:user3'])
        self.assertEqual(new_stack.getLevelContent(context=self), [])

        #
        # Here user1 is WorkspaceManager wich is the associated local roles and
        # because the stack is empty it's granted
        #

        member_user1 = mtool.getMemberById('user1')
        user1_roles = member_user1.getRolesInContext(self)
        self.assertEqual('WorkspaceManager' in user1_roles, 1)

        self.login('user', ('Owner', 'WorkspaceManager',))
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user1',
                                                     context=self),
                         1)

        self.login('user2', ('Member',))
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     member_id='user2',
                                                     context=self),
                         0)

        #
        # Here user3 is the Authenticated Member because the stack is empty
        # it's granted
        #

        auth_member = mtool.getAuthenticatedMember()
        self.assertEqual(auth_member.getMemberId(), 'user3')
        auth_roles = auth_member.getRolesInContext(self)
        self.assertEqual('Owner' in auth_roles, 1)

        self.login('user1', ('Owner',))
        self.assertEqual(hierarchical._canManageStack(ds=new_stack,
                                                     aclu=aclu,
                                                     mtool=mtool,
                                                     context=self),
                         1)

    def test_HierarchicalStackDefinitionWithLevelChanges(self):

        # Add a fake acl_users to the instance
        aclu = FakeUserFolderWithGroups()
        # Add a fake membership tool
        mtool = FakeMembershipTool()

        hierarchical = HierarchicalStackDefinition(
            'Hierarchical Stack',
            'toto')

        # Add expressions
        hierarchical.addManagedRole(
            'WorkspaceManager',
            "python:level == stack.getCurrentLevel() and 1 or nothing")
        hierarchical.addManagedRole(
            'WorkspaceMember',
            "python:level < stack.getCurrentLevel() and 1 or nothing")
        hierarchical.addManagedRole(
            'WorkspaceReader',
            "python:level > stack.getCurrentLevel() and 1 or nothing")

        # XX
        hierarchical.setEmptyStackManageGuard(
            guard_roles='Owner; WorkspaceManager')

        # Basics
        self.assertEqual(hierarchical.meta_type,
                         'Hierarchical Stack Definition')
        self.assertEqual(
            hierarchical.getStackDataStructureType(), 'Hierarchical Stack')
        self.assertEqual(hierarchical.getStackWorkflowVariableId(), 'toto')

        # Stack ds preparation
        ds = hierarchical._prepareStack(ds=None)
        self.assertEqual(ds.meta_type, 'Hierarchical Stack')

        # A given HierarchicalStack
        hstack = HierarchicalStack()
        ds = hierarchical._prepareStack(ds=hstack)
        self.assertEqual(ds.meta_type, 'Hierarchical Stack')
        self.assertEqual(ds, hstack)

        # A wrong type given as ds
        # Will change it for a HierarchicalStack
        sstack = SimpleStack()
        ds = hierarchical._prepareStack(ds=sstack)
        self.assertEqual(ds.meta_type, 'Hierarchical Stack')
        self.assertNotEqual(ds, sstack)

        #
        # push
        #

        hstack = HierarchicalStack()

        # Push one guy in it
        new_stack = hierarchical._push(hstack,
                                      push_ids=['user:user1'],
                                      levels=[0])

        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user2'],
                                      levels=[0])

        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user3'],
                                      levels=[1])

        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user4'],
                                      levels=[-1])

        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user5'],
                                      levels=[2])

        new_stack = hierarchical._push(new_stack,
                                      push_ids=['user:user6'],
                                      levels=[-2])

        # Not the same instance since it's a copy
        self.assertNotEqual(new_stack, hstack)

        # Check meta_type
        self.assertEqual(new_stack.meta_type, 'Hierarchical Stack')

        ## Check local roles

        # Push the guy in it
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceManager',),
                          'user2': ('WorkspaceManager',),
                          'user3': ('WorkspaceReader',),
                          'user4': ('WorkspaceMember',),
                          'user5': ('WorkspaceReader',),
                          'user6': ('WorkspaceMember',),
                          })

        #
        # Check _canManageStack for this guys
        #

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         0)

        #
        # Change current level to -1
        #

        hierarchical._doDecLevel(new_stack)

        # Local roles

        # current ones
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceReader',),
                          'user2': ('WorkspaceReader',),
                          'user3': ('WorkspaceReader',),
                          'user4': ('WorkspaceManager',),
                          'user5': ('WorkspaceReader',),
                          'user6': ('WorkspaceMember',),
                          })

        # Check _canManageStack for this guys

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         0)


        #
        # Change current level to -2
        #

        hierarchical._doDecLevel(new_stack)

        # Current Local roles mapping
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceReader',),
                          'user2': ('WorkspaceReader',),
                          'user3': ('WorkspaceReader',),
                          'user4': ('WorkspaceReader',),
                          'user5': ('WorkspaceReader',),
                          'user6': ('WorkspaceManager',),
                          })

        # Check _canManageStack for this guys

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         1)


        #
        # Change current level to -1
        #

        hierarchical._doIncLevel(new_stack)

        # Current Local roles mapping
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceReader',),
                          'user2': ('WorkspaceReader',),
                          'user3': ('WorkspaceReader',),
                          'user4': ('WorkspaceManager',),
                          'user5': ('WorkspaceReader',),
                          'user6': ('WorkspaceMember',),
                          })

        # Check _canManageStack for this guys

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         0)


        #
        # Change current level to 0
        #

        hierarchical._doIncLevel(new_stack)

        # Current Local roles mapping
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceManager',),
                          'user2': ('WorkspaceManager',),
                          'user3': ('WorkspaceReader',),
                          'user4': ('WorkspaceMember',),
                          'user5': ('WorkspaceReader',),
                          'user6': ('WorkspaceMember',),
                          })

        # Check _canManageStack for this guys

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         0)


        #
        # Change current level to 1
        #

        hierarchical._doIncLevel(new_stack)

        # Current Local roles mapping
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceMember',),
                          'user2': ('WorkspaceMember',),
                          'user3': ('WorkspaceManager',),
                          'user4': ('WorkspaceMember',),
                          'user5': ('WorkspaceReader',),
                          'user6': ('WorkspaceMember',),
                          })

        # Check _canManageStack for this guys

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         0)

        #
        # Change current level to 2
        #

        hierarchical._doIncLevel(new_stack)

        # Current Local roles mapping
        self.assertEqual(hierarchical._getLocalRolesMapping(new_stack),
                         {'user1': ('WorkspaceMember',),
                          'user2': ('WorkspaceMember',),
                          'user3': ('WorkspaceMember',),
                          'user4': ('WorkspaceMember',),
                          'user5': ('WorkspaceManager',),
                          'user6': ('WorkspaceMember',),
                          })

        # Check _canManageStack for this guys

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user1',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user2',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user3',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user4',
                                                     ),
                         0)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user5',
                                                     ),
                         1)

        self.assertEqual(hierarchical._canManageStack(new_stack,
                                                     aclu,
                                                     mtool,
                                                     self,
                                                     member_id='user6',
                                                     ),
                         0)

    def test_reset_simple_sdef(self):

        #
        # Test reset simple sdef
        #

        simple = SimpleStackDefinition(
            'Simple Stack',
            'toto')

        stack = simple._push(None, push_ids=['user:user1'])
        self.assertEqual(stack.getMetaType(),
                         'Simple Stack')
        self.assertEqual(stack.getStackContent(context=self),
                         ['user:user1'])
        stack = simple._reset(stack)
        self.assertEqual(stack.getMetaType(),
                         'Simple Stack')
        self.assertEqual(stack.getStackContent(context=self),
                         [])

    def test_reset_hierarchical_sdef(self):

        #
        # Test reset simple sdef
        #

        hierarchical = HierarchicalStackDefinition(
            'Hierarchical Stack',
            'toto'
            )

        stack = hierarchical._push(None,
                                  push_ids=['user:user1'],
                                  levels=[0])
        self.assertEqual(stack.getMetaType(),
                         'Hierarchical Stack')
        self.assertEqual(stack.getLevelContent(context=self),
                         ['user:user1'])
        stack = hierarchical._reset(stack)
        self.assertEqual(stack.getMetaType(),
                         'Hierarchical Stack')
        self.assertEqual(stack.getLevelContent(context=self),
                         [])

    def test_managed_roles(self):

        #
        # This API is defined on the base stack definition class
        #

        sstackdef = StackDefinition('Simple Stack', 'id')
        self.assert_(sstackdef.getManagedRoles() == [])

        # Add WorkspaceManager as managed role
        sstackdef.addManagedRole('WorkspaceManager')
        self.assertEqual(sstackdef.getManagedRoles(), ['WorkspaceManager'])

        # Add WorkspaceMember as managed role
        sstackdef.addManagedRole('WorkspaceMember')
        self.assert_('WorkspaceMember' in sstackdef.getManagedRoles())
        self.assert_('WorkspaceManager' in sstackdef.getManagedRoles())
        self.assert_(len(sstackdef.getManagedRoles()) == 2)

        # Del a WorkspaceMember
        sstackdef.delManagedRole('WorkspaceMember')
        self.assert_('WorkspaceMember' not in sstackdef.getManagedRoles())
        self.assert_('WorkspaceManager' in sstackdef.getManagedRoles())
        self.assert_(len(sstackdef.getManagedRoles()) == 1)

    def test_role_expressions(self):

        #
        # Test the possiblity to add expressions to role
        #

        sstackdef = StackDefinition('Simple Stack', 'id')
        self.assert_(sstackdef.getManagedRoles() == [])

        # Add WorkspaceManager as managed role
        sstackdef.addManagedRole('WorkspaceManager')
        self.assertEqual(sstackdef.getManagedRoles(), ['WorkspaceManager'])

        # Add expression
        sstackdef._addExpressionForRole('WorkspaceManager', 'string:toto')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         None), 'toto')

        # Change expression
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:1')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         None), 1)

    def test_role_expression_NS_with_simple(self):

        #
        # Test the NS content
        #

        sstack = SimpleStack()
        sstackdef = SimpleStackDefinition('Simple Stack Definition',
                                          'Simple Stack')

        # Add WorkspaceManager as managed role
        sstackdef.addManagedRole('WorkspaceManager')
        self.assertEqual(sstackdef.getManagedRoles(), ['WorkspaceManager'])

        # Add expression and test the NS (if the stack object is available)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:stack')
        self.assertEqual(
            sstackdef._getExpressionForRole('WorkspaceManager', sstack),
            sstack)
        sstackdef._addExpressionForRole(
            'WorkspaceManager', 'python:stack.getStackContent()')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack), [])
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:stackdef')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack),
                         sstackdef)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:level')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack),
                         0)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:elt')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack),
                         None)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:elt')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack,
                                                         None,
                                                         'elt1'),
                         'elt1')
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:DateTime')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is not None)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:nothing')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is None)

        # test portal object none in here
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:portal')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is None)

        # Add a fake URLTool
        class URLTool:
            meta_type = 'CMF URL Tool'
            id = 'portal_url'
            def getPortalObject(self):
                return self

        self.portal_url = URLTool()
        sstackdef.portal_url = URLTool()

        # Test again and check we have one now
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:portal')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is not None)

    def test_role_expression_NS_with_hierarchical(self):

        #
        # Test the NS content
        #

        sstack = HierarchicalStack()
        sstackdef = HierarchicalStackDefinition('Hierarchical Stack Definition',
                                                'Hierarchical Stack')

        # Add WorkspaceManager as managed role
        sstackdef.addManagedRole('WorkspaceManager')
        self.assertEqual(sstackdef.getManagedRoles(), ['WorkspaceManager'])

        # Add expression and test the NS (if the stack object is available)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:stack')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack), sstack)
        sstackdef._addExpressionForRole('WorkspaceManager',
                                        'python:stack.getStackContent()')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack), {})
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:stackdef')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack),
                         sstackdef)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:level')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack),
                         0)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:level')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack,
                                                         1),
                         1)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:elt')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack),
                         None)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:elt')
        self.assertEqual(sstackdef._getExpressionForRole('WorkspaceManager',
                                                         sstack,
                                                         1,
                                                         'elt1'),
                         'elt1')
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:DateTime')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is not None)
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:nothing')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is None)

        # test portal object none in here
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:portal')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is None)

        # Add a fake URLTool
        class URLTool:
            meta_type = 'CMF URL Tool'
            id = 'portal_url'
            def getPortalObject(self):
                return self

        self.portal_url = URLTool()
        sstackdef.portal_url = URLTool()

        # Test again and check we have one now
        sstackdef._addExpressionForRole('WorkspaceManager', 'python:portal')
        self.assert_(sstackdef._getExpressionForRole('WorkspaceManager',
                                                     sstack) is not None)

    def test_getlocalRolesMappings_with_simple(self):

        #
        # test namespace:
        # - stack
        # - elt
        #
        sstackdef = SimpleStackDefinition('Simple Stack',
                                          'toto')

        # Add WorkspaceManager as managed role
        sstackdef.addManagedRole('WorkspaceManager')
        self.assertEqual(sstackdef.getManagedRoles(), ['WorkspaceManager'])

        # test that local role is given only if number of stack elements is even
        sstack = SimpleStack()
        sstackdef._addExpressionForRole('WorkspaceManager',
                                        'python:len(stack.getStackContent())%2==1')
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack), {})
        sstack = sstackdef._push(sstack, push_ids=('user:elt1',))
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'elt1': ('WorkspaceManager',)})
        sstack = sstackdef._push(sstack, push_ids=('user:elt2',))
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack), {})
        sstack = sstackdef._push(sstack, push_ids=('user:elt3',))
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'elt1': ('WorkspaceManager',),
                          'elt2': ('WorkspaceManager',),
                          'elt3': ('WorkspaceManager',),
                          })

        # test that local role is given only if elt id starts with 'hello'
        sstack = SimpleStack()
        sstackdef._addExpressionForRole('WorkspaceManager',
                                        "python:elt.getIdWithoutPrefix().startswith('hello')")
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack), {})
        sstack = sstackdef._push(sstack, push_ids=('user:hello_elt1',))
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'hello_elt1': ('WorkspaceManager',)})
        sstack = sstackdef._push(sstack, push_ids=('user:elt2',))
        self.assertEqual(sstackdef._getLocalRolesMapping(sstack),
                         {'hello_elt1': ('WorkspaceManager',)})

    def test_getlocalRolesMappings_with_hierarchical(self):

        #
        # test namespace:
        # - stack
        # - elt
        # - level
        #
        hstack = HierarchicalStack()
        hstackdef = HierarchicalStackDefinition('Hierarchical Stack',
                                                'toto')

        # Add WorkspaceManager as managed role
        hstackdef.addManagedRole('WorkspaceManager')
        self.assertEqual(hstackdef.getManagedRoles(), ['WorkspaceManager'])

        # test that local role is given only if there an uneven number of
        # people at given level
        hstackdef._addExpressionForRole('WorkspaceManager',
                                        'python:len(stack.getLevelContent(level))%2==1')
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack), {})
        kw = {
            'push_ids': ('user:elt1',),
            'levels': (0,)
            }
        hstack = hstackdef._push(hstack, **kw)
        # NB: expression is evaluated after elt1 has been inserted into the
        # stack
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'elt1': ('WorkspaceManager',)})
        kw = {
            'push_ids': ('user:elt2',),
            'levels': (0,)
            }
        hstack = hstackdef._push(hstack, **kw)
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack), {})
        kw = {
            'push_ids': ('user:elt3',),
            'levels': (1,)
            }
        hstack = hstackdef._push(hstack, **kw)
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'elt3': ('WorkspaceManager',),})

        # test that local role is given only if elt id starts with 'hello'
        hstack = HierarchicalStack()
        hstackdef._addExpressionForRole('WorkspaceManager',
                                        "python:elt.getIdWithoutPrefix().startswith('hello')")
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack), {})
        kw = {
            'push_ids': ('user:hello_elt1',),
            'levels': (0,)
            }
        hstack = hstackdef._push(hstack, **kw)
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'hello_elt1': ('WorkspaceManager',)})
        kw = {
            'push_ids': ('user:elt2',),
            'levels': (0,)
            }
        hstack = hstackdef._push(hstack, **kw)
        self.assertEqual(hstackdef._getLocalRolesMapping(hstack),
                         {'hello_elt1': ('WorkspaceManager',)})


    def test_ResetOnSimpleStackDefinition(self):

        #
        # Test the reset behavior on the Simple Stack Definition class type
        #

        stack = SimpleStack()
        stackdef = SimpleStackDefinition('Simple Stack',
                                         'Fake')

        kw = {}
        kw['push_ids'] = ('elt1',)
        stack = stackdef._push(stack, **kw)
        self.assertEqual([x for x in stack._getElementsContainer()],
                         ['elt1'])

        # Reset with one (1) new user
        stack = stackdef._reset(stack, reset_ids=('elt2',))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()],
                         ['elt2'])

        # Reset with two (2) new users
        stack = stackdef._reset(stack, reset_ids=('elt3', 'elt4'))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()],
                         ['elt3', 'elt4'])

        # Reset with one (1) new group
        stack = stackdef._reset(stack, reset_ids=('group:elt2',))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()],
                         ['group:elt2'])

        # Reset with two (2) new users
        stack = stackdef._reset(stack,
                                    reset_ids=('group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()],
                         ['group:elt3', 'group:elt4'])

        # Reset with one new stack
        new_stack = SimpleStack()
        new_stack._push('new_elt')
        stack = stackdef._reset(stack, new_stack=new_stack)
        self.assertEqual(stack._getElementsContainer(),
                         new_stack._getElementsContainer())

        # Reset with a new stack, new users and new groups
        new_stack = SimpleStack()
        stack = stackdef._reset(stack, new_stack=new_stack,
                                reset_ids=('elt1', 'elt2', 'group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()],
                         ['elt1', 'elt2', 'group:elt3', 'group:elt4'])

    def test_ResetOnHierarchicalStackDefinition(self):

        #
        # Test the reset behavior on the Hierachical Stack Definition
        # class type
        #

        stack = HierarchicalStack()
        stackdef = HierarchicalStackDefinition('Hierarchical Stack',
                                               'Fake')

        kw = {}
        kw['push_ids'] = ('elt1',)
        kw['levels'] = (0,)
        stack = stackdef._push(stack, **kw)
        self.assertEqual([x for x in stack._getElementsContainer()[0]],
                         ['elt1'])

        # Reset with one (1) new user
        stack = stackdef._reset(stack, reset_ids=('elt2',))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()[0]],
                         ['elt2'])

        # Reset with two (2) new users
        stack = stackdef._reset(stack, reset_ids=('elt3', 'elt4'))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()[0]],
                         ['elt3', 'elt4'])

        # Reset with one (1) new group
        stack = stackdef._reset(stack, reset_ids=('group:elt2',))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()[0]],
                         ['group:elt2'])

        # Reset with two (2) new users
        stack = stackdef._reset(stack,
                                    reset_ids=('group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()[0]],
                         ['group:elt3', 'group:elt4'])

        # Reset with one new stack
        new_stack = HierarchicalStack()
        new_stack._push('new_elt')
        stack = stackdef._reset(stack, new_stack=new_stack)
        self.assertEqual(stack._getElementsContainer(),
                         new_stack._getElementsContainer())

        # Reset with a new stack, new users and new groups
        new_stack = HierarchicalStack()
        stack = stackdef._reset(stack, new_stack=new_stack,
                                reset_ids=('elt1', 'elt2', 'group:elt3', 'group:elt4'))
        self.assertEqual([x.getId() for x in stack._getElementsContainer()[0]],
                         ['elt1', 'elt2', 'group:elt3', 'group:elt4'])

    def test_insertInBetweenLevelWithinHierarchical(self):
        # test some insertions within a hierarchical stack through
        # a stack definition
        hstack = HierarchicalStack()
        self.assertEqual(hstack.getStackContent(context=self), {})

        hstackdef = HierarchicalStackDefinition('Hierarhical Stack', 'fake')

        # Normal
        #hstack = hstackdef._push(hstack, elt='elt1')
        hstack._push('elt1')
        hstack._push('elt3', level=1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1'],
                          1:['elt3']})

        # Insert in between 0 and 1
        # current_level is 0
        self.assertEqual(hstack.getCurrentLevel(), 0)
        hstack._push('elt2', low_level=0, high_level=1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {0:['elt1'],
                          1:['elt2'],
                          2:['elt3'],
                          })
        # Change current level and try to insert
        # 0 is the edge level where we need to test
        hstack.doIncLevel()
        self.assertEqual(hstack.getCurrentLevel(), 1)
        hstack._push('elt4', low_level=0, high_level=1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          })
        hstack._push('elt5', low_level=2, high_level=3)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        hstack._push('elt6', low_level=-2, high_level=-1)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        hstack._push('elt7', low_level=-4, high_level=-3)
        self.assertEqual(hstack.getStackContent(context=self),
                         {-2:['elt6'],
                          -1:['elt1'],
                          0:['elt4'],
                          1:['elt2'],
                          2:['elt3'],
                          3:['elt5'],
                          })
        hstack._push('elt7', low_level=4, high_level=5)
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
    suite.addTest(unittest.makeSuite(TestCPSWorkflowStackDefinition))
    suite.addTest(doctest.DocFileTest('doc/stackdefinition.txt',
                                      package='Products.CPSWorkflow',
                                      optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS))
    return suite

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
