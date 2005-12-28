# -*- coding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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

""" CPS Workflow Stack Registries and Registry Tool
"""

from zLOG import LOG, INFO

from zope.interface import implements
from zope.interface.verify import verifyClass, DoesNotImplement
from Products.CPSWorkflow.interfaces import IStackElement
from Products.CPSWorkflow.interfaces import IWorkflowStack
from Products.CPSWorkflow.interfaces import IWorkflowStackDefinition
from Products.CPSWorkflow.interfaces import IWorkflowStackRegistry
from Products.CPSWorkflow.interfaces import IWorkflowStackDefRegistry
from Products.CPSWorkflow.interfaces import IWorkflowStackElementRegistry


class WorkflowStackRegistryCls(object):
    """Registry of the available stack types
    """

    implements(IWorkflowStackRegistry)

    def __init__(self):
        self._stack_classes = {}

    def register(self, cls=None):
        """Register a class for a stack type
        """
        if cls is not None:
            try:
                verifyClass(IWorkflowStack, cls)
            except DoesNotImplement:
                LOG("WorkflowStackRegistry error : ", INFO,
                    "Cannot import class %s" %str(cls))
                raise
            else:
                meta_type = cls.meta_type
                if meta_type not in self.listWorkflowStackTypes():
                    self._stack_classes[meta_type] = cls
                    return 1
        return 0

    def listWorkflowStackTypes(self):
        """Return the list of workflow stack types
        """
        _types = self._stack_classes.keys()
        _types.sort()
        return _types

    def makeWorkflowStackTypeInstance(self, stack_type, **kw):
        """Factory to make a workflow stack type instancec of the given
        workflow stack type with id = <id>
        """
        if stack_type in self.listWorkflowStackTypes():
            return self._stack_classes[stack_type](**kw)
        return None

    def getClass(self, stack_type):
        """Get the instance class for a workflow stack of the given type
        """
        return self._stack_classes.get(stack_type)

###############################################################

class WorkflowStackDefRegistryCls(object):
    """Registry of the available stack def types
    """

    implements(IWorkflowStackDefRegistry)

    def __init__(self):
        self._stack_def_classes = {}

    def register(self, cls=None):
        """Register a class for a stack def type
        """
        if cls is not None:
            try:
                verifyClass(IWorkflowStackDefinition, cls)
            except DoesNotImplement:
                LOG("WorkflowStackDefRegistry error : ", INFO,
                    "Cannot import class %s" %str(cls))
                raise
            else:
                meta_type = cls.meta_type
                if meta_type not in self.listWorkflowStackDefTypes():
                    self._stack_def_classes[meta_type] = cls
                    return 1
        return 0

    def listWorkflowStackDefTypes(self):
        """Return the list of workflow stack def types
        """
        _types = self._stack_def_classes.keys()
        _types.sort()
        return _types

    def makeWorkflowStackDefTypeInstance(self, stack_def_type, stack_ds_type,
                                         wf_var_id, **kw):
        """Factory to make a workflow stack def type instance of the given
        workflow stack type with id = <id>
        """
        if stack_def_type in self.listWorkflowStackDefTypes():
            return self._stack_def_classes[stack_def_type](stack_ds_type,
                                                           wf_var_id,
                                                           **kw)
        return None

    def getClass(self, stack_def_type):
        """Get the instance class for a workflow stack def of the given type
        """
        return self._stack_def_classes.get(stack_def_type)

###############################################################

class WorkflowStackElementRegistryCls(object):
    """Registry of the available stack element types
    """

    implements(IWorkflowStackElementRegistry)

    def __init__(self):
        self._stack_element_classes = {}
        self._prefix_meta_types = {}

    def register(self, cls=None):
        """Register a class for a stack element type
        """
        if cls is not None:
            try:
                verifyClass(IStackElement, cls)
            except DoesNotImplement:
                LOG("WorkflowStackElementRegistry error : ", INFO,
                    "Cannot import class %s" %str(cls))
                raise
            else:
                meta_type = cls.meta_type
                prefix = cls.prefix
                if meta_type not in self.listWorkflowStackElementTypes():
                    self._stack_element_classes[meta_type] = cls
                    self._prefix_meta_types[prefix] = meta_type
                    return 1
        return 0

    def listWorkflowStackElementTypes(self):
        """Return the list of workflow stack elt types
        """
        _types = self._stack_element_classes.keys()
        _types.sort()
        return _types

    def makeWorkflowStackElementTypeInstance(self, stack_elt_type,
                                             elt_str, **kw):
        """Factory to make a workflow stack element type instance of the given
        workflow stack type with id = <id>
        """
        if stack_elt_type in self.listWorkflowStackElementTypes():
            return self._stack_element_classes[stack_elt_type](elt_str, **kw)
        return None

    def getClass(self, stack_elt_type):
        """Get the instance class for a workflow stack elt of the given type
        """
        return self._stack_element_classes.get(stack_elt_type)

    def getMetaTypeForPrefix(self, prefix):
        """Returns the meta_type of the elements to construct giving a prefix
        """
        if prefix is not None:
            return self._prefix_meta_types.get(prefix)

###############################################################

WorkflowStackRegistry = WorkflowStackRegistryCls()
WorkflowStackDefRegistry = WorkflowStackDefRegistryCls()
WorkflowStackElementRegistry = WorkflowStackElementRegistryCls()
