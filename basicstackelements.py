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

 - Hidden User Stack Element : a stack element used when a given user stack
   element is not visible

 - Hidden Group Stack Element : a stack element used when a given group stack
   element is not visible

Each stack element *MUST* have a meta_type and a prefix.  It is
compulsory to register you new stack element within the
WorkflowStackElementRegistry. Furthermore, it is a quite practical way
to introspect your stack element and to known what's the nature of a
given stack element.

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
    prefix = 'user'

    __implement__ = (IStackElement,)

    user_id = ''

    def __init__(self, user_id):
        self.user_id = user_id

    def __call__(self):
        return self.user_id

    def __str__(self):
        return self.user_id

    def getIdForRoleSettings(self):
        # XXX change this when no empty prefix are given anymore
        if self.user_id.startswith('user:'):
            return self.getIdWithoutPrefix()
        return self.user_id

InitializeClass(UserStackElement)

class GroupStackElement(UserStackElement):
    """Group Stack Element

    Stack element you may use to store a group. It understand only the group
    id. The group id is stored with CPS group style convention (i.e : group_id
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

    prefix = 'group'
    group_id = ''

    def __init__(self, group_id, prefix=''):
        self.group_id = group_id
        if prefix:
            self.prefix = 'group'

    def __call__(self):
        return self.group_id

    def __str__(self):
        return self.group_id

    def getIdForRoleSettings(self):
        return self.group_id

InitializeClass(GroupStackElement)

#########################################################################
#########################################################################

USER_STACK_ELEMENT_NOT_VISIBLE  = 'label_user_stack_element_not_visible'
GROUP_STACK_ELEMENT_NOT_VISIBLE = 'label_group_stack_element_not_visible'

class HiddenUserStackElement(UserStackElement):
    """Hidden User Stack Element

    Hidden User Stack Element is a stack element proposed to end users
    when this last doesn't have the view permissions on the element.

    Note, this is never stored within a stack element container.
    """
    meta_type = 'Hidden User Stack Element'
    prefix = 'hidden_user'
    
    __implement__ = (IStackElement,)

    def __init__(self):
        pass
    
    def __call__(self):
        return USER_STACK_ELEMENT_NOT_VISIBLE

    def __str__(self):
        return USER_STACK_ELEMENT_NOT_VISIBLE

    def getIdForRoleSettings(self):
        return ''

InitializeClass(HiddenUserStackElement)

class HiddenGroupStackElement(GroupStackElement):
    """Hidden Group Stack Element

    Hidden Group Stack Element is a stack element proposed to end users
    when this last doesn't have the view permissions on the element.

    Note, this is never stored within a stack element container.
    """
    meta_type = 'Hidden Group Stack Element'
    prefix = 'hidden_group'
    
    __implement__ = (IStackElement,)

    def __init__(self):
        pass

    def __call__(self):
        return GROUP_STACK_ELEMENT_NOT_VISIBLE

    def __str__(self):
        return GROUP_STACK_ELEMENT_NOT_VISIBLE

    def getGroupIdWithoutPrefix(self):
        """Return the group id without the 'group:' prefix
        """
        return GROUP_STACK_ELEMENT_NOT_VISIBLE

    def getIdForRoleSettings(self):
        return ''
    

InitializeClass(HiddenGroupStackElement)

#########################################################################
#########################################################################

class UserSubstituteStackElement(UserStackElement):
    """User Substitute Stack Element
    """
    meta_type = 'User Substitute Stack Element'
    prefix = 'user_substitute'

    __implement__ = (IStackElement,)
    
    def getIdForRoleSettings(self):
        return self.getIdWithoutPrefix()

InitializeClass(UserSubstituteStackElement)

class GroupSubstituteStackElement(GroupStackElement):
    """Group Substitute Stack Element
    """
    meta_type = 'Group Substitute Stack Element'
    prefix = 'group_substitute'

    __implement__ = (IStackElement,)

    prefix = 'group_substitute'

    def getIdForRoleSettings(self):
        return self.getIdWithoutPrefix()


InitializeClass(GroupSubstituteStackElement)

##########################################################
##########################################################

WorkflowStackElementRegistry.register(UserStackElement)
WorkflowStackElementRegistry.register(GroupStackElement)
WorkflowStackElementRegistry.register(UserSubstituteStackElement)
WorkflowStackElementRegistry.register(GroupSubstituteStackElement)
WorkflowStackElementRegistry.register(HiddenUserStackElement)
WorkflowStackElementRegistry.register(HiddenGroupStackElement)
