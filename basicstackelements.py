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
"""Basic Stack Elements

This module contains the basic stack elements you may need within a CMF or CPS
site. It includes :

 - User Stack Element : a stack element that can be used to store a member.

 - Group Stack Element : a stack element that can be used to store a group.

 - User Substitute Stack Element : a stack element that can be used to store a
   user substitute.

 - Group Subsctitute Stack Element : a stack element that can be used to store
   a group substitute.

Each stack element *MUST* have a meta_type. It is compulsory to register you
new stack element within the WorkflowStackElementRegistry. Furthermore, it is a
quite practical way to introspect your stack element and to known what's the
nature of a given stack element.

"""

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from stackregistries import WorkflowStackElementRegistry

from stackelement import StackElement
from interfaces import IStackElement

class UserStackElement(StackElement):
    """User Stack Element

    Stack element you may use to store a member. It understand only the user
    id without prefix. (i.e : user_id = 'anguenot')

    You may use it like this :

        >>> use = UserStackElement('anguenot')
        >>> use()
        'anguenot'
        >>> str(use)
        'anguenot'
        >>> 'anguenot' == use
        True
    """
    meta_type = 'User Stack Element'

    __implement__ = (IStackElement,)

    user_id = ''

    def __init__(self, user_id):
        self.user_id = user_id

    def __call__(self):
        return self.user_id

    def __str__(self):
        return self.user_id

InitializeClass(UserStackElement)

class GroupStackElement(UserStackElement):
    """Group Stack Element

    Stack element you may use to store a group. It understand only the group
    id. The group id is stored with CPS group style conventiopn (i.e : group_id
    = 'group:nuxeo')

    You may use it like this :

        >>> gse = GroupStackElement('group:nuxeo')
        >>> gse()
        'group:nuxeo'
        >>> str(gse)
        'group:nuxeo'
        >>> 'group:nuxeo' == gse
        True

        >>> gse.getGroupIdWithoutPrefix()
        'nuxeo'
    """
    meta_type = 'Group Stack Element'

    __implement__ = (IStackElement,)

    group_prefix = 'group:'
    group_id = ''

    def __init__(self, group_id, prefix=''):
        self.group_id = group_id
        if prefix:
            self.group_prefix = 'group:'

    def __call__(self):
        return self.group_id

    def __str__(self):
        return self.group_id

    def _getGroupPrefix(self):
        return self.group_prefix

    def getGroupIdWithoutPrefix(self):
        """Return the group id without the 'group:' prefix
        """
        return self()[len(self._getGroupPrefix()):]

InitializeClass(GroupStackElement)

class UserSubstituteStackElement(UserStackElement):
    """User Substitute Stack Element
    """
    meta_type = 'User Substitute Stack Element'

    __implement__ = (IStackElement,)

    # XXX to implement

InitializeClass(UserSubstituteStackElement)

class GroupSubstituteStackElement(GroupStackElement):
    """Group Substitute Stack Element
    """
    meta_type = 'Group Substitute Stack Element'

    __implement__ = (IStackElement,)

    # XXX to implement

InitializeClass(GroupSubstituteStackElement)

##########################################################
##########################################################

WorkflowStackElementRegistry.register(UserStackElement)
WorkflowStackElementRegistry.register(GroupStackElement)
WorkflowStackElementRegistry.register(UserSubstituteStackElement)
WorkflowStackElementRegistry.register(GroupSubstituteStackElement)
