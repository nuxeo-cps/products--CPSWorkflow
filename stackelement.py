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
"""Stack Element

A Stack ELement is an element stored within a stack type.
"""

from types import StringType

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo, getSecurityManager
from Acquisition import aq_parent, aq_inner
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import getToolByName

from stackdefinitionguard import StackDefinitionGuard as Guard

from interfaces import IStackElement

class StackElement(SimpleItem):
    """Stack Element
    """

    meta_type = 'Stack Element'
    prefix = ''
    id = ''

    hidden_meta_type = ''

    __implements__ = (IStackElement,)

    security = ClassSecurityInfo()

    view_guard = None
    edit_guard = None

    def __init__(self, id):
	self.id = id

    #
    # PRIVATE
    #

    def __cmp__(self, other):
	if isinstance(other, StackElement):
	    return cmp(self.getId(), other())
	elif isinstance(other, StringType):
	    return cmp(self.getId(), other)
	return 0

    def __call__(self):
	return self.getId()

    def __str__(self):
	return self.getId()

    #
    # API
    #

    def getPrefix(self):
	"""Returns the prefix for this stack element
	"""
	return self.prefix

    def getIdWithoutPrefix(self):
	"""Return the group id without the 'group:' prefix
	"""
	return self()[len(self.getPrefix())+1:]

    def getHiddenMetaType(self):
	return self.hidden_meta_type

    #
    # SECURITY
    #

    def isVisible(self, sm, stack, context):
	"""Is the entry visible by the user

	returns a boolean
	"""

	# Standalone elt
	if stack is None or context is None:
	    return 1

	wftool = getToolByName(context, 'portal_workflow', None)
	if wftool is None:
	    # No workflow tool thus standalone
	    return 1

	# XXX CPS assumptions
	wf_def = wftool.getWorkflowsFor(context)[0]

	# First check if there's an override
	if self.getViewGuard():
	    return self.getViewGuard().check(sm, wf_def, context)

	# Evaluate the default guard for view of the stackdef within
	# the stack context
	else:
	    for k, v in wftool.getStacks(context).items():
		if v == stack:
		    stackdef = wftool.getStackDefinitionFor(context, k)
		    guard = stackdef.getViewStackElementGuard()
		    return guard.check(sm, wf_def, context)
	return 1

    def isEditable(self, sm, stack, context):
	"""Is the entry editable by the user

	returns a boolean
	"""

	# Standalone elt
	if stack is None or context is None:
	    return 1

	wftool = getToolByName(context, 'portal_workflow', None)
	if wftool is None:
	    # No workflow tool thus standalone
	    return 1

	# XXX CPS assumptions
	wf_def = wftool.getWorkflowsFor(context)[0]

	# First check if there's an override
	if self.getViewGuard():
	    return self.getViewGuard().check(sm, wf_def, context)

	# Evaluate the default guard for view of the stackdef within
	# the stack context
	else:
	    # XXX
	    for k, v in wftool.getStacks(context).items():
		if v == stack:
		    stackdef = wftool.getStackDefinitionFor(context, k)
		    guard = stackdef.getEditStackElementGuard()
		    return guard.check(sm, wf_def, context)
	return 1


    #
    # GUARDS
    #

    def getViewGuard(self):
	return self.view_guard

    def setViewGuard(self, guard_permissions='', guard_roles='',
		     guard_groups='', guard_expr=''):
	self.view_guard = Guard()
	_props = {'guard_permissions':guard_permissions,
		  'guard_roles':guard_roles,
		  'guard_groups':guard_groups,
		  'guard_expr':guard_expr,
		  }
	self.getViewGuard().changeFromProperties(_props)

    def getEditGuard(self):
	return self.edit_guard

    def setEditGuard(self, guard_permissions='', guard_roles='',
		     guard_groups='', guard_expr=''):
	self.edit_guard = Guard()
	_props = {'guard_permissions':guard_permissions,
		  'guard_roles':guard_roles,
		  'guard_groups':guard_groups,
		  'guard_expr':guard_expr,
		  }
	self.getEditGuard().changeFromProperties(_props)


InitializeClass(StackElement)
