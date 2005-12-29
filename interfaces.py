# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
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
"""CPS Workflow interfaces.
"""

from zope.interface import Interface

from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.interfaces import IWorkflowDefinition


class ICPSWorkflowTool(IWorkflowTool):
    """CPS workflow tool.
    """


class ICPSWorkflowDefinition(IWorkflowDefinition):
    """CPS workflow definition.
    """


class IWorkflowStackDefinition(Interface):
    """API for the Workflow Stack Definition
    """

    def getStackDataStructureType():
        """Get the id of the stack data structure the stack definition is
        holding
        """

    def getStackWorkflowVariableId():
        """Get the workflow variable id mapping this configuration
        """

    def _push(ds, **kw):
        """Push delegatees

        This method has to be implemented by a child class
        """

    def _pop(ds, **kw):
        """Pop delegatees

        This method has to be implemented by a child class
        """

    def _reset(ds, **kw):
        """Reset stack.

        ds contains the data structure.
        """

    ########################################################################

    def getManagedRoles():
        """Get all the roles tha stack can manage
        """

    def addManagedRole(role_id):
        """Add a role to to the list of local role
        """

    def delManagedRole(role_id):
        """Del a role to the list of local role
        """

    ########################################################################

    def _createExpressionNS(role_id, stack, level, elt):
        """Create an expression context for expression evaluation
        """

    def _addExpressionForRole(role_id, expresion):
        """Add a TALES expression for a given role
        """

    def _getExpressionForRole(role_id, stack, level=None, elt=None):
        """Compute the expression for a given role
        """

    #######################################################################

    def _getLocalRolesMapping(ds):
        """Give the local roles mapping for the member / group ids within the
        stack
        """

    #######################################################################

    def _canManageStack(ds, aclu, mtool, context, **kw):
        """Can the current member manage the stack?

        It will depend on the stack data structure.
        """

    def getManagerStackIds():
        """Get the ids of other stacks for which the people within those
        can manage this stackf

        For instance in the common use case members within the 'Pilots'
        stack can manage 'Associates' and 'Watchers' stacks.
        """


class IWorkflowStack(Interface):
    """API for the Workflow Stack
    """

    # Private

    def _getElementsContainer():
        """Return the stack elements container.

        This is PersistentList type
        """

    def _prepareElement(elt_str=None, **kw):
        """Prepare the element.

        Usual format : <prefix : id>
        Call the registry to construct an instance according to the prefix
        Check WorkflowStackElementRegistry
        """

    # Public

    def getMetaType():
        """Get the meta_type of the class.

        Needs to be public for non restricted code.
        """

    def getStackContent(type='str', **kw):
        """Get the actual content of the stack.

        It has to supports at least three types of returned values:
         - str
         - role
         - call
        """

    def push(elt=None):
        """Push elt in the queue.
        """

    def pop(pop_ids=[]):
        """Remove element in pop_ids from within the queue.
        """

    def reset(**kw):
        """Reset the stack
        """

    def getCopy():
        """Duplicate self.

        Returns a new object instance of the same type
        """

    def __deepcopy__(ob):
        """Deep copy.

        Just to call a clean API while calling getCopy().
        Copes with mutable attrs to break reference.
        """

    def render(context, mode, **kw):
        """Render in mode.
        """


class ISimpleWorkflowStack(Interface):
    """API for the Workflow Stack
    """

    def __deepcopy__(ob):
        """Deep copy.

        Just to call a clean API while calling getCopy().
        """

    def getStackContent():
        """Get the stack content.
        """

    def getCopy():
        """Duplicate self.

        Returns a new object instance of the same type.
        """


class IHierarchicalWorkflowStack(Interface):
    """API for the Hierarchical Workflow Stack
    """

    def __deepcopy__(ob):
        """Deep copy.

        Just to call a clean API while calling getCopy().
        """

    def getCurrentLevel():
        """Get the current level.
        """

    def doIncLevel():
        """Increment the level value.

        The level has to exist and host elts.
        """

    def doDecLevel():
        """Decrement the level value.

        The level has to exist and host elts.
        """

    def getLevelContent(level=None):
        """Get the content of the level given as parameter.

        If not specified let's return the current level content.
        """

    def getAllLevels():
        """Get all the existing levels with elts.

        Result is returned sorted.
        """


class IWorkflowStackRegistry(Interface):
    """API for the Workflow Stack Registries
    """
    def register(cls=None):
        """Register a class for a stack type.
        """

    def listWorkflowStackTypes():
        """Get the list of workflow stack types.
        """

    def makeWorkflowStackTypeInstance(stack_type, **kw):
        """Factory to make a workflow stack type instancec of the given
        workflow stack type with id = <id>.
        """

    def getClass(stack_type):
        """Get the instance class for a workflow stack of the given type.
        """


class IWorkflowStackDefRegistry(Interface):
    """API for the Workflow Stack Registries
    """
    def register(cls=None):
        """Register a class for a stack type.
        """

    def listWorkflowStackDefTypes():
        """Get the list of workflow stack types.
        """

    def makeWorkflowStackDefTypeInstance(stack_def_type, stack_ds_type,
          wf_var_id, **kw):
        """Factory to make a workflow stack def type instance of the given
        workflow stack type with id = <id>.
        """

    def getClass(stack_def_type):
        """Get the instance class for a workflow stack of the given type.
        """


class IWorkflowStackElementRegistry(Interface):
    """API for the Workflow Stack Element Registries
    """
    def register(cls=None):
        """Register a class for a stack type.
        """

    def listWorkflowStackElementTypes():
        """Get the list of workflow stack element types.
        """

    def makeWorkflowStackElementTypeInstance(stack_elt_type, elt_str, **kw):
        """Factory to make a workflow s tack type instancec of the given
        workflow stack elt type with id = <id>.
        """

    def getClass(stack_elt_type):
        """Get the instance class for a workflow stack of the given type.
        """


class IStackElement(Interface):
    """API for the Workflow Stack Element

    The stack element classes you may want to define and register within the
    WOrkflowStackElementRegistry *DO* have to inherit and implement this
    interface
    """

    def __call__():
        """Has to be overriden by the child.
        """

    def __str__():
        """Has to be overriden by the child.
        """

    def __cmp__(other):
        """Comparison can be done against another stack element or
        against a string.
        """
