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
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem

from stackdefinitionguard import StackDefinitionGuard as Guard

from interfaces import IStackElement

class StackElement(SimpleItem):
    """Stack Element

    All the user defined stack elements ho have to inherit from StackElement
    and override the following methodds :
        - __call__()
        - __str__()
        - __cmp__()
    """

    meta_type = 'Stack Element'
    prefix = ''

    __implements__ = (IStackElement,)

    security = ClassSecurityInfo()

    guard = None

    def __call__(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError

    def __cmp__(self, other):
        if isinstance(other, StackElement):
            return cmp(self(), other())
        elif isinstance(other, StringType):
            return cmp(self(), other)
        return 0

    def getGuard(self):
        """Return a temporarly guard instance
        """
        if self.guard is not None:
            return self.guard
        else:
            return Guard().__of__(self)

    def getGuardSummary(self):
        """Return a guard summary for display purpose
        """
        res = None
        if self.guard is not None:
            res = self.guard.getSummary()
        return res

InitializeClass(StackElement)
