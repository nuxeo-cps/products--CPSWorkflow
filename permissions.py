# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors: Julien Anguenot <ja@nuxeo.com>
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

""" CPS Workflow Permission

 - 'Manage workflows' is the permission needed to edit cps workflow
    configuration objects.

"""

from Products.CMFCore.permissions import setDefaultRoles

ManageWorkflows = 'Manage workflows'
setDefaultRoles(ManageWorkflows, ('Manager',))

# wftool will check 'View' too, so that it's not necessary (but possible) to
# have the wf control this permission
ViewStatusHistory = 'View status history'
setDefaultRoles(ViewStatusHistory, ('Member',))
