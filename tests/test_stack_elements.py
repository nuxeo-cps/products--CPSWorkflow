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

from Products.PageTemplates.TALES import CompilerError

from Products.CPSWorkflow.interfaces import IStackElement
from Products.CPSWorkflow.stackelement import StackElement
from Products.CPSWorkflow.stackelement import StackElementWithData
from Products.CPSWorkflow.basicstackelements import UserStackElement
from Products.CPSWorkflow.basicstackelements import GroupStackElement
from Products.CPSWorkflow.basicstackelements import UserStackElementWithData
from Products.CPSWorkflow.basicstackelements import GroupStackElementWithData
from Products.CPSWorkflow.basicstackelements import HiddenUserStackElement
from Products.CPSWorkflow.basicstackelements import HiddenGroupStackElement
from Products.CPSWorkflow.basicstackelements import UserSubstituteStackElement
from Products.CPSWorkflow.basicstackelements import GroupSubstituteStackElement
from Products.CPSWorkflow.basicstackelements import \
     USER_STACK_ELEMENT_NOT_VISIBLE, GROUP_STACK_ELEMENT_NOT_VISIBLE

from Products.CPSWorkflow.stackdefinitionguard import \
     StackDefinitionGuard as Guard


class FakeAclUsers:

    def getGroupById(self, group_id):
        if group_id == 'nuxeo':
            return FakeGroup('nuxeo', users='anguenot')
        elif group_id == 'empty':
            return FakeGroup('empty')
        else:
            raise KeyError(group_id)

class FakeGroup:

    def __init__(self, id, users=[]):
        self.id = id
        self.users = users

    def getUsers(self):
        return self.users


class TestStackElement(unittest.TestCase):

    def test_interface(self):
        from zope.interface.verify import verifyClass
        verifyClass(IStackElement, StackElement)

    def test_getPrefix(self):
        stack_elt = StackElement('fake')
        self.assertEquals(stack_elt.getPrefix(), '')

    def test_getIdWithoutPrefix(self):
        stack_elt = StackElement('fake')
        self.assertEquals(stack_elt.getIdWithoutPrefix(), 'fake')

    def test_getHiddenMetaType(self):
        stack_elt = StackElement('fake')
        self.assertEquals(stack_elt.getHiddenMetaType(), '')

    # XXX TODO: test isVisible, isEditable

    def test_stack_element_viewguard(self):

        #
        # Test the guard of the stack element
        #

        stack_elt = StackElement('fake')

        stack_elt.view_guard = Guard()

        guard = stack_elt.getViewGuard()
        self.assertNotEqual(guard, None)

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Initialize the guard with empty values
        # not initialization
        guard_props = {'guard_permissions':'',
                       'guard_roles':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==0)

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager;',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; ')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager;Member',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; Member')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager;Member',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; Member')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal;',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal; ')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :'python:1'}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'python:1')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :'string:'}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'string:')

        # Change guard with wrong TALES
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :'python:'}
        self.assertRaises(CompilerError,
                          guard.changeFromProperties, guard_props)

        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'string:')

        # Summary
        summary = """Requires permission: <code>ManagePortal</code> <br/> Requires role: <code>Manager</code> <br/> Requires expr: <code>string:</code>"""
        self.assertEqual(guard.getSummary(), summary)

        # reinit the guard
        guard_props = {'guard_permissions':'',
                       'guard_roles':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==0)

        # No API on DCWorkflow guard to reset properly....
        guard.permissions = ''
        guard.roles = ''
        guard.expr = None

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

    def test_stack_element_editguard(self):

        #
        # Test the guard of the stack element
        #

        stack_elt = StackElement('fake')

        stack_elt.view_guard = Guard()

        guard = stack_elt.getViewGuard()
        self.assertNotEqual(guard, None)

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Initialize the guard with empty values
        # not initialization
        guard_props = {'guard_permissions':'',
                       'guard_roles':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==0)

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager;',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; ')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager;Member',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; Member')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager;Member',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; Member')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal;',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal; ')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :'python:1'}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'python:1')

        # Change guard
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :'string:'}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'string:')

        # Change guard with wrong TALES
        guard_props = {'guard_roles':'Manager',
                       'guard_permissions':'ManagePortal',
                       'guard_expr' :'python:'}
        self.assertRaises(CompilerError,
                          guard.changeFromProperties, guard_props)

        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'string:')

        # Summary
        summary = """Requires permission: <code>ManagePortal</code> <br/> Requires role: <code>Manager</code> <br/> Requires expr: <code>string:</code>"""
        self.assertEqual(guard.getSummary(), summary)

        # reinit the guard
        guard_props = {'guard_permissions':'',
                       'guard_roles':'',
                       'guard_expr' :''}
        res = guard.changeFromProperties(guard_props)
        self.assert_(res==0)

        # No API on DCWorkflow guard to reset properly....
        guard.permissions = ''
        guard.roles = ''
        guard.expr = None

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')


class TestBasicStackElements(unittest.TestCase):

    def test_UserStackElement(self):

        # XXX supported for compatibility
        elt = UserStackElement('anguenot')
        self.assertEqual(elt(), 'anguenot')
        self.assertEqual(str(elt), 'anguenot')
        self.assert_('anguenot' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'anguenot')
        self.assertEqual(elt.getPrefix(), 'user')

        elt = UserStackElement('user:anguenot')
        self.assertEqual(elt(), 'user:anguenot')
        self.assertEqual(str(elt), 'user:anguenot')
        self.assert_('user:anguenot' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'anguenot')
        self.assertEqual(elt.getPrefix(), 'user')

        self.assertEqual(elt.getHiddenMetaType(), 'Hidden User Stack Element')

        self.assertEqual(elt.holdsUser('anguenot'), True)
        self.assertEqual(elt.holdsUser('anguenoteuh'), False)

    def test_UserStackElementCopy(self):
        elt = UserStackElement('user:anguenot')
        copy = elt.getCopy()
        # Try changing one attr and check
        copy.id = 'other'
        self.assertNotEqual(elt.getId(), copy.getId())

    def test_GroupStackElement(self):
        elt = GroupStackElement('group:nuxeo')
        self.assertEqual(elt(), 'group:nuxeo')

        self.assertEqual(str(elt), 'group:nuxeo')
        self.assert_('group:nuxeo' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'group:nuxeo')
        self.assertEqual(elt.getPrefix(), 'group')

        self.assertEqual(elt.getHiddenMetaType(), 'Hidden Group Stack Element')

        self.assertEqual(elt.holdsUser('anguenot', FakeAclUsers()), True)
        self.assertEqual(elt.holdsUser('anguenoteuh', FakeAclUsers()), False)

        # test with other groups
        elt = GroupStackElement('group:empty')
        self.assertEqual(elt.holdsUser('anguenot', FakeAclUsers()), False)
        elt = GroupStackElement('group:truc')
        self.assertEqual(elt.holdsUser('anguenot', FakeAclUsers()), False)

    def test_GroupStackElementCopy(self):
        elt = GroupStackElement('group:nuxeo')
        copy = elt.getCopy()
        # Try changing one attr and check
        copy.id = 'other'
        self.assertNotEqual(elt.getId(), copy.getId())

    def test_HiddenUserStackElement(self):
        elt = HiddenUserStackElement('fake')
        self.assertEqual(elt(),  USER_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(str(elt),  USER_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(elt.getIdForRoleSettings(), '')


class TestStackElementWithData(unittest.TestCase):

    def test_interface(self):
        from zope.interface.verify import verifyClass
        verifyClass(IStackElement, StackElementWithData)

    def test_getPrefix(self):
        stack_elt = StackElementWithData('fake')
        self.assertEquals(stack_elt.getPrefix(), '')

    def test_getIdWithoutPrefix(self):
        stack_elt = StackElementWithData('fake')
        self.assertEquals(stack_elt.getIdWithoutPrefix(), 'fake')

    def test_getHiddenMetaType(self):
        stack_elt = StackElementWithData('fake')
        self.assertEquals(stack_elt.getHiddenMetaType(), '')

    def test_creation(self):
        kw = {
            'title': 'My fake element',
            'element_state': 'acknowledged',
            }
        stack_elt = StackElementWithData('fake', **kw)
        # test __call__
        kw.update({'id': 'fake'})
        self.assertEquals(stack_elt(), kw)

    def test_data_api(self):
        kw = {
            'title': 'My fake element',
            'element_state': 'acknowledged',
            }
        stack_elt = StackElementWithData('fake', **kw)
        self.assertEquals(stack_elt.getId(), 'fake')
        self.assertEquals(stack_elt.getData(), kw)
        self.assertEquals(stack_elt.get('title'), 'My fake element')
        self.assertEquals(stack_elt.get('titleuh'), None)
        self.assertEquals(stack_elt['title'], 'My fake element')
        self.assertRaises(KeyError,
                          stack_elt.__getitem__,
                          'titleuh')
        stack_elt['title'] = 'New title'
        self.assertEquals(stack_elt.get('title'), 'New title')

        new_kws = {
            'id': 'hahaha',
            'title': 'Other title',
            'element_state': 'new',
            'new_key': 'new value',
            }
        stack_elt.update(new_kws)
        # id has not changed
        self.assertEquals(stack_elt.getId(), 'fake')
        new_data = {
            'title': 'Other title',
            'element_state': 'new',
            'new_key': 'new value',
            }
        self.assertEquals(stack_elt.getData(), new_data)

        # set editable attributes, only title will be editable
        stack_elt._editable_attributes = ['title']
        new_kws = {
            'title': 'New title',
            'element_state': 'other',
            'foo': 'bar',
            }
        stack_elt.update(new_kws)
        self.assertEquals(stack_elt.getId(), 'fake')
        new_data = {
            'title': 'New title',
            'element_state': 'new',
            'new_key': 'new value',
            }
        self.assertEquals(stack_elt.getData(), new_data)

    def test_UserStackElementWithData(self):
        kw = {
            'title': 'User element',
            'element_state': 'acknowledged',
            }
        info = {
            'id': 'user_wdata:anguenot',
            'title': 'User element',
            'element_state': 'acknowledged',
            }
        elt = UserStackElementWithData('user_wdata:anguenot', **kw)
        self.assertEqual(elt(), info)
        self.assert_('user_wdata:anguenot' == elt)
        self.assertEqual(elt.getId(), 'user_wdata:anguenot')
        self.assertEqual(elt.getIdForRoleSettings(), 'anguenot')
        self.assertEqual(elt.getPrefix(), 'user_wdata')
        self.assertEqual(elt.getData(), kw)

        self.assertEqual(elt.getHiddenMetaType(), 'Hidden User Stack Element')

        self.assertEqual(elt.holdsUser('anguenot'), True)
        self.assertEqual(elt.holdsUser('anguenoteuh'), False)

    def test_UserStackElementWithDataCopy(self):
        # test copy
        kw = {
            'title': 'Fake title',
            'element_state': 'acknowledged',
            }
        elt = UserStackElementWithData('fake', **kw)
        self.assertEquals(elt.get('title'), 'Fake title')
        copy = elt.getCopy()
        self.assertEquals(copy.get('title'), 'Fake title')
        copy['title'] = 'New title'
        self.assertEquals(elt.get('title'), 'Fake title')
        self.assertEquals(copy.get('title'), 'New title')

    def test_GroupStackElementWithData(self):
        kw = {
            'title': 'Group element',
            'element_state': 'acknowledged',
            }
        info = {
            'id': 'group_wdata:nuxeo',
            'title': 'Group element',
            'element_state': 'acknowledged',
            }
        elt = GroupStackElementWithData('group_wdata:nuxeo', **kw)
        self.assertEqual(elt(), info)
        self.assert_('group_wdata:nuxeo' == elt)
        self.assertEqual(elt.getId(), 'group_wdata:nuxeo')
        self.assertEqual(elt.getIdForRoleSettings(), 'group:nuxeo')
        self.assertEqual(elt.getPrefix(), 'group_wdata')
        self.assertEqual(elt.getHiddenMetaType(), 'Hidden Group Stack Element')
        self.assertEqual(elt.getData(), kw)

        self.assertEqual(elt.holdsUser('anguenot', FakeAclUsers()), True)
        self.assertEqual(elt.holdsUser('anguenoteuh', FakeAclUsers()), False)

        # test with other groups
        elt = GroupStackElement('group_wdata:empty')
        self.assertEqual(elt.holdsUser('anguenot', FakeAclUsers()), False)
        elt = GroupStackElement('group_wdata:truc')
        self.assertEqual(elt.holdsUser('anguenot', FakeAclUsers()), False)


class TestHiddenStackElements(unittest.TestCase):

    def test_HiddenUserStackElementCopy(self):
        elt = HiddenUserStackElement('user:anguenot')
        copy = elt.getCopy()
        # Try changing one attr and check
        copy.id = 'other'
        self.assertNotEqual(elt.getId(), copy.getId())

    def test_HiddenGroupStackElement(self):
        elt = HiddenGroupStackElement('fake')
        self.assertEqual(elt(),  GROUP_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(str(elt),  GROUP_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(elt.getIdForRoleSettings(), '')

    def test_HiddeGroupStackElementCopy(self):
        elt = HiddenGroupStackElement('group:nuxeo')
        copy = elt.getCopy()
        # Try changing one attr and check
        copy.id = 'other'
        self.assertNotEqual(elt.getId(), copy.getId())


class TestSubstituteStackElements(unittest.TestCase):

    def test_UserSubstituteStackElement(self):
        elt = UserSubstituteStackElement('user_substitute:anguenot')
        self.assertEqual(elt(), 'user_substitute:anguenot')
        self.assertEqual(str(elt), 'user_substitute:anguenot')
        self.assert_('user_substitute:anguenot' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'anguenot')
        self.assertEqual(elt.getPrefix(), 'user_substitute')

        self.assertEqual(elt.getHiddenMetaType(), 'Hidden User Stack Element')

    def test_UserSustituteStackElementCopy(self):
        elt = UserSubstituteStackElement('user_substitute:user:anguenot')
        copy = elt.getCopy()
        # Try changing one attr and check
        copy.id = 'other'
        self.assertNotEqual(elt.getId(), copy.getId())

    def test_GroupSubstituteStackElement(self):
        elt = GroupSubstituteStackElement('group_substitute:nuxeo')
        self.assertEqual(elt(), 'group_substitute:nuxeo')
        self.assertEqual(str(elt), 'group_substitute:nuxeo')
        self.assert_('group_substitute:nuxeo' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'group:nuxeo')
        self.assertEqual(elt.getPrefix(), 'group_substitute')

        self.assertEqual(elt.getHiddenMetaType(), 'Hidden Group Stack Element')

    def test_GroupSustituteStackElementCopy(self):
        elt = GroupSubstituteStackElement('group_substitute:nuxeo')
        copy = elt.getCopy()
        # Try changing one attr and check
        copy.id = 'other'
        self.assertNotEqual(elt.getId(), copy.getId())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStackElement))
    suite.addTest(unittest.makeSuite(TestStackElementWithData))
    suite.addTest(unittest.makeSuite(TestBasicStackElements))
    suite.addTest(unittest.makeSuite(TestHiddenStackElements))
    suite.addTest(unittest.makeSuite(TestSubstituteStackElements))
    suite.addTest(doctest.DocFileTest('basicstackelements.py',
                                      package='Products.CPSWorkflow',
                                      optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS))
    return suite


if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
