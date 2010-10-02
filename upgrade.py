# (C) Copyright 2010 Georges Racinet
# Author: Georges Racinet <georges@racinet.fr>
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

import logging

import transaction
from Products.CPSUtil.text import upgrade_string_unicode
from Products.CPSCore.ProxyBase import (walk_cps_except_folders,
                                        walk_cps_proxies,
                                        )
from Products.CPSCore.interfaces import ICPSProxy

logger = logging.getLogger(__name__)

def upgrade_unicode_for(proxy):
    """Upgrade workflow history for proxy."""

    for transitions in proxy.workflow_history.values():
        for trans in transitions:
            c = trans.get('comments')
            if c is not None:
                trans['comments'] = upgrade_string_unicode(c)
    return True

def upgrade_unicode_in(folder, counters=None, walk_folders=False):
    """Upgrade workflow comments for proxies in this folder.

    If not walk_folders, descends in folderish documents, but not in folders
    """
    logger.debug("Entering folder %s", folder)
    if counters is None:
        counters = dict(done=0, total=0)

    if ICPSProxy.providedBy(folder): # could be portal
        counters['total'] += 1
        if upgrade_unicode_for(folder):
            counters['done'] += 1

    walk = walk_folders and walk_cps_proxies or walk_cps_except_folders
    for p in walk(folder):
        counters['total'] += 1
        if upgrade_unicode_for(p):
            counters['done'] += 1
        if counters['done'] % 1000 == 0:
            logger.info("Upgraded workflow history for %d documents.",
                        counters['done'])
            transaction.commit()

def upgrade_unicode(portal):
    cpounters = dict(done=0, total=0)

    logger.info("Starting workflow history upgrade for all documents.")
    counters = dict(done=0, total=0)
    upgrade_unicode_in(portal, counters=counters, walk_folders=True)
    transaction.commit()

    logger.warn(
        "Finished to upgrade workflow history. Successful for %d/%d proxies",
        counters['done'], counters['total'])
