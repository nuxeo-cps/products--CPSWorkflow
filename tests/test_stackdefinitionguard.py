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

from Products.CPSWorkflow.stackdefinitionguard import StackDefinitionGuard

class TestStackDefinitionGuard(ZopeTestCase):

    def test_BaseStackDefinitionGuard(self):

        #
        # Test the guard of the stack element
        #

        guard = StackDefinitionGuard()
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

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestStackDefinitionGuard)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
