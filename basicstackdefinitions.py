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

"""Basic stack definitions modules

This module contains basic stack definitions.

c.f : doc/stackdefinitions.txt
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from stackdefinition import StackDefinition
from stackregistries import WorkflowStackDefRegistry

from zope.interface import implements
from Products.CPSWorkflow.interfaces import IWorkflowStackDefinition


class SimpleStackDefinition(StackDefinition):
    """Simple Stack Definition
    """

    implements(IWorkflowStackDefinition)

    meta_type = 'Simple Stack Definition'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #
    # PRIVATE API
    # Overrides the not implemented method of Stack
    #

    def _getLocalRolesMapping(self, ds):
        """Give the local roles mapping for the member / group ids within the
        stack

        Simple case : all the member of the stack have the associated local
        role
        """

        mapping = {}

        # Prepare the ds
        ds = self._prepareStack(ds)

        # Build local role mapping, define local role for each stack element,
        # even if it's not visible to current user.
        for elt in ds._getStackContent():
            elt_id = elt.getIdForRoleSettings()
            for role_id in self.getManagedRoles():
                if self._getExpressionForRole(role_id, ds, level=None,
                                              elt=elt):
                    mapping[elt_id] = mapping.get(elt_id, ()) + (role_id,)

        return mapping

InitializeClass(SimpleStackDefinition)

###################################################
###################################################

class HierarchicalStackDefinition(StackDefinition):
    """Hierarchical Stack Definition
    """

    implements(IWorkflowStackDefinition)

    meta_type = 'Hierarchical Stack Definition'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    #
    # PRIVATE API
    # Overrides the not implemented method of Stack
    #

    def _getLocalRolesMapping(self, ds):
        """Give the local roles mapping for the member / group ids within the
        stack

        Simple case : all the member of the stack have the associated local
        role
        """

        mapping = {}

        # Prepare the ds
        ds = self._prepareStack(ds)

        # Build local role mapping, define local role for each stack element,
        # even if it's not visible to current user.
        stack_content = ds._getStackContent()
        for level, elts in stack_content.items():
            for elt in elts:
                elt_id = elt.getIdForRoleSettings()
                for role_id in self.getManagedRoles():
                    if self._getExpressionForRole(role_id, ds, level, elt):
                        mapping[elt_id] = mapping.get(elt_id, ()) + (role_id,)

        return mapping

    #
    # SPECIFIC PRIVATE API
    #

    def _doIncLevel(self, ds):
        """Increase the stack level
        """
        ds = self._prepareStack(ds)
        ds.doIncLevel()
        ds = ds.getCopy()
        return ds

    def _doDecLevel(self, ds):
        """Decrease the stack level
        """
        ds = self._prepareStack(ds)
        ds.doDecLevel()
        ds = ds.getCopy()
        return ds

InitializeClass(HierarchicalStackDefinition)

#####################################################################
#####################################################################

WorkflowStackDefRegistry.register(SimpleStackDefinition)
WorkflowStackDefRegistry.register(HierarchicalStackDefinition)
