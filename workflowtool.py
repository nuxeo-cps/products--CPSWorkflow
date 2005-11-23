# -*- coding: iso-8859-15 -*-
# (C) Copyright 2002-2005 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
# Contributor: Julien Anguenot <ja@nuxeo.com>
#              - Stack workflow API
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
"""Workflow Tool with CPS proxy knowledge, CPS placeful workflow support and
stack workflows support.
"""

from zLOG import LOG, ERROR, DEBUG, TRACE, INFO

from types import StringType
from Acquisition import aq_base, aq_parent, aq_inner
from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo, Unauthorized
from OFS.Folder import Folder
from webdav.WriteLockInterface import WriteLockInterface

from Products.CMFCore.utils import _checkPermission, getToolByName
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.WorkflowTool import WorkflowTool as BaseWorkflowTool

from stackregistries import WorkflowStackRegistry
from stackregistries import WorkflowStackDefRegistry
from stackregistries import WorkflowStackElementRegistry

from transitions import TRANSITION_ALLOWSUB_CREATE
from transitions import TRANSITION_ALLOWSUB_DELETE
from transitions import TRANSITION_ALLOWSUB_MOVE
from transitions import TRANSITION_ALLOWSUB_COPY
from transitions import TRANSITION_ALLOWSUB_PUBLISHING
from transitions import TRANSITION_ALLOWSUB_CHECKOUT
from transitions import TRANSITION_INITIAL_CREATE
from transitions import TRANSITION_INITIAL_MOVE
from transitions import TRANSITION_INITIAL_COPY
from transitions import TRANSITION_INITIAL_PUBLISHING
from transitions import TRANSITION_INITIAL_CHECKOUT
from transitions import TRANSITION_ALLOW_CHECKIN
from transitions import TRANSITION_BEHAVIOR_PUBLISHING

#
# CPSCore is optional now.
# Check DEPENDENCIES.txt
#

try:
    from Products.CPSCore.ProxyBase import ProxyBase, ProxyFolderishDocument
    from Products.CPSCore.ProxyBase import ProxyBTreeFolderishDocument
    from Products.CPSCore.EventServiceTool import getEventService
except ImportError, e:
    if str(e) not in ('No module named CPSCore.EventServiceTool'
                      'No module named CPSCore.ProxyBase'):
        raise

    LOG("Optional Dependencies missing", INFO,
        "CPSCore.EventServiceTool and CPSCore.ProxyBase")

    #
    # Here defines optional dependencies on CPSCore elt.
    #

    class FakeEventService:
        def notify(self, *args, **kw):
            pass

    def getEventService(context):
        return FakeEventService

    class ProxyBase:
        pass

    class ProxyFolderishDocument:
        pass

    class ProxyBTreeFolderishDocument:
        pass

# id of the cps workflow configuration objects
Config_id = '.cps_workflow_configuration'


class WorkflowTool(BaseWorkflowTool):
    """A Workflow Tool extending the CMFCore one with CPS features.

    - Initial transition knowledge for CPSWorkflow
    - Placefulness
    - Delegates storage of workflow history for proxies to repository tool
    """

    id = 'portal_workflow'
    meta_type = 'CPS Workflow Tool'
    title = 'CPS Workflow Tool'

    manage_options = ( Folder.manage_options[0],
                       { 'label' : 'Workflows',
                         'action' : 'manage_selectWorkflows'
                       },
                       { 'label' : 'Overview', 'action' : 'manage_overview' }
                     ) + Folder.manage_options[1:]

    security = ClassSecurityInfo()

    # We don't need a default default chain
    _default_chain = ()

    #def __init__(self):
    #    pass

    #
    # Allow user code access to constants.
    #

    TRANSITION_ALLOWSUB_CHECKOUT =   TRANSITION_ALLOWSUB_CHECKOUT
    TRANSITION_INITIAL_CREATE =      TRANSITION_INITIAL_CREATE
    TRANSITION_INITIAL_CHECKOUT =    TRANSITION_INITIAL_CHECKOUT
    TRANSITION_INITIAL_PUBLISHING =  TRANSITION_INITIAL_PUBLISHING
    TRANSITION_BEHAVIOR_PUBLISHING = TRANSITION_BEHAVIOR_PUBLISHING

    #
    # API
    #
    security.declarePublic('isCreationAllowedIn')
    def isCreationAllowedIn(self, container, get_details=0):
        """Is the creation of a subobject allowed in the container ?"""
        return self.isBehaviorAllowedFor(container, 'create',
                                         get_details=get_details)

    security.declarePublic('isBehaviorAllowedFor')
    def isBehaviorAllowedFor(self, container, behavior, transition=None,
                             get_details=0):
        """Is some behavior allowed in the container?

        If transition is present, only check a transition with this name.
        """
        container = self._container_maybe_rpath(container)
        behavior = {
            'create': TRANSITION_ALLOWSUB_CREATE,
            'delete': TRANSITION_ALLOWSUB_DELETE,
            'cut':    TRANSITION_ALLOWSUB_MOVE,
            'copy':   TRANSITION_ALLOWSUB_COPY,
            'paste':  TRANSITION_ALLOWSUB_CREATE,
            }.get(behavior, behavior)
        for wf in self.getWorkflowsFor(container):
            # XXX deal with non-CPS workflows
            ok, why = wf.isBehaviorAllowedFor(container, behavior,
                                              transition, get_details=1)
            if not ok:
                LOG('isBehaviorAllowedFor', DEBUG, 'not ok for %s: %s' %
                    (behavior, why))
                if get_details:
                    return 0, '%s, %s' % (wf.getId(), why)
                else:
                    return 0
        if get_details:
            return 1, ''
        else:
            return 1

    security.declarePublic('getAllowedContentTypes')
    def getAllowedContentTypes(self, ob):
        """Get the list of portal types allowed for creating.

           Note that all creation transitions are taken into account, not just
           'create'.
        """
        ttool = getToolByName(self, 'portal_types')
        getInitialTransitions = ttool.getInitialTransitions
        allowed = []
        for type in ttool.listTypeInfo():
            if getInitialTransitions(ob, type.getId(),
                                     TRANSITION_INITIAL_CREATE):
                allowed.append(type)

        return allowed

    security.declarePublic('getAllowedPublishingTransitions')
    def getAllowedPublishingTransitions(self, ob):
        """Get the list of allowed initial transitions for publishing."""
        d = {}
        for wf in self.getWorkflowsFor(ob):
            if not hasattr(aq_base(wf), 'getAllowedPublishingTransitions'):
                # Not a CPS workflow.
                continue
            for t in wf.getAllowedPublishingTransitions(ob):
                d[t] = None
        transitions = d.keys()
        transitions.sort()
        return transitions

    security.declarePublic('getInitialTransitions')
    def getInitialTransitions(self, container, type_name, behavior):
        """Get the initial transitions for a type in a container.

        container: can be an rpath.

        type_name: the portal type to check.

        behavior: the type of transition to check for.

        Returns a sequence of transition names.
        """
        container = self._container_maybe_rpath(container)
        LOG('CPSWFT', TRACE,
            "getInitialTransitions container=%s type_name=%s behavior=%s "
            % ('/'.join(container.getPhysicalPath()), type_name, behavior))
        d = {}

        for wf_id in self.getChainFor(type_name, container=container):
            wf = self.getWorkflowById(wf_id)
            if wf is None:
                # Incorrect workflow name in chain.
                continue
            if not hasattr(aq_base(wf), 'getInitialTransitions'):
                # Not a CPS workflow.
                continue
            for t in wf.getInitialTransitions(container, behavior):
                d[t] =  None

        transitions = d.keys()
        transitions.sort()
        LOG('CPSWFT', TRACE, "  Transitions are %s" % `transitions`)
        return transitions

    def _container_maybe_rpath(self, container):
        if isinstance(container, StringType):
            rpath = container
            if not rpath or rpath.startswith('/') or '..' in rpath.split('/'):
                raise ValueError(rpath)
            portal = aq_parent(aq_inner(self))
            container = portal.unrestrictedTraverse(rpath)
        return container

    security.declarePublic('getDefaultLanguage')
    def getDefaultLanguage(self):
        """Get the default language for a new object."""
        portal = aq_parent(aq_inner(self))
        if hasattr(portal, 'translation_service'):
            return portal.translation_service.getDefaultLanguage()
        else:
            return 'en'

    security.declarePublic('invokeFactoryFor')
    def invokeFactoryFor(self, container, type_name, id,
                         language=None, initial_transition=None,
                         *args, **kw):
        """Create an object in a container.

        The variable initial_transition is the initial transition to use
        (in all workflows). If None, use the first initial transition
        for 'create' found.

        The object created will be a proxy to a real object if the type
        type_name has an property of id 'cps_proxy_type' and of value
        'folder', 'document' or 'folderishdocument'.
        """
        container = self._container_maybe_rpath(container)
        LOG('invokeFactoryFor', DEBUG,
            "Called with container=%s type_name=%s id=%s "
            "language=%s initial_transition=%s" %
            ('/'.join(container.getPhysicalPath()), type_name, id,
             language, initial_transition))
        if language is None:
            language = self.getDefaultLanguage()
        if initial_transition is None:
            # If no initial transition is mentionned, find a default.
            crtrans = self.getInitialTransitions(container, type_name,
                                                 TRANSITION_INITIAL_CREATE)
            if len(crtrans) == 1:
                initial_transition = crtrans[0]
            elif len(crtrans) > 1:
                raise WorkflowException(
                    "More than one initial transition available "+str(crtrans))
            else:
                raise WorkflowException(
                    "No initial_transition to create %s (type_name=%s) in %s"
                    % (id, type_name, container.getId()))
        ob = self._createObject(container, id,
                                initial_transition, TRANSITION_INITIAL_CREATE,
                                language=language, type_name=type_name,
                                kwargs=kw)
        return ob.getId()

    security.declarePublic('findNewId')
    def findNewId(self, container, id):
        """Find what will be the new id of an object created in a container."""
        container = self._container_maybe_rpath(container)
        base_container = aq_base(container)
        if hasattr(base_container, id):
            # Collision, find a free one.
            i = 0
            while 1:
                i += 1
                try_id = '%s_%d' % (id, i)
                if not hasattr(base_container, try_id):
                    id = try_id
                    break
        return id

    security.declarePrivate('cloneObject')
    def cloneObject(self, ob, container, initial_transition, kwargs):
        """Clone ob into container according to some initial transition.

        (Called by a CPS workflow during publishing transition.)
        """
        LOG('cloneObject', DEBUG, 'Called with ob=%s container=%s '
            'initial_transition=%s' % (ob.getId(), container.getId(),
                                       initial_transition))
        id = self.findNewId(container, ob.getId())
        new_ob = self._createObject(container, id,
                                    initial_transition,
                                    TRANSITION_INITIAL_PUBLISHING,
                                    old_ob=ob, kwargs=kwargs)
        return new_ob


    security.declarePrivate('checkoutObject')
    def checkoutObject(self, ob, container, initial_transition,
                       language_map, kwargs):
        """Checkout ob into container according to some initial transition.

        Checkout the languages according to the language map.

        (Called by CPS Workflow during checkout transition.)
        """
        LOG('checkoutObject', DEBUG, "Called with ob=%s container=%s "
            "initial_transition=%s language_map=%s" %
            (ob.getId(), container.getId(), initial_transition, language_map))
        id = self.findNewId(container, ob.getId())
        new_ob = self._createObject(container, id,
                                    initial_transition,
                                    TRANSITION_INITIAL_CHECKOUT,
                                    language_map=language_map,
                                    old_ob=ob, kwargs=kwargs)
        return new_ob

    def _createObject(self, container, id,
                      initial_transition, initial_behavior,
                      language=None, type_name=None, old_ob=None,
                      language_map=None,
                      kwargs=None):
        """Create an object in a container, according to initial behavior."""
        LOG('_createObject', DEBUG, 'Called with container=%s id=%s '
            'initial_transition=%s' % (container.getId(), id,
                                       initial_transition))
        pxtool = getToolByName(self, 'portal_proxies')

        if kwargs is None:
            kwargs = {}

        # Check that the workflow of the container allows sub behavior.
        subbehavior = {
            TRANSITION_INITIAL_CREATE:     TRANSITION_ALLOWSUB_CREATE,
            TRANSITION_INITIAL_MOVE:       TRANSITION_ALLOWSUB_MOVE,
            TRANSITION_INITIAL_COPY:       TRANSITION_ALLOWSUB_COPY,
            TRANSITION_INITIAL_PUBLISHING: TRANSITION_ALLOWSUB_PUBLISHING,
            TRANSITION_INITIAL_CHECKOUT:   TRANSITION_ALLOWSUB_CHECKOUT,
            }.get(initial_behavior)
        if subbehavior is None:
            raise WorkflowException("Incorrect initial_behavior=%s" %
                                    initial_behavior)
        ok, why = self.isBehaviorAllowedFor(container, subbehavior,
                                            get_details=1)
        if not ok:
            if why:
                details = 'not allowed by workflow %s' % why
            else:
                details = 'no workflow'
            raise WorkflowException("Container %s does not allow "
                                    "subobject behavior %s (%s)" %
                                    (container.getId(),
                                     subbehavior, details))
        # Find type to create.
        if initial_behavior != TRANSITION_INITIAL_CREATE:
            type_name = old_ob.getPortalTypeName()
        # Find out if we must create a normal document or a proxy.
        # XXX determine what's the best way to parametrize this
        proxy_type = None
        ttool = getToolByName(self, 'portal_types')
        for ti in ttool.listTypeInfo():
            if ti.getId() != type_name:
                continue
            proxy_type = getattr(ti, 'cps_proxy_type', None)
            break

        if initial_behavior == TRANSITION_INITIAL_PUBLISHING:
            # XXX should not notify cmfadd
            ob = container.copyContent(old_ob, id)
            # Removing any possible WebDAV locks on the checked-out object
            # because the copyContent method also copy locks (which might or
            # might not be considered a bug).
            if WriteLockInterface.isImplementedBy(ob):
                ob.wl_clearLocks()
            # XXX later! the object is not finished yet!
            ob.manage_afterCMFAdd(ob, container)
            self._insertWorkflowRecursive(ob, initial_transition,
                                          initial_behavior, kwargs)
        elif initial_behavior == TRANSITION_INITIAL_CREATE:
            if not proxy_type:
                # XXX constructContent doesn't exist everywhere!
                # XXX especially when creating at the root of the portal.
                id = container.constructContent(type_name, id, **kwargs)
                # constructContent indexed the object (CMF contract)
                ob = getattr(container, id)
            else:
                # Create a proxy and a document in the repository.
                proxy = pxtool.createEmptyProxy(proxy_type, container,
                                                type_name, id)

                if kwargs.has_key('datamodel'):
                    # Fill the datamodel with the proxy we now have
                    dm = kwargs['datamodel']
                    dm._setObject(None, proxy=proxy)

                # Set the first language as default language.
                proxy.setDefaultLanguage(language)
                pxtool.createRevision(proxy, language, **kwargs)
                # createRevision indexed the proxy
                ob = proxy
            ob.manage_afterCMFAdd(ob, container)
            # XXX at this point we still don't have a workflow state...
            # XXX so tree caches are wrong!
            self._insertWorkflow(ob, initial_transition, initial_behavior,
                                 kwargs)
        elif initial_behavior == TRANSITION_INITIAL_CHECKOUT:
            if not isinstance(old_ob, ProxyBase):
                raise WorkflowException("Can't checkout non-proxy object %s"
                                        % '/'.join(old_ob.getPhysicalPath()))
            old_proxy = old_ob
            from_language_revs = old_proxy.getLanguageRevisions()
            docid = old_proxy.getDocid()
            proxy = pxtool.createEmptyProxy(proxy_type, container,
                                            type_name, id, docid)
            pxtool.checkoutRevisions(old_proxy, proxy, language_map)
            proxy.setDefaultLanguage(old_proxy.getDefaultLanguage())
            proxy.setFromLanguageRevisions(from_language_revs)
            ob = proxy
            ob.manage_afterCMFAdd(ob, container)
            self._insertWorkflow(ob, initial_transition, initial_behavior,
                                 kwargs)
        else:
            raise NotImplementedError(initial_behavior)
        return ob

    def _insertWorkflow(self, ob, initial_transition, initial_behavior,
                        kwargs):
        """Insert ob into workflows."""
        # Do initial transition for all workflows.
        LOG('_insertWorkflow', DEBUG,
            "inserting %s using transition=%s behavior=%s kw=%s" %
            (ob.getId(), initial_transition, initial_behavior, kwargs))
        reindex = 0

        # Remove old workflow information.
        try:
            delattr(ob, 'workflow_history')
        except (AttributeError, KeyError):
            # ExtensionClasses raise KeyError... duh.
            pass

        for wf in self.getWorkflowsFor(ob):
            if hasattr(aq_base(wf), 'insertIntoWorkflow'):
                wf.insertIntoWorkflow(ob, initial_transition, initial_behavior,
                                      kwargs)
                reindex = 1
        if reindex:
            self._reindexWorkflowVariables(ob)
            # XXX this should be done in reindexObject really...
            evtool = getEventService(self)
            evtool.notify('sys_modify_object', ob, {})

    def _insertWorkflowRecursive(self, ob, initial_transition,
                                 initial_behavior, kwargs):
        """Recursively insert into workflows.

        Only done for proxies... XXX correct?
        """
        LOG('_insertWorkflowRecursive', DEBUG,
            "Recursively inserting %s using transition=%s behavior=%s"
            % (ob.getId(), initial_transition, initial_behavior))
        if not isinstance(ob, ProxyBase):
            LOG('_insertWorkflowRecursive', DEBUG, "  Is not a proxy")
            #return # XXX correct?
        self._insertWorkflow(ob, initial_transition, initial_behavior, kwargs)
        # The recursion is only applied if it's a proxy folderish document.
        # If the considered object is a folder, its content should not be
        # subject to workflow modifications.
        isproxyfolderishdoc = isinstance(ob, ProxyFolderishDocument) or \
                              isinstance(ob, ProxyBTreeFolderishDocument)
        if isproxyfolderishdoc:
            for subob in ob.objectValues():
                self._insertWorkflowRecursive(subob, initial_transition,
                                              initial_behavior, kwargs)

    security.declarePrivate('checkinObject')
    def checkinObject(self, ob, dest_ob, transition):
        """Checkin ob into dest_ob.

        Then make the dest_ob follow the transition.

        (Called by CPS Workflow during checkin transition.)
        """
        ok, why = self.isBehaviorAllowedFor(dest_ob, TRANSITION_ALLOW_CHECKIN,
                                            transition, get_details=1)
        if not ok:
            if why:
                details = 'not allowed by workflow %s' % why
            else:
                details = 'no workflow'
            raise WorkflowException("Object=%s transition=%s does not allow "
                                    "checkin behavior (%s)" %
                                    (dest_ob.getId(), transition, details))
        pxtool = getToolByName(self, 'portal_proxies')
        pxtool.checkinRevisions(ob, dest_ob)
        self.doActionFor(dest_ob, transition) # XXX pass kw args ?

    security.declarePrivate('mergeObject')
    def mergeObject(self, ob, dest_container, state_var, new_state):
        """Merge a proxy into some existing one.

        Merging is the act of adding the revisions of a proxy into an
        existing one in the same container. If the proxy is a folderishdoc,
        also replaces the old subobjects with the new ones.

        Returns the destination object, or None if no merging was found.

        Does not do deletion of the source object. The destination
        object is guaranteed to be different than the source.

        (Called by CPSWorkflow during merge transition.)
        """
        pxtool = getToolByName(self, 'portal_proxies')
        dest_ob = self._checkObjectMergeable(ob, dest_container,
                                             state_var, new_state)[0]
        if dest_ob is not None:
            pxtool.checkinRevisions(ob, dest_ob)

        # For folderish documents, copy subobjects into new container.
        if (isinstance(dest_ob, ProxyFolderishDocument) or
            isinstance(dest_ob, ProxyBTreeFolderishDocument)):
            for id_ in [id_ for id_ in ob.objectIds()
                        if not id_.startswith('.')]:
                # Merge objects
                if id_ in dest_ob.objectIds():
                    subob = ob._getOb(id_)
                    dest_subob = self._checkObjectMergeable(
                        subob, dest_ob, state_var, new_state)[0]
                    if subob is not None:
                        pxtool.checkinRevisions(subob, dest_subob)
                # Insert into the container with workflow
                else:
                    subob = ob._getOb(id_)
                    dest_ob.copyContent(subob, id_)
                    subob = dest_ob._getOb(id_)

                    type_name = subob.getTypeInfo().getId()
                    inserted = False
                    # XXX enough ??
                    for behavior in (TRANSITION_INITIAL_CREATE,
                                     TRANSITION_INITIAL_PUBLISHING):
                        if inserted:
                            break
                        crtrans = self.getInitialTransitions(subob, type_name,
                                                             behavior)
                        for initial_transition in crtrans:
                            initial_behavior = behavior
                            try:
                                self._insertWorkflowRecursive(
                                    subob, initial_transition,
                                    initial_behavior, {})
                                inserted = True
                                break
                            except (WorkflowException, Unauthorized):
                                # Let's try other transitions
                                pass
                    if not inserted:
                        raise WorkflowException(
                            "You are not allowed to copy / paste here !")

            # Now erase the ones that are not part of the new revision anymore
            ids = [id_ for id_ in dest_ob.objectIds()
                   if not id_.startswith('.') and id_ not in ob.objectIds()]
            dest_ob.manage_delObjects(ids)

        return dest_ob

    security.declarePublic('isObjectMergeable')
    def isObjectMergeable(self, ob, dest_container, state_var, new_state):
        """Check if a proxy can be merged into some existing one
        in the destination container.

        dest_container can be an rpath.

        Returns the destination rpath, and language_revs, or None, None
        """
        dest_ob, language_revs = self._checkObjectMergeable(ob, dest_container,
                                                            state_var,
                                                            new_state)
        if dest_ob is not None:
            utool = getToolByName(self, 'portal_url')
            return utool.getRelativeUrl(dest_ob), language_revs
        else:
            return None, None

    security.declarePrivate('_checkObjectMergeable')
    def _checkObjectMergeable(self, ob, dest_container, state_var, new_state):
        """Check if a proxy can be merged into some existing one
        in the destination container.

        dest_container can be an rpath.

        Return the destination proxy and language_revs, or None, None.
        """
        LOG('_checkObjectMergeable', DEBUG,
            'check ob=%s dest=%s var=%s state=%s'
            % (ob.getId(), dest_container, state_var, new_state))
        if not isinstance(ob, ProxyBase):
            LOG('_checkObjectMergeable', DEBUG, ' Not a proxy')
            return None, None

        utool = getToolByName(self, 'portal_url')
        pxtool = getToolByName(self, 'portal_proxies')

        rpath = utool.getRelativeUrl(ob)
        if isinstance(dest_container, StringType):
            container_rpath = dest_container
        else:
            container_rpath = utool.getRelativeUrl(dest_container)
        if container_rpath:
            container_rpath += '/'
        infos = pxtool.getProxyInfosFromDocid(ob.getDocid(),
                                              [state_var])
        dest_ob = None
        language_revs = None
        for info in infos:
            dob = info['object']
            drpath = info['rpath']
            if drpath != container_rpath+dob.getId():
                # Proxy not in the dest container.
                LOG('_checkObjectMergeable', TRACE,
                    '  Not in dest: %s' % drpath)
                continue
            if info[state_var] != new_state:
                # Proxy not in the correct state.
                LOG('_checkObjectMergeable', TRACE,
                    '  Bad state=%s: %s' % (info[state_var], drpath))
                continue
            if drpath == rpath:
                # Skip ourselves.
                LOG('_checkObjectMergeable', TRACE,
                    '  Ourselves: %s' % drpath)
                continue
            # Get the first one that matches.
            dest_ob = dob
            language_revs = info['language_revs']
            LOG('_checkObjectMergeable', DEBUG, ' Found %s' % drpath)
            break
        if dest_ob is None:
            LOG('_checkObjectMergeable', DEBUG, ' NotFound')
        return dest_ob, language_revs

    #
    # Constrained workflow transitions for folderish documents.
    #
    security.declarePublic('doActionFor')
    def doActionFor(self, ob, action, wf_id=None, *args, **kw):
        """Execute the given workflow action for the object.

        Invoked by user interface code.
        The workflow object must perform its own security checks.
        """
        # Don't recurse for initial transitions! # XXX urgh
        isproxyfolderishdoc = isinstance(ob, ProxyFolderishDocument) or \
                              isinstance(ob, ProxyBTreeFolderishDocument)
        if isproxyfolderishdoc and not kw.has_key('dest_container'):
            return self._doActionForRecursive(ob, action, wf_id=wf_id,
                                              *args, **kw)
        else:
            return self._doActionFor(ob, action, wf_id=wf_id, *args, **kw)

    security.declarePrivate('_doActionFor')
    def _doActionFor(self, ob, action, wf_id=None, *args, **kw):
        """Follow a transition."""
        LOG('_doActionFor', DEBUG, 'start, ob=%s action=%s' %
            (ob.getId(), action))
        wfs = self.getWorkflowsFor(ob)
        if wfs is None:
            wfs = ()
        if wf_id is None:
            if not wfs:
                raise WorkflowException('No workflows found.')
            for wf in wfs:
                LOG('_doActionFor', TRACE, ' testing wf %s' % wf.getId())
                if wf.isActionSupported(ob, action, **kw):
                    LOG('_doActionFor', TRACE, ' found!')
                    break
                LOG('_doActionFor', TRACE, ' not found')
            else:
                raise WorkflowException(
                    'No workflow provides the "%s" action.' % action)
        else:
            wf = self.getWorkflowById(wf_id)
            if wf is None:
                raise WorkflowException(
                    'Requested workflow definition not found.')
        return self._invokeWithNotification(
            wfs, ob, action, wf.doActionFor, (ob, action) + args, kw)

    security.declarePrivate('_doActionForRecursive')
    def _doActionForRecursive(self, ob, action, wf_id=None, *args, **kw):
        """Recursively calls doactionfor."""
        LOG('_doActionForRecursive', DEBUG, 'ob=%s action=%s' %
            (ob.getId(), action))
        if not isinstance(ob, ProxyBase): # XXX
            return
        # Do the recursion children first, so that if we have to do an
        # accept and a merge, subdocuments are merged already published.
        for subob in ob.objectValues():
            self._doActionForRecursive(subob, action, wf_id=wf_id, *args, **kw)
        self._doActionFor(ob, action, wf_id=wf_id, *args, **kw)

    #
    # History/status management
    #

    security.declarePublic('getFullHistoryOf')
    def getFullHistoryOf(self, ob):
        """Return the full history of an object.

        Uses aggregated history for proxies.

        Returns () for non-proxies.
        """
        if not _checkPermission(View, ob):
            raise Unauthorized("Can't get history of an unreachable object.")
        if not isinstance(ob, ProxyBase):
            return ()
        repotool = getToolByName(self, 'portal_repository')
        return repotool.getHistory(ob.getDocid()) or ()

    security.declarePrivate('setStatusOf')
    def setStatusOf(self, wf_id, ob, status):
        """Append an entry to the workflow history.

        Stores the local history in the object itself.
        Stores the aggregated history using the repository tool.

        The entry also has 'rpath' and 'workflow_id' values stored.

        Invoked by workflow definitions.
        """
        # Additional info in status: rpath, workflow_id
        utool = getToolByName(self, 'portal_url')
        status = status.copy()
        status['rpath'] = utool.getRelativeUrl(ob)
        status['workflow_id'] = wf_id

        # Standard CMF storage.
        BaseWorkflowTool.setStatusOf(self, wf_id, ob, status)

        # CPS specifics
        # Store aggregated history in repository.
        # XXX Check to avoir the dependency in here.
        if not isinstance(ob, ProxyBase):
            return
        repotool = getToolByName(self, 'portal_repository')
        docid = ob.getDocid()
        wfh = repotool.getHistory(docid) or ()
        wfh += (status,)
        repotool.setHistory(docid, wfh)

    #
    # Misc
    #

    # Overloaded for placeful workflow definitions
    def getChainFor(self, ob, container=None):
        """Return the chain that applies to the given object.

        The first argument is either an object or a portal type name.

        Takes into account placeful workflow definitions, by starting
        looking for them at the object itself, or in the container
        if provided.
        """
##         import traceback
##         from zExceptions.ExceptionFormatter import format_exception
##         traceback.format_exception = format_exception
##         from StringIO import StringIO
##         s = StringIO()
##         traceback.print_stack(file=s)
##         LOG('getChainFor', DEBUG, 'comming from tb:\n%s' % s.getvalue())

        if isinstance(ob, StringType):
            pt = ob
        elif hasattr(aq_base(ob), '_getPortalTypeName'):
            pt = ob._getPortalTypeName()
            if container is None:
                container = ob
        else:
            pt = None
        if pt is None:
            return ()
        if container is None:
            LOG('WorkflowTool', ERROR,
                'getChainFor: no container for ob %s' % (ob,))
            return ()
        # Find placeful workflow configuration object.
        wfconf = getattr(container, Config_id, None)
        if wfconf is not None:
            # Was it here or did we acquire?
            start_here = hasattr(aq_base(container), Config_id)
            chain = wfconf.getPlacefulChainFor(pt, start_here=start_here)
            if chain is not None:
                return chain
        # Nothing placeful found.
        return self.getGlobalChainFor(pt)

    security.declarePrivate('getGlobalChainFor')
    def getGlobalChainFor(self, ob):
        """Get the global chain for a given object or type_name."""
        return WorkflowTool.inheritedAttribute('getChainFor')(self, ob)

    security.declarePrivate('getManagedPermissions')
    def getManagedPermissions(self):
        """Get all the permissions managed by the workflows."""
        perms = {}
        for wf in self.objectValues():
            if not getattr(wf, '_isAWorkflow', 0):
                continue
            if hasattr(aq_base(wf), 'getManagedPermissions'):
                # CPSWorkflow
                permissions = wf.getManagedPermissions()
            elif hasattr(aq_base(wf), 'permissions'):
                # DCWorkflow
                permissions = wf.permissions
            else:
                # Probably a DefaultWorkflow
                permissions = (View, ModifyPortalContent)
            for p in permissions:
                perms[p] = None
        return perms.keys()

    #
    # STACK WORKFLOWS API
    #

    security.declarePublic('getStackDefinitionsFor')
    def getStackDefinitionsFor(self, ob):
        """Return stack definitions from the ob's current StateDefinition

        The delegatees information is as follow for instance:
           {'Pilots': <StackDefinition Instance at sxxxx >,
            'Watchers': <StackDefinitionInstance at xxxx>,
            'Associates': <StackDefinitionInstance at xxxx>}

        The key is the name of the workflow variable.  The value is a instance
        of one of the stack definition instances holding the stack
        configuration. (i.e : CPSWorkflowStackDefinitions.py)
        """
        info = {}
        for wf in self.getWorkflowsFor(ob):
            state_def = wf._getWorkflowStateOf(ob)
            if state_def is not None:
                info.update(state_def.getStackDefinitions())
        return info

    security.declarePublic('getStackDefinitionFor')
    def getStackDefinitionFor(self, ob, wf_var_id=''):
        """Return the stack definition instance from ob's current
        StateDefinition given the workflow variable id
        """
        if wf_var_id:
            stackdefs = self.getStackDefinitionsFor(ob)
            if stackdefs:
                return stackdefs.get(wf_var_id)
        return None

    security.declarePublic('getStacks')
    def getStacks(self, ob):
        """Return defined delegatees data structures for this ob

        returned value is a dictionnary containing as keys the name of the
        variables and as value the data structure instance storing the
        delegatees
        """
        data_structs = {}
        delegatees_info = self.getStackDefinitionsFor(ob)
        for var_id in delegatees_info.keys():
            for wf in self.getWorkflowsFor(ob):
                try:
                    ds_instance = self.getInfoFor(ob, var_id, wf_id=wf.id)
                except (WorkflowException, KeyError,):
                    data_structs[var_id] = None
                else:
                    data_structs[var_id] = ds_instance
        return data_structs

    security.declarePublic('getStackFor')
    def getStackFor(self, ob, stack_id):
        """Return the delegatees data struct corresponding to the stack_id
        """
        return self.getStacks(ob).get(stack_id)

    security.declarePublic('canManageStack')
    def canManageStack(self, ob, stack_id, **kw):
        """Can the authenticated use or the user given it's member_id
        manage the stack given its id.

        You may have a hierarchy in between the stack. For instance, in the
        'Pilots' stack the people can manage the 'Associates' and 'Observers'
        stacks.
        """
        stackdef = self.getStackDefinitionFor(ob, stack_id)
        if stackdef:
            mtool = getToolByName(self, 'portal_membership')
            aclu = self.acl_users
            ds = self.getStackFor(ob, stack_id)
            canManage = stackdef._canManageStack(ds, aclu, mtool, ob, **kw)
            if canManage:
                return 1
            else:
                # XXX AT: the same stack def is checked another time. If user
                # can manage the empty stack and the stack definition is in its
                # manager stacks ids, canManageStack will say yes and we don't
                # want that.
                # Anyway I'm not correcting it because manager_stack_ids
                # mechanism will not stay as it is, right? ;)
                stackdefs = self.getStackDefinitionsFor(ob)
                for stackdef_id in stackdefs.keys():
                    ostack_def = stackdefs[stackdef_id]
                    canManage = ostack_def._canManageStack(None, aclu, mtool,
                                                           ob, **kw)
                    manager_stack_ids = ostack_def.getManagerStackIds()
                    if (canManage and
                        stack_id in manager_stack_ids):
                        return 1
        return 0

    ####################################################################

    security.declarePublic('getWorkflowStackRegistry')
    def getWorkflowStackRegistry(self):
        """Returns the Workflow Stack Regitry

        So that it can be access from within restricted code
        """
        return WorkflowStackRegistry

    security.declarePublic('getWorkflowStackDefRegistry')
    def getWorkflowStackDefRegistry(self):
        """Returns the Workflow Stack Definition Regitry

        So that it can be access from within restricted code
        """
        return WorkflowStackDefRegistry

    security.declarePublic('getWorkflowStackElementRegistry')
    def getWorkflowStackElementRegistry(self):
        """Returns the Workflow Stack Element Regitry

        So that it can be access from within restricted code
        """
        return WorkflowStackElementRegistry

    ####################################################################

    security.declareProtected(ManagePortal,
                              'updateFormerLocalRoleMappingForStack')
    def updateFormerLocalRoleMappingForStack(self, ob, wf_id, stack_id,
                                             mapping):
        """Set the former local role mapping

        Sets the mapping for a given stack on a given given content
        object for a given workflow. The former local role mapping is
        defined within the status of the object.
        """
        status = self[wf_id]._getStatusOf(ob)
        sflrm = status.setdefault('sflrm', {})
        sflrm[stack_id] = mapping
        ob.workflow_history._p_changed = 1

    security.declareProtected(ManagePortal,
                               'getFormerLocalRoleMappingForStack')
    def getFormerLocalRoleMappingForStack(self, ob, wf_id, stack_id):
        """Return the former local role mapping for a given stack on a given
        given content object for a given workflow
        """

        # XXX code sucks

        _wf_history = ob.workflow_history[wf_id]
        if len(_wf_history) > 1:
            return _wf_history[-2].get('sflrm', {}).get(stack_id, {})
        return {}

    #
    # ZMI
    #

    manage_overview = DTMLFile('zmi/explainCPSWorkflowTool', globals())

    def all_meta_types(self):
        return ({'name': 'CPS Workflow',
                 'action': 'manage_addWorkflowForm',
                 'permission': ManagePortal},
                {'name': 'Workflow',
                 'action': 'manage_addWorkflowForm',
                 'permission': ManagePortal},
                )


InitializeClass(WorkflowTool)

def addWorkflowTool(container, REQUEST=None):
    """Add a CPS Workflow Tool."""
    ob = WorkflowTool()
    id = ob.getId()
    container._setObject(id, ob)
    if REQUEST is not None:
        REQUEST.RESPONSE.redirect(container.absolute_url()+'/manage_main')
