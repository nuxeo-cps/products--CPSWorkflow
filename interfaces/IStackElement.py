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

"""Workflow Stack Element interface
"""

import Interface

class IStackElement(Interface.Base):
    """API for the Workflow Stack Element

    The stack element classes you may want to define and register within the
    WOrkflowStackElementRegistry *DO* have to inherit and implement this
    interface
    """

    def __call__():
        """Has to be overriden by the child
        """

    def __str__():
        """Has to be overriden by the child
        """

    def __cmp__(other):
        """Comparaison can be done against another stack element or against a
        string """

    def getGuard():
        """Return a temporarly guard instance
        """

    def getGuardSummary():
        """Return a guard summary for display purpose
        """
