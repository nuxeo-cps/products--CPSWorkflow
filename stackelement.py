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

A Stack ELement is stored within a stack.
"""

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem

from Products.DCWorkflow.Guard import Guard

from interfaces import IStackElement

class StackElement(SimpleItem):
    """Stack Element

    A Stack Element has a guard as attribut.
    """

    meta_type = 'Stack Element'

    __implements__ = (IStackElement,)

    security = ClassSecurityInfo()

    guard = None

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
