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
"""Bacis Stack Elements
"""

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from stackregistries import WorkflowStackElementRegistry

from stackelement import StackElement
from interfaces import IStackElement

class UserStackElement(StackElement):
    """User Stack Element
    """
    meta_type = 'User Stack Element'

InitializeClass(UserStackElement)

class GroupStackElement(UserStackElement):
    """Group Stack Element
    """
    meta_type = 'Group Stack Element'

InitializeClass(GroupStackElement)

class UserSubstituteStackElement(UserStackElement):
    """User Substitute Stack Element
    """
    meta_type = 'User Substitute Stack Element'

InitializeClass(UserSubstituteStackElement)

class GroupSubstituteStackElement(GroupStackElement):
    """Group Substitute Stack Element
    """
    meta_type = 'Group Substitute Stack Element'

InitializeClass(GroupSubstituteStackElement)

##########################################################
##########################################################

WorkflowStackElementRegistry.register(UserStackElement)
WorkflowStackElementRegistry.register(GroupStackElement)
WorkflowStackElementRegistry.register(UserSubstituteStackElement)
WorkflowStackElementRegistry.register(GroupSubstituteStackElement)
