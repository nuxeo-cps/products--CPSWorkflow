# -*- coding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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

"""Workflow Stack Element Registry interface

This module contains the interface for the workflow stack element registry
classes
"""

import Interface

class IWorkflowStackElementRegistry(Interface.Base):
    """API for the Workflow Stack Element Registries
    """
    def register(cls=None):
        """Register a class for a stack type
        """

    def listWorkflowStackElementTypes():
        """Return the list of workflow stack element types
        """

    def makeWorkflowStackElementTypeInstance(stack_elt_type, elt_str, **kw):
        """Factory to make a workflow s tack type instancec of the given
        workflow stack elt type with id = <id>
        """

    def getClass(stack_elt_type):
        """Get the instance class for a workflow stack of the given type
        """
