# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
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
"""CPSWorkflow browser views.
"""

from Products.CPSUtil.browser import BaseAddView
from Products.CPSWorkflow.workflow import WorkflowDefinition

class CPSWorkflowDefinitionAddView(BaseAddView):
    """Add view for a CPSWorkflow.
    """
    _dir_name = 'workflows'
    description = u"A CPS Workflow."
    klass = WorkflowDefinition

    _id_attr = 'workflow_id'

    def _getFileName(self, file_id):
        return 'workflows/%s/definition.xml' % file_id
