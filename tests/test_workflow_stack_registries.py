# (c) 2003 Nuxeo SARL <http://nuxeo.com>
# $Id$

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

portal_name = 'test_portal'
ZopeTestCase.installProduct('CMFCore')
ZopeTestCase.installProduct('CMFDefault')
ZopeTestCase.installProduct('MailHost')
ZopeTestCase.installProduct('CPSWorkflow')

from Products.CMFDefault.Portal import manage_addCMFSite

from Products.CMFCore.utils import getToolByName

from Products.CPSWorkflow.stackregistries import \
     WorkflowStackRegistryCls, WorkflowStackDefRegistryCls, \
     WorkflowStackRegistry, WorkflowStackDefRegistry

from Products.CPSWorkflow.basicstacks import SimpleStack, \
     HierarchicalStack

from Products.CPSWorkflow.basicstackdefinitions import \
     SimpleWorkflowStackDefinition, HierarchicalWorkflowStackDefinition

from Products.CPSWorkflow.interfaces.IWorkflowStackRegistry import \
     IWorkflowStackRegistry
from Products.CPSWorkflow.interfaces.IWorkflowStackDefRegistry import \
     IWorkflowStackDefRegistry

from Interface.Verify import verifyClass

class WorkflowStackRegistryTestCase(ZopeTestCase.PortalTestCase):
    """Workflow Stack Registry test case
    """

    def getPortal(self):
        if not hasattr(self.app, portal_name):
            manage_addCMFSite(self.app, portal_name)
        return self.app[portal_name]

    def test_interfaces(self):
        verifyClass(IWorkflowStackRegistry, WorkflowStackRegistryCls)
        verifyClass(IWorkflowStackDefRegistry, WorkflowStackDefRegistryCls)

    def test_stack_registry_cls_types(self):
        self.assert_(isinstance(WorkflowStackRegistry,
                                WorkflowStackRegistryCls,
                                ))
        self.assert_(isinstance(WorkflowStackDefRegistry,
                                WorkflowStackDefRegistryCls,
                                ))

    def test_stack_registry(self):

        #
        # Test the stack registry with the stack types defined within
        # the CPSWorkflowStacks
        #

        # Reset registries for being able to test behaviors
        stack_reg_save = WorkflowStackRegistry._stack_classes
        WorkflowStackRegistry._stack_classes = {}

        self.assertEqual(WorkflowStackRegistry.listWorkflowStackTypes(),
                         [])
        self.assertEqual(WorkflowStackRegistry.register(SimpleStack),
                         1)
        self.assertEqual(WorkflowStackRegistry.listWorkflowStackTypes(),
                         ['Simple Stack'])

        # Not possible to duplicate registration
        self.assertEqual(WorkflowStackRegistry.register(SimpleStack),
                         0)
        self.assertEqual(WorkflowStackRegistry.listWorkflowStackTypes(),
                         ['Simple Stack'])

        # Test registry API with Simple Stack
        self.assertEqual(WorkflowStackRegistry.getClass('Simple Stack'),
                         SimpleStack)
        self.assertEqual(WorkflowStackRegistry.getClass('Fake Stack'), None)

        icls = WorkflowStackRegistry.makeWorkflowStackTypeInstance(
            'Simple Stack')
        self.assert_(isinstance(icls, SimpleStack))

        #
        # Now test with Hierarchical Stack
        #

        self.assertEqual(WorkflowStackRegistry.listWorkflowStackTypes(),
                         ['Simple Stack'])

        # Test registry API with Hierarchical Stack
        self.assertEqual(WorkflowStackRegistry.register(HierarchicalStack),
                         1)
        self.assertEqual(WorkflowStackRegistry.listWorkflowStackTypes(),
                         ['Hierarchical Stack', 'Simple Stack'])

        # Test duplication again
        self.assertEqual(WorkflowStackRegistry.register(HierarchicalStack),
                         0)
        self.assertEqual(WorkflowStackRegistry.listWorkflowStackTypes(),
                         ['Hierarchical Stack', 'Simple Stack'])

        # Test registry API with Hierarchical  Stack
        self.assertEqual(WorkflowStackRegistry.getClass('Hierarchical Stack'),
                         HierarchicalStack)

        icls = WorkflowStackRegistry.makeWorkflowStackTypeInstance(
            'Hierarchical Stack')
        self.assert_(isinstance(icls, HierarchicalStack))

        # test instance creation with a not registered type
        icls = WorkflowStackRegistry.makeWorkflowStackTypeInstance(
            'Fake Stack Type')
        self.assert_(icls is None)

        icls = WorkflowStackRegistry.makeWorkflowStackTypeInstance(
            '')
        self.assert_(icls is None)

        # Recover old value
        WorkflowStackRegistry._stack_classes = stack_reg_save

    def test_stack_def_registry(self):

        #
        # Test the stack def registry with the stack types defined within
        # the CPSWorkflowStacks
        #

        # Reset the reg for being able to test the behavior
        stackdef_reg_save = WorkflowStackDefRegistry._stack_def_classes
        WorkflowStackDefRegistry._stack_def_classes = {}

        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         [])
        self.assertEqual(WorkflowStackDefRegistry.register(
            SimpleWorkflowStackDefinition), 1)
        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         ['Simple Workflow Stack Definition'])

        # Not possible to duplicate registration
        self.assertEqual(WorkflowStackDefRegistry.register(
            SimpleWorkflowStackDefinition), 0)
        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         ['Simple Workflow Stack Definition'])

        # Test registry API with Simple Stack
        self.assertEqual(WorkflowStackDefRegistry.getClass(
            'Simple Workflow Stack Definition'), SimpleWorkflowStackDefinition)
        self.assertEqual(WorkflowStackDefRegistry.getClass('Fake Stack'), None)

        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            'Simple Workflow Stack Definition', 'Simple Stack', 'Pilot')
        self.assert_(isinstance(icls, SimpleWorkflowStackDefinition))

        #
        # Now test with Hierarchical Stack
        #

        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         ['Simple Workflow Stack Definition'])

        # Test registry API with Hierarchical Stack
        self.assertEqual(WorkflowStackDefRegistry.register(
            HierarchicalWorkflowStackDefinition), 1)
        self.assert_('Hierarchical Workflow Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_('Simple Workflow Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_(len(WorkflowStackDefRegistry.listWorkflowStackDefTypes()) == 2)

        # Test duplication again
        self.assertEqual(WorkflowStackDefRegistry.register(
            HierarchicalWorkflowStackDefinition), 0)
        self.assert_('Hierarchical Workflow Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_('Simple Workflow Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_(len(WorkflowStackDefRegistry.listWorkflowStackDefTypes()) == 2)

        # Test registry API with Hierarchical  Stack
        self.assertEqual(WorkflowStackDefRegistry.getClass(
            'Hierarchical Workflow Stack Definition'),
                         HierarchicalWorkflowStackDefinition)

        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            'Hierarchical Workflow Stack Definition', 'Hierarchical Stack',
            'Pilot')
        self.assert_(isinstance(icls, HierarchicalWorkflowStackDefinition))

        # test instance creation with a not registered type
        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            'Fake Stack Type', 'XXX type', 'Associates')
        self.assert_(icls is None)

        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            '', '', '')
        self.assert_(icls is None)

        # Recover back the value
        WorkflowStackDefRegistry._stack_def_classes = stackdef_reg_save

if __name__ == '__main__':
    framework()
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(WorkflowStackRegistryTestCase))
        return suite
