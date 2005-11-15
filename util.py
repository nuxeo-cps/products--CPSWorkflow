# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel <og@nuxeo.com>
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

"""Utilities for CPSWorkflow
"""

from AccessControl import ModuleSecurityInfo
from DateTime import DateTime


def updateEffectiveDate(proxy):
    """Set effective_date of published proxies to 'now' if not already set to
    some date.

    This won't trigger the creation of a new version even though published
    documents are frozen by the workflow.

    This function should be called by a workflow script on publishing
    transitions.
    """
    did_update = False
    for lang in proxy.getLanguageRevisions():
        doc = proxy.getContent(lang=lang)
        if getattr(doc, 'effective_date', None) is None:
            doc.effective_date = DateTime()
            did_update = True
    if did_update:
        proxy.proxyChanged()

ModuleSecurityInfo('Products.CPSWorkflow.util').declarePublic(
        'updateEffectiveDate')

