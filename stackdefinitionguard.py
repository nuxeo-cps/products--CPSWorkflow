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

"""Stack definition guard

DCWorkflow guard with extended namespace
"""

from Globals import InitializeClass

from Products.DCWorkflow.Guard import Guard
from Products.DCWorkflow.Guard import formatNameUnion
from Products.DCWorkflow.permissions import ManagePortal

from Products.CMFCore.utils import _checkPermission

from expression import CPSStateChangeInfo
from expression import createExprContext

class StackDefinitionGuard(Guard):

    def check(self, sm, wf_def, ob):
        """Checks conditions in this guard.
        """
        u_roles = None
        if wf_def is not None:
            if wf_def.manager_bypass:
                # Possibly bypass.
                u_roles = sm.getUser().getRolesInContext(ob)
                if 'Manager' in u_roles:
                    return 1
        if self.permissions:
            for p in self.permissions:
                if _checkPermission(p, ob):
                    break
            else:
                return 0
        if self.roles:
            # Require at least one of the given roles.
            if u_roles is None:
                u_roles = sm.getUser().getRolesInContext(ob)
            for role in self.roles:
                if role in u_roles:
                    break
            else:
                return 0
        if self.groups:
            # Require at least one of the specified groups.
            u = sm.getUser()
            b = aq_base( u )
            if hasattr( b, 'getGroupsInContext' ):
                u_groups = u.getGroupsInContext( ob )
            elif hasattr( b, 'getGroups' ):
                u_groups = u.getGroups()
            else:
                u_groups = ()
            for group in self.groups:
                if group in u_groups:
                    break
            else:
                return 0
        expr = self.expr
        if expr is not None:
            if wf_def is not None:
                econtext = createExprContext(CPSStateChangeInfo(ob, wf_def))
                res = expr(econtext)
                if not res:
                    return 0
        return 1
    
InitializeClass(StackDefinitionGuard)
