# -*- coding: iso-8859-15 -*-
import unittest
from Testing.ZopeTestCase import ZopeTestCase
from Products.PageTemplates.TALES import CompilerError
from Interface.Verify import verifyClass

from Products.CPSWorkflow.stackelement import StackElement

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

def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestStackElements)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
