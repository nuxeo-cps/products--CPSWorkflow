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
     WorkflowStackRegistryCls, WorkflowStackRegistry
from Products.CPSWorkflow.stackregistries import \
     WorkflowStackDefRegistryCls, WorkflowStackDefRegistry
from Products.CPSWorkflow.stackregistries import \
     WorkflowStackElementRegistry, WorkflowStackElementRegistryCls

from Products.CPSWorkflow.basicstacks import SimpleStack, \
     HierarchicalStack

from Products.CPSWorkflow.basicstackdefinitions import \
     SimpleStackDefinition, HierarchicalStackDefinition

from Products.CPSWorkflow.basicstackelements import \
     UserStackElement, GroupStackElement, UserSubstituteStackElement, \
     GroupSubstituteStackElement

from Products.CPSWorkflow.interfaces import IWorkflowStackRegistry
from Products.CPSWorkflow.interfaces import IWorkflowStackDefRegistry
from Products.CPSWorkflow.interfaces import IWorkflowStackElementRegistry

from Interface.Verify import verifyClass, DoesNotImplement

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
        verifyClass(IWorkflowStackElementRegistry,
                    WorkflowStackElementRegistryCls)

    def test_stack_registry_cls_types(self):
        self.assert_(isinstance(WorkflowStackRegistry,
                                WorkflowStackRegistryCls,
                                ))
        self.assert_(isinstance(WorkflowStackDefRegistry,
                                WorkflowStackDefRegistryCls,
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
            SimpleStackDefinition), 1)
        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         ['Simple Stack Definition'])

        # Not possible to duplicate registration
        self.assertEqual(WorkflowStackDefRegistry.register(
            SimpleStackDefinition), 0)
        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         ['Simple Stack Definition'])

        # Test registry API with Simple Stack
        self.assertEqual(WorkflowStackDefRegistry.getClass(
            'Simple Stack Definition'), SimpleStackDefinition)
        self.assertEqual(WorkflowStackDefRegistry.getClass('Fake Stack'), None)

        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            'Simple Stack Definition', 'Simple Stack', 'Pilot')
        self.assert_(isinstance(icls, SimpleStackDefinition))

        #
        # Now test with Hierarchical Stack
        #

        self.assertEqual(WorkflowStackDefRegistry.listWorkflowStackDefTypes(),
                         ['Simple Stack Definition'])

        # Test registry API with Hierarchical Stack
        self.assertEqual(WorkflowStackDefRegistry.register(
            HierarchicalStackDefinition), 1)
        self.assert_('Hierarchical Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_('Simple Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_(len(WorkflowStackDefRegistry.listWorkflowStackDefTypes()) == 2)

        # Test duplication again
        self.assertEqual(WorkflowStackDefRegistry.register(
            HierarchicalStackDefinition), 0)
        self.assert_('Hierarchical Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_('Simple Stack Definition' in
                     WorkflowStackDefRegistry.listWorkflowStackDefTypes())
        self.assert_(len(WorkflowStackDefRegistry.listWorkflowStackDefTypes()) == 2)

        # Test registry API with Hierarchical  Stack
        self.assertEqual(WorkflowStackDefRegistry.getClass(
            'Hierarchical Stack Definition'),
                         HierarchicalStackDefinition)

        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            'Hierarchical Stack Definition', 'Hierarchical Stack',
            'Pilot')
        self.assert_(isinstance(icls, HierarchicalStackDefinition))

        # test instance creation with a not registered type
        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            'Fake Stack Type', 'XXX type', 'Associates')
        self.assert_(icls is None)

        icls = WorkflowStackDefRegistry.makeWorkflowStackDefTypeInstance(
            '', '', '')
        self.assert_(icls is None)

        # Recover back the value
        WorkflowStackDefRegistry._stack_def_classes = stackdef_reg_save

    def test_stack_element_registry(self):

        #
        # Test the stack element registry with the stack types defined within
        # the CPSWorkflowStacks
        #

        # Reset registries for being able to test behaviors
        stack_reg_save = WorkflowStackElementRegistry._stack_element_classes
        WorkflowStackElementRegistry._stack_element_classes = {}

        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),[])
        self.assertEqual(
            WorkflowStackElementRegistry.register(UserStackElement),
            1)
        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['User Stack Element'])

        # Not possible to duplicate registration
        self.assertEqual(
            WorkflowStackElementRegistry.register(UserStackElement),
            0)
        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['User Stack Element'])

        # Test registry API with User Stack Element
        self.assertEqual(
            WorkflowStackElementRegistry.getClass('User Stack Element'),
            UserStackElement)
        self.assertEqual(
            WorkflowStackElementRegistry.getClass('Fake Stack Element'),
            None)

        icls = WorkflowStackElementRegistry.makeWorkflowStackElementTypeInstance('User Stack Element', 'toto')
        self.assert_(isinstance(icls, UserStackElement))

        #
        # Now test with GroupStackElement
        #

        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['User Stack Element'])

        self.assertEqual(
            WorkflowStackElementRegistry.register(GroupStackElement),
            1)
        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['Group Stack Element', 'User Stack Element'])

        # Test duplication again
        self.assertEqual(
            WorkflowStackElementRegistry.register(GroupStackElement),
            0)
        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['Group Stack Element', 'User Stack Element'])

        # Test registry API with Group Stack Element
        self.assertEqual(
            WorkflowStackElementRegistry.getClass('Group Stack Element'),
            GroupStackElement)

        icls = WorkflowStackElementRegistry.makeWorkflowStackElementTypeInstance('Group Stack Element', 'group:titi')
        self.assert_(isinstance(icls, GroupStackElement))

        #
        # Now test with UserSubstituteStackElement
        #

        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['Group Stack Element', 'User Stack Element'])

        self.assertEqual(
            WorkflowStackElementRegistry.register(UserSubstituteStackElement),
            1)
        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['Group Stack Element', 'User Stack Element',
             'User Substitute Stack Element',])

        # Test registry API with Group Stack Element
        self.assertEqual(
            WorkflowStackElementRegistry.getClass(
            'User Substitute Stack Element'),
            UserSubstituteStackElement)

        icls = WorkflowStackElementRegistry.makeWorkflowStackElementTypeInstance('User Substitute Stack Element', 'user')
        self.assert_(isinstance(icls, UserSubstituteStackElement))

        #
        # Now test with GroupSubstituteStackElement
        #

        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['Group Stack Element', 'User Stack Element',
             'User Substitute Stack Element',])

        self.assertEqual(
            WorkflowStackElementRegistry.register(GroupSubstituteStackElement),
            1)
        self.assertEqual(
            WorkflowStackElementRegistry.listWorkflowStackElementTypes(),
            ['Group Stack Element',
             'Group Substitute Stack Element',
             'User Stack Element',
             'User Substitute Stack Element',])

        # Test registry API with Group Stack Element
        self.assertEqual(
            WorkflowStackElementRegistry.getClass(
            'Group Substitute Stack Element'),
            GroupSubstituteStackElement)

        icls = WorkflowStackElementRegistry.makeWorkflowStackElementTypeInstance('Group Substitute Stack Element', 'group:titi')
        self.assert_(isinstance(icls, GroupSubstituteStackElement))

        # test instance creation with a not registered type
        icls = WorkflowStackElementRegistry.makeWorkflowStackElementTypeInstance('Fake Stack Element', 'xx')
        self.assert_(icls is None)

        icls = WorkflowStackElementRegistry.makeWorkflowStackElementTypeInstance('', '')
        self.assert_(icls is None)

        # Recover old value
        WorkflowStackElementRegistry._stack_element_classes = stack_reg_save

    def test_stack_registry_interface_check(self):

        #
        # Here, we will try to register a stack that is not implementing the
        # base interface
        #

        class FakeStack:
            meta_type = 'Fake Stack'

        self.assertRaises(DoesNotImplement,
                          WorkflowStackRegistry.register, FakeStack)
        self.assert_(
            'Fake Stack' not in
            WorkflowStackRegistry.listWorkflowStackTypes())

    def test_stackdef_registry_interface_check(self):

        #
        # Here, we will try to register a stackdef that is not implementing the
        # base interface
        #

        class FakeStackDef:
            meta_type = 'Fake Stack Def'

        self.assertRaises(DoesNotImplement,
                          WorkflowStackDefRegistry.register,
                          FakeStackDef)
        self.assert_(
            'Fake Stack Def' not in
            WorkflowStackRegistry.listWorkflowStackTypes())

    def test_stackelt_registry_interface_check(self):

        #
        # Here, we will try to register a stackelt that is not implementing the
        # base interface
        #

        class FakeStackElement:
            meta_type = 'Fake Stack Element'

        self.assertRaises(DoesNotImplement,
                          WorkflowStackElementRegistry.register,
                          FakeStackElement)
        self.assert_(
            'Fake Stack Element' not in
            WorkflowStackElementRegistry.listWorkflowStackElementTypes())


if __name__ == '__main__':
    framework()
else:
    from unittest import TestSuite, makeSuite
    def test_suite():
        suite = TestSuite()
        suite.addTest(makeSuite(WorkflowStackRegistryTestCase))
        return suite
