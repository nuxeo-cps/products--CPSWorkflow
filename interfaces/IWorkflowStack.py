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

"""Workflow Stack interface

This module contains the interface for the WorkflowStack class
"""

import Interface

class IWorkflowStack(Interface.Base):
    """API for the Workflow Stack
    """

    #
    # PRIVATE
    #

    def _getElementsContainer():
        """Returns the stack elements container
        
        This is PersistentList type
        """

    def _prepareElement(elt_str=None, **kw):
        """Prepare the element.
        
        Usual format : <prefix : id>
        Call the registry to construct an instance according to the prefix
        Check WorkflowStackElementRegistry
        """

    #
    # PUBLIC
    #

    def getMetaType():
        """Returns the meta_type of the class

        Needs to be public for non restricted code
        """

    def getStackContent(type='str', **kw):
        """Return the actual content of the stack.

        It has to supports at least three types of returned values:

         + str
         + role
         + call
        """

    def push(elt=None):
        """Push elt in the queue
        """
    
    def pop(elt=None):
        """Remove elt from within the queue
        
        If elt is None then remove the last one
        """

    def reset(**kw):
        """Reset the stack
        """

    def getCopy():
        """Duplicate self

        Return a new object instance of the same type
        """

    def __deepcopy__(ob):
        """Deep copy. Just to call a clean API while calling getCopy()
        
        Cope with mutable attrs to break reference
        """
    
    def render(context, mode, **kw):
        """Render in mode
        """
