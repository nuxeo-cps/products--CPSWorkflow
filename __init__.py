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

from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFCore.utils import ToolInit

import workflow
import workflowtool
import expression
import transitions
import states

import basicstacks
import basicstackdefinitions
import stackregistries
import stackelement

from configuration import Configuration
from configuration import addConfiguration

tools = (
    workflowtool.WorkflowTool,
    )

def initialize(registrar):
    # Workflow Configuration Object
    registrar.registerClass(
        Configuration,
        permission=ManagePortal,
        constructors=(addConfiguration,)
        )
    # Workflow Tool
    ToolInit(
        'CPS Workflow Tools',
        tools=tools,
        product_name='CPSWorkflow',
        icon='tool.png',
        ).initialize(registrar)
