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
from Products.PageTemplates.TALES import CompilerError
from Interface.Verify import verifyClass

from Products.CPSWorkflow.stackelement import StackElement

from Products.CPSWorkflow.basicstackelements import UserStackElement
from Products.CPSWorkflow.basicstackelements import GroupStackElement
from Products.CPSWorkflow.basicstackelements import HiddenUserStackElement
from Products.CPSWorkflow.basicstackelements import HiddenGroupStackElement
from Products.CPSWorkflow.basicstackelements import UserSubstituteStackElement
from Products.CPSWorkflow.basicstackelements import GroupSubstituteStackElement
from Products.CPSWorkflow.basicstackelements import \
     USER_STACK_ELEMENT_NOT_VISIBLE, GROUP_STACK_ELEMENT_NOT_VISIBLE

from Products.CPSWorkflow.interfaces import IStackElement

class TestStackElements(ZopeTestCase):

    def test_interface(self):
        verifyClass(IStackElement, StackElement)

    def test_stack_element_guard(self):

        #
        # Test the guard of the stack element
        #

        stack_elt = StackElement()
        guard = stack_elt.getGuard()

        # XXX fix API
        stack_elt.guard = guard
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
        self.assertEqual(stack_elt.getGuardSummary(), summary)
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

        ##
        ## XXX need to test the check() API
        ##

    def test_UserStackElement(self):
        elt = UserStackElement('anguenot')
        self.assertEqual(elt(), 'anguenot')
        self.assertEqual(str(elt), 'anguenot')
        self.assert_('anguenot' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'anguenot')
        self.assertEqual(elt.getPrefix(), 'user')

    def test_GroupStackElement(self):
        elt = GroupStackElement('group:nuxeo')
        self.assertEqual(elt(), 'group:nuxeo')
        self.assertEqual(str(elt), 'group:nuxeo')
        self.assert_('group:nuxeo' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'group:nuxeo')
        self.assertEqual(elt.getPrefix(), 'group')

    def test_HiddenUserStackElement(self):
        elt = HiddenUserStackElement()
        self.assertEqual(elt(),  USER_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(str(elt),  USER_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(elt.getIdForRoleSettings(), '')

    def test_HiddenGroupStackElement(self):
        elt = HiddenGroupStackElement()
        self.assertEqual(elt(),  GROUP_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(str(elt),  GROUP_STACK_ELEMENT_NOT_VISIBLE)
        self.assertEqual(elt.getIdForRoleSettings(), '')

    def test_UserSubstituteStackElement(self):
        elt = UserSubstituteStackElement('user_substitute:anguenot')
        self.assertEqual(elt(), 'user_substitute:anguenot')
        self.assertEqual(str(elt), 'user_substitute:anguenot')
        self.assert_('user_substitute:anguenot' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'anguenot')
        self.assertEqual(elt.getPrefix(), 'user_substitute')
        
    def test_GroupSubstituteStackElement(self):
        elt = GroupSubstituteStackElement('group_substitute:group:nuxeo')
        self.assertEqual(elt(), 'group_substitute:group:nuxeo')
        self.assertEqual(str(elt), 'group_substitute:group:nuxeo')
        self.assert_('group_substitute:group:nuxeo' == elt)
        self.assertEqual(elt.getIdForRoleSettings(), 'group:nuxeo')
        self.assertEqual(elt.getPrefix(), 'group_substitute')

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestStackElements)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
