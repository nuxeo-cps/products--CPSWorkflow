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

from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCorePermissions import ManagePortal

from interfaces.IWorkflowStackRegistry import IWorkflowStackRegistry
from interfaces.IWorkflowStackDefRegistry import IWorkflowStackDefRegistry

class WorkflowStackRegistryCls:
    """Registry of the available stack types
    """

    __implements__ = (IWorkflowStackRegistry,)

    def __init__(self):
        self._stack_classes = {}

    def register(self, cls=None):
        """Register a class for a stack type
        """
        if cls is not None:
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

InitializeClass(WorkflowStackRegistryCls)

###############################################################
###############################################################

class WorkflowStackDefRegistryCls:
    """Registry of the available stack def types
    """

    __implements__ = (IWorkflowStackDefRegistry,)

    def __init__(self):
        self._stack_def_classes = {}

    def register(self, cls=None):
        """Register a class for a stack def type
        """
        if cls is not None:
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

InitializeClass(WorkflowStackDefRegistryCls)

###############################################################
###############################################################

WorkflowStackRegistry = WorkflowStackRegistryCls()
WorkflowStackDefRegistry = WorkflowStackDefRegistryCls()