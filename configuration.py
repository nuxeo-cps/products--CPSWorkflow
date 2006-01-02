# -*- coding: iso-8859-15 -*-
# (C) Copyright 2002, 2003, 2005 Nuxeo SARL <http://nuxeo.com>
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
"""CPS workflow configuration object.

This is a placeful definition of the portal_type -> workflow chain
mapping.
"""

from zLOG import LOG, ERROR, DEBUG
from Acquisition import aq_parent, aq_inner
from Globals import InitializeClass, DTMLFile, PersistentMapping
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.CPSWorkflow.permissions import ManageWorkflows
from Products.CPSWorkflow.workflowtool import LOCAL_WORKFLOW_CONFIG_ID
from Products.CPSWorkflow.interfaces import ILocalWorkflowConfiguration


class Configuration(SimpleItem):
    """Workflow Configuration.

    A workflow configuration object describes placefully what workflow
    chain are to be used for what portal_type.
    """

    implements(ILocalWorkflowConfiguration)

    id = LOCAL_WORKFLOW_CONFIG_ID
    meta_type = 'CPS Workflow Configuration'
    portal_type = None

    security = ClassSecurityInfo()

    def __init__(self):
        self.clear()

    security.declareProtected(ManageWorkflows, 'clear')
    def clear(self):
        self._chains_by_type = PersistentMapping()
        self._chains_by_type_under = PersistentMapping()
        # The None value means "use the default chain".
        # If a key is present, then the chain is overloaded,
        #    otherwise any acquired config is used.
        # XXX There is no way to override locally the default chain...

    #
    # API called by CPS Workflow Tool
    #
    def _get_chain_or_default(self, portal_type, chain):
        """Return the chain for portal_type, or the Default chain."""
        if chain is not None:
            return chain
        wftool = getToolByName(self, 'portal_workflow')
        # May want to revisit this if we want to placefully override Default
        return wftool.getDefaultChainFor(portal_type)

    security.declarePrivate('getPlacefulChainFor')
    def getPlacefulChainFor(self, portal_type, start_here=1):
        """Get the chain for the given portal_type.

        Returns None if no placeful chain is found.
        Acquires from parent configurations if needed.
        """
        if not start_here:
            if self._chains_by_type_under.has_key(portal_type):
                chain = self._chains_by_type_under[portal_type]
                return self._get_chain_or_default(portal_type, chain)
        if self._chains_by_type.has_key(portal_type):
            chain = self._chains_by_type[portal_type]
            return self._get_chain_or_default(portal_type, chain)
        # Ask above.
        parent = aq_parent(aq_inner(aq_parent(aq_inner(self))))
        try:
            higher_conf = parent.aq_acquire(LOCAL_WORKFLOW_CONFIG_ID,
                                            containment=1)
        except AttributeError:
            # Nothing placeful found.
            return None
        return higher_conf.getPlacefulChainFor(portal_type, start_here=0)

    #
    # Internal API
    #
    security.declareProtected(ManageWorkflows, 'setChain')
    def setChain(self, portal_type, chain):
        """Set the chain for a portal type."""
        wftool = getToolByName(self, 'portal_workflow')
        if chain is not None:
            for wf_id in chain:
                if not wftool.getWorkflowById(wf_id):
                    raise ValueError, (
                        '"%s" is not a workflow ID.' % wf_id)
            chain = tuple(chain)
        self._chains_by_type[portal_type] = chain

    security.declareProtected(ManageWorkflows, 'setChainUnder')
    def setChainUnder(self, portal_type, chain):
        """Set the "under" chain for a portal type."""
        wftool = getToolByName(self, 'portal_workflow')
        if chain is not None:
            for wf_id in chain:
                if not wftool.getWorkflowById(wf_id):
                    raise ValueError, (
                        '"%s" is not a workflow ID.' % wf_id)
            chain = tuple(chain)
        self._chains_by_type_under[portal_type] = chain

    security.declareProtected(ManageWorkflows, 'delChain')
    def delChain(self, portal_type):
        """Delete the chain for a portal type."""
        del self._chains_by_type[portal_type]

    security.declareProtected(ManageWorkflows, 'delChainUnder')
    def delChainUnder(self, portal_type):
        """Delete the chain for a portal type."""
        del self._chains_by_type_under[portal_type]

    security.declarePrivate('getChains')
    def getChains(self):
        """Get the chains.

        Returns two mappings (local, below) of portal_type -> chain
        A chain is '(Default)' or '' or a workflow id.
        """
        local, below = {}, {}
        for mapping, source in ((local, self._chains_by_type),
                                (below, self._chains_by_type_under)):
            for portal_type, chains in source.items():
                if chains:
                    # Only keep one workflow
                    chain = chains[0]
                elif chains is None:
                    chain = '(Default)'
                else:
                    chain = ''
                mapping[portal_type] = chain
        return (local, below)

    security.declarePrivate('setChains')
    def setChains(self, local, below):
        """Set the chains.
        """
        for mapping, set in ((local, self.setChain),
                             (below, self.setChainUnder)):
            for portal_type, chain in mapping.items():
                if chain == '(Default)':
                    chains = None
                elif chain:
                    # Only keep one workflow
                    chains = [chain.strip()]
                else:
                    chains = []
                set(portal_type, chains)

    #
    # ZMI
    #
    manage_options = ({'label' : 'Workflows',
                       'action' : 'manage_editForm',
                       },
                      ) + SimpleItem.manage_options

    _manage_editForm = DTMLFile('zmi/workflowConfigurationEditForm', globals())

    security.declareProtected(ManageWorkflows, 'manage_editForm')
    def manage_editForm(self, REQUEST=None):
        """The edit form."""
        ttool = getToolByName(self, 'portal_types')
        types_infos = []
        addable_infos = []
        for cbt in self._chains_by_type, self._chains_by_type_under:
            types_info = []
            addable_info = []
            for ti in ttool.listTypeInfo():
                id = ti.getId()
                title = ti.Title()
                if cbt.has_key(id):
                    chain = cbt[id]
                    if chain is not None:
                        chain_str = ', '.join(chain)
                    else:
                        chain_str = '(Default)'
                    if title == id:
                        title = None
                    types_info.append({'id': id,
                                       'title': title,
                                       'chain': chain_str})
                else:
                    if title != id:
                        title = '%s (%s)' % (title, id)
                    addable_info.append({'id': id,
                                         'title': title})
            types_infos.append(types_info)
            addable_infos.append(addable_info)
        return self._manage_editForm(REQUEST,
                                     types_infos=types_infos,
                                     addable_infos=addable_infos)

    security.declareProtected(ManageWorkflows, 'manage_editChains')
    def manage_editChains(self,
                          sub_save=None, sub_del=None,
                          REQUEST=None):
        """Edit the chains."""
        kw = REQUEST.form
        ttool = getToolByName(self, 'portal_types')
        if sub_save is not None:
            for cbt in self._chains_by_type, self._chains_by_type_under:
                if cbt is self._chains_by_type:
                    prefix = 'chain_'
                    set = self.setChain
                else:
                    prefix = 'under_chain_'
                    set = self.setChainUnder
                for ti in ttool.listTypeInfo():
                    id = ti.getId()
                    if not cbt.has_key(id):
                        continue
                    chain = kw.get(prefix+id)
                    if chain is None:
                        continue
                    if chain == '(Default)':
                        chain = None
                    else:
                        chain = chain.split(',')
                        chain = [wf.strip() for wf in chain if wf.strip()]
                    set(id, chain)
            if REQUEST is not None:
                REQUEST.set('manage_tabs_message', 'Saved.')
                return self.manage_editForm(REQUEST)
        elif sub_del is not None:
            for cbt in self._chains_by_type, self._chains_by_type_under:
                if cbt is self._chains_by_type:
                    prefix = 'cb_'
                    dodel = self.delChain
                else:
                    prefix = 'under_cb_'
                    dodel = self.delChainUnder
                for ti in ttool.listTypeInfo():
                    id = ti.getId()
                    if not cbt.has_key(id):
                        continue
                    if kw.has_key(prefix+id):
                        dodel(id)
            if REQUEST is not None:
                REQUEST.set('manage_tabs_message', 'Deleted.')
                return self.manage_editForm(REQUEST)

    security.declareProtected(ManageWorkflows, 'manage_addChain')
    def manage_addChain(self, portal_type, chain, under_sub_add=None,
                        REQUEST=None):
        """Add a chain."""
        if under_sub_add is None:
            set = self.setChain
        else:
            set = self.setChainUnder
        chain = chain.strip()
        if chain == '(Default)':
            chain = None
        else:
            chain = chain.split(',')
            chain = [wf.strip() for wf in chain if wf.strip()]
        set(portal_type, chain)
        if REQUEST is not None:
            REQUEST.set('manage_tabs_message', 'Added.')
            return self.manage_editForm(REQUEST)

InitializeClass(Configuration)

def addConfiguration(container, REQUEST=None):
    """Add a Workflow Configuration."""
    # container is a dispatcher when called from ZMI
    ob = Configuration()
    id = ob.getId()
    container._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(container.absolute_url()+'/manage_main')
    else:
        return container._getOb(id)
