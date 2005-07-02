# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Anahide Tchertchian <at@nuxeo.com>
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
##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
#
# $Id$
"""Workflow tool import/export for CMFSetup

Knows about :
- transition and state flags
- stacks

Does not know about placeful worklow mappings configuration files yet.
"""
from zLOG import LOG, DEBUG

import os
from xml.dom.minidom import parseString as domParseString

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.CPSWorkflow.workflow import WorkflowDefinition as CPSWorkflowDefinition

# setup imports
from Products.CMFSetup.utils import _coalesceTextNodeChildren
from Products.CMFSetup.utils import _extractDescriptionNode
from Products.CMFSetup.utils import _getNodeAttribute
from Products.CMFSetup.utils import _getNodeAttributeBoolean

from Products.CMFSetup.workflow import WorkflowToolConfigurator
from Products.CMFSetup.workflow import WorkflowDefinitionConfigurator
from Products.CMFSetup.workflow import _getWorkflowFilename
from Products.CMFSetup.workflow import TRIGGER_TYPES
from Products.CMFSetup.workflow import _METATYPE_SUFFIXES

# overloaded
#from Products.CMFSetup.workflow import _extractStateNodes
#from Products.CMFSetup.workflow import _extractTransitionNodes
from Products.CMFSetup.workflow import _extractVariableNodes
from Products.CMFSetup.workflow import _extractWorklistNodes
from Products.CMFSetup.workflow import _extractPermissionNodes
from Products.CMFSetup.workflow import _extractScriptNodes
from Products.CMFSetup.workflow import _extractActionNode
from Products.CMFSetup.workflow import _extractGuardNode

#overloaded
#from Products.CMFSetup.workflow import _initDCWorkflowStates
#from Products.CMFSetup.workflow import _initDCWorkflowTransitions
from Products.CMFSetup.workflow import _initDCWorkflowVariables
from Products.CMFSetup.workflow import _initDCWorkflowWorklists
from Products.CMFSetup.workflow import _initDCWorkflowScripts

#overloaded
#from Products.CMFSetup.workflow import _extractStateNodes
#from Products.CMFSetup.workflow import _extractTransitionNodes
from Products.CMFSetup.workflow import _extractVariableNodes
from Products.CMFSetup.workflow import _extractWorklistNodes
from Products.CMFSetup.workflow import _extractScriptNodes
from Products.CMFSetup.workflow import _extractPermissionNodes
from Products.CMFSetup.workflow import _extractActionNode
from Products.CMFSetup.workflow import _extractGuardNode
from Products.CMFSetup.workflow import _extractDefaultNode
from Products.CMFSetup.workflow import _extractMatchNode

WF_META_TYPES = [
    DCWorkflowDefinition.meta_type,
    CPSWorkflowDefinition.meta_type,
    ]

TRANSITION_BEHAVIORS = {
    10: 'TRANSITION_ALLOWSUB_CREATE',
    11: 'TRANSITION_ALLOWSUB_DELETE',
    12: 'TRANSITION_ALLOWSUB_MOVE',
    13: 'TRANSITION_ALLOWSUB_COPY',
    14: 'TRANSITION_ALLOWSUB_PUBLISHING',
    15: 'TRANSITION_ALLOWSUB_CHECKOUT',
    #
    20: 'TRANSITION_INITIAL_CREATE',
    22: 'TRANSITION_INITIAL_MOVE',
    23: 'TRANSITION_INITIAL_COPY',
    24: 'TRANSITION_INITIAL_PUBLISHING',
    25: 'TRANSITION_INITIAL_CHECKOUT',
    26: 'TRANSITION_ALLOW_CHECKIN',
    #
    31: 'TRANSITION_BEHAVIOR_DELETE',
    32: 'TRANSITION_BEHAVIOR_MOVE',
    33: 'TRANSITION_BEHAVIOR_COPY',
    34: 'TRANSITION_BEHAVIOR_PUBLISHING',
    35: 'TRANSITION_BEHAVIOR_CHECKOUT',
    36: 'TRANSITION_BEHAVIOR_CHECKIN',
    37: 'TRANSITION_BEHAVIOR_FREEZE',
    38: 'TRANSITION_BEHAVIOR_MERGE',
    #
    41: 'TRANSITION_BEHAVIOR_PUSH_DELEGATEES',
    42: 'TRANSITION_BEHAVIOR_POP_DELEGATEES',
    44: 'TRANSITION_BEHAVIOR_WORKFLOW_UP',
    45: 'TRANSITION_BEHAVIOR_WORKFLOW_DOWN',
    48: 'TRANSITION_BEHAVIOR_WORKFLOW_RESET',
    }

STATE_BEHAVIORS = {
    101: 'STATE_BEHAVIOR_PUSH_DELEGATEES',
    102: 'STATE_BEHAVIOR_POP_DELEGATEES',
    103: 'STATE_BEHAVIOR_WORKFLOW_UP',
    104: 'STATE_BEHAVIOR_WORKFLOW_DOWN',
    108: 'STATE_BEHAVIOR_WORKFLOW_RESET',
    }

_pkgdir = package_home(globals())
_xmldir = os.path.join(_pkgdir, 'xml')

_FILENAME = 'workflows.xml'


def exportWorkflowTool(context):
    """ Export worklow tool worklows as a set of XML files.
    """
    site = context.getSite()
    wftc = CPSWorkflowToolConfigurator(site).__of__(site)
    wfdc = CPSWorkflowDefinitionConfigurator(site).__of__(site)
    wf_tool = getToolByName(site, 'portal_workflow')
    text = wftc.generateXML()

    context.writeDataFile(_FILENAME, text, 'text/xml')

    for wf_id in wf_tool.getWorkflowIds():

        wf_dirname = wf_id.replace(' ', '_')
        wf_xml = wfdc.generateWorkflowXML(wf_id)
        wf_scripts = wfdc.getWorkflowScripts(wf_id)

        if wf_xml is not None:
            context.writeDataFile('definition.xml',
                                  wf_xml,
                                  'text/xml',
                                  'workflows/%s' % wf_dirname,
                                  )
            if wf_scripts:
                for filename, script in wf_scripts.items():
                    context.writeDataFile(filename,
                                          script,
                                          'text/plain',
                                          'workflows/%s/scripts' % wf_dirname,
                                          )

    return 'Workflows exported.'


def importWorkflowTool( context ):

    """ Import worflow tool and contained workflow definitions.

    Take care of CPSWorkflow specifics
    """
    site = context.getSite()
    encoding = context.getEncoding()
    tool = getToolByName( site, 'portal_workflow' )

    if context.shouldPurge():

        tool.setDefaultChain( '' )
        if tool._chains_by_type is not None:
            tool._chains_by_type.clear()

        for workflow_id in tool.getWorkflowIds():
            tool._delObject( workflow_id )

    text = context.readDataFile( _FILENAME )

    if text is not None:

        wftc = CPSWorkflowToolConfigurator( site, encoding )
        tool_info = wftc.parseXML( text )

        wfdc = CPSWorkflowDefinitionConfigurator( site )

        for info in tool_info[ 'workflows' ]:

            if info[ 'meta_type' ] in WF_META_TYPES:

                filename = info[ 'filename' ]
                sep = filename.rfind( '/' )
                if sep == -1:
                    wf_text = context.readDataFile( filename )
                else:
                    wf_text = context.readDataFile( filename[sep+1:],
                                                    filename[:sep] )

                ( workflow_id
                , title
                , state_variable
                , initial_state
                , states
                , transitions
                , variables
                , worklists
                , permissions
                , scripts
                ) = wfdc.parseWorkflowXML( wf_text, encoding )

                workflow_id = str( workflow_id ) # No unicode!

                if info['meta_type'] == DCWorkflowDefinition.meta_type:
                    tool._setObject( workflow_id
                                     , DCWorkflowDefinition( workflow_id ) )
                elif info['meta_type'] == CPSWorkflowDefinition.meta_type:
                    tool._setObject( workflow_id
                                     , CPSWorkflowDefinition( workflow_id ) )

                workflow = tool._getOb( workflow_id )

                _initWorkflow( workflow
                               , title
                               , state_variable
                               , initial_state
                               , states
                               , transitions
                               , variables
                               , worklists
                               , permissions
                               , scripts
                               , context
                               )

        for type_id, workflow_ids in tool_info[ 'bindings' ].items():

            chain = ','.join( workflow_ids )
            if type_id is None:
                tool.setDefaultChain( chain )
            else:
                tool.setChainForPortalTypes( ( type_id, ), chain )

    return 'Workflows imported.'


class CPSWorkflowToolConfigurator(WorkflowToolConfigurator):
    """ Synthesize XML description of site's workflow tool.

    Take care of CPSWorkflow psecifics and do not retrict to DCWorkflow
    workflows.
    """
    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'getWorkflowInfo')
    def getWorkflowInfo(self, workflow_id):
        """ Return a mapping describing a given workflow.

        Take CPSWorkflowDefinition objects too
        """
        workflow_tool = getToolByName(self._site, 'portal_workflow')
        workflow = workflow_tool.getWorkflowById(workflow_id)

        workflow_info = {
            'id'          : workflow_id,
            'meta_type'   : workflow.meta_type,
            'title'       : unicode(workflow.title_or_id(), 'iso-8859-15'),
            }

        if workflow.meta_type in WF_META_TYPES:
            workflow_info['filename'] = _getWorkflowFilename(workflow_id)

        return workflow_info

    def _convertWorkflows(self, val):
        for wf in val:
            if wf['meta_type'] in WF_META_TYPES:
                if wf['filename'] == wf['workflow_id']:
                    wf['filename'] = _getWorkflowFilename(wf['filename'])
            else:
                wf['filename'] = None

        return val

InitializeClass(CPSWorkflowToolConfigurator)


class CPSWorkflowDefinitionConfigurator(WorkflowDefinitionConfigurator):
    """ Synthesize XML description of site's workflows.
    """
    security = ClassSecurityInfo()

    def __init__(self, site):
        self._site = site

    #
    # Export
    #

    security.declareProtected(ManagePortal, 'getWorkflowInfo')
    def getWorkflowInfo(self, workflow_id):
        """
        Take CPSWorkflowDefinition objects too
        """
        workflow_tool = getToolByName(self._site, 'portal_workflow')
        workflow = workflow_tool.getWorkflowById(workflow_id)

        workflow_info = {
            'id'          : workflow_id,
            'meta_type'   : workflow.meta_type,
            'title'       : unicode(workflow.title_or_id(), 'iso-8859-15'),
            }

        if workflow.meta_type in WF_META_TYPES:
            # some of the methods used in _extractDCWorkflowInfo are overriden
            self._extractDCWorkflowInfo(workflow, workflow_info)

        return workflow_info

    security.declareProtected(ManagePortal, 'generateWorkflowXML')
    def generateWorkflowXML(self, workflow_id):
        """ Pseudo API.

        Take CPSWorkflowDefinition objects too
        """
        info = self.getWorkflowInfo(workflow_id)

        if info['meta_type'] != CPSWorkflowDefinition.meta_type:
            return None

        return self._workflowConfig(workflow_id=workflow_id)

    security.declarePrivate('_workflowConfig')
    _workflowConfig = PageTemplateFile('wtcWorkflowExport.xml',
                                       _xmldir,
                                       __name__='workflowConfig',
                                       )

    security.declareProtected(ManagePortal, 'getWorkflowScripts')
    def getWorkflowScripts(self, workflow_id):
        """ Return a mapping of workflow scripts, with script names as keys and
        script content as values
        """
        res = {}
        workflow_tool = getToolByName(self._site, 'portal_workflow')
        workflow = workflow_tool.getWorkflowById(workflow_id)
        scripts = self._extractScripts(workflow)
        for script in scripts:
            suffix = _METATYPE_SUFFIXES.get(script['meta_type'], 'py')
            res[script['id'] + '.' + suffix] = script['body']
        return res

    security.declarePrivate('_extractTransitions')
    def _extractTransitions(self, workflow):
        """ Return a sequence of mappings describing DCWorkflow transitions.

        Export transition flags and other properties too
        """
        result = []
        dcwf_result = WorkflowDefinitionConfigurator._extractTransitions(self,
                                                                         workflow)
        # append transitions flags info
        items = workflow.transitions.objectItems()
        items.sort()

        index = 0
        for k, v in items:
            # get already calculated infos
            info = dcwf_result[index]
            index += 1

            # encoding...
            info['title'] = unicode(info['title'], 'iso-8859-15')
            info['description'] = unicode(info['description'], 'iso-8859-15')

            try:
                t_behaviors = v.transition_behavior
            except AttributeError:
                # not a CPS workflow
                t_behaviors = []
            else:
                t_behaviors = [TRANSITION_BEHAVIORS[x] for x in t_behaviors]

            info.update({
                'transition_behavior': t_behaviors,
                # Transitions allowed at destination
                'clone_allowed_transitions': v.clone_allowed_transitions,
                'checkout_allowed_initial_transitions': v.checkout_allowed_initial_transitions,
                'checkin_allowed_transitions': v.checkin_allowed_transitions,
                # Stack workflow transition flags
                'push_on_workflow_variable': v.push_on_workflow_variable,
                'pop_on_workflow_variable': v.pop_on_workflow_variable,
                'workflow_up_on_workflow_variable': v.workflow_up_on_workflow_variable,
                'workflow_down_on_workflow_variable': v.workflow_down_on_workflow_variable,
                'workflow_reset_on_workflow_variable': v.workflow_reset_on_workflow_variable,
                })
            result.append(info)

        return result

    security.declarePrivate( '_extractStates' )
    def _extractStates( self, workflow ):
        """ Return a sequence of mappings describing DCWorkflow states.

        Add state behaviours and stack definitions
        """
        result = []
        dcwf_result = WorkflowDefinitionConfigurator._extractStates(self,
                                                                    workflow)

        items = workflow.states.objectItems()
        items.sort()
        index = 0
        for k, v in items:
            # get already calculated infos
            info = dcwf_result[index]
            index += 1

            # encoding...
            info['title'] = unicode(info['title'], 'iso-8859-15')
            info['description'] = unicode(info['description'], 'iso-8859-15')

            try:
                s_behaviors = v.state_behaviors
            except AttributeError:
                # not a CPS workflow
                s_behaviors = []
            else:
                s_behaviors = [STATE_BEHAVIORS[x] for x in s_behaviors]

            stackdefs_info = []
            try:
                stackdefs = v.getStackDefinitions()
            except AttributeError:
                # not a CPS workflow
                pass
            else:
                for stackdef_id, stackdef in stackdefs.items():

                    managed_roles_info = []
                    managed_roles = stackdef.getManagedRoles()
                    for role in managed_roles:
                        expr = stackdef._managed_role_exprs.get(role, 'python:1')
                        managed_roles_info.append({
                            'name': role,
                            'expression': expr,
                            })
                    stackdef_info = {
                        # stackdef name // also variable name...
                        'id': stackdef_id,
                        'meta_type': stackdef.meta_type,
                        'stack_type': stackdef.getStackDataStructureType(),
                        # XXX AT: supposed to be the same than the stackdef id
                        # as variable is created from it
                        'variable_id': stackdef.getStackWorkflowVariableId(),
                        'manager_stack_ids': stackdef.getManagerStackIds(),
                        'managed_roles': managed_roles_info,
                        }

                    guards = {
                        'empty_stack_manage_guard': stackdef.getEmptyStackManageGuard(),
                        'edit_stack_element_guard': stackdef.getEditStackElementGuard(),
                        'view_stack_element_guard': stackdef.getViewStackElementGuard(),
                        }

                    for guard_id, guard in guards.items():
                        stackdef_info.update({
                            guard_id + '_permissions': guard.permissions,
                            guard_id + '_roles': guard.roles,
                            guard_id + '_groups': guard.groups,
                            guard_id + '_expr': guard.getExprText(),
                            })

                    stackdefs_info.append(stackdef_info)

            info.update({
                'state_behaviors': s_behaviors,
                # later
                'stackdefs': stackdefs_info,
                'push_on_workflow_variable': v.push_on_workflow_variable,
                'pop_on_workflow_variable': v.pop_on_workflow_variable,
                'workflow_up_on_workflow_variable': v.workflow_up_on_workflow_variable,
                'workflow_down_on_workflow_variable': v.workflow_down_on_workflow_variable,
                'workflow_reset_on_workflow_variable': v.workflow_reset_on_workflow_variable,
                })

            result.append(info)

        return result


    def _extractScripts( self, workflow ):
        """ Return a sequence of mappings describing DCWorkflow scripts.

        Scripts are located in the 'scripts' subdirectory
        """
        result = []

        items = workflow.scripts.objectItems()
        items.sort()

        for k, v in items:

            filename = _getScriptFilename( workflow.getId(), k, v.meta_type )

            info = { 'id'                   : k
                   , 'meta_type'            : v.meta_type
                   , 'body'                 : v.read()
                   , 'filename'             : filename
                   }

            result.append( info )

        return result
    #
    # Import
    #

    security.declareProtected(ManagePortal, 'parseWorkflowXML')
    def parseWorkflowXML(self, xml, encoding=None):
        """ Pseudo API.
        """
        dom = domParseString(xml)

        # XXX
        root = dom.getElementsByTagName('cps-workflow')[ 0 ]

        workflow_id = _getNodeAttribute(root, 'workflow_id', encoding)
        title = _getNodeAttribute(root, 'title', encoding)
        state_variable = _getNodeAttribute(root, 'state_variable', encoding)
        try:
            initial_state = _getNodeAttribute(root, 'initial_state', encoding)
        except ValueError:
            # no initial state
            initial_state = None

        states = _extractStateNodes(root)
        transitions = _extractTransitionNodes(root)
        variables = _extractVariableNodes(root)
        worklists = _extractWorklistNodes(root)
        permissions = _extractPermissionNodes(root)
        scripts = _extractScriptNodes(root)

        return (workflow_id
               , title
               , state_variable
               , initial_state
               , states
               , transitions
               , variables
               , worklists
               , permissions
               , scripts
              )


InitializeClass(CPSWorkflowDefinitionConfigurator)

def _initWorkflow( workflow
                   , title
                   , state_variable
                   , initial_state
                   , states
                   , transitions
                   , variables
                   , worklists
                   , permissions
                   , scripts
                   , context
                   ):
    """ Initialize a DC or CPS Workflow using values parsed from XML.
    """
    # XXX AT: maybe workflow shouldnt be created until now so that its meta
    # type is handled in here
    workflow.title = title
    workflow.state_var = state_variable
    workflow.initial_state = initial_state

    permissions = permissions[:]
    permissions.sort()
    workflow.permissions = permissions

    _initDCWorkflowVariables( workflow, variables )
    # overloaded...
    _initWorkflowStates( workflow, states )
    # overloaded...
    _initWorkflowTransitions( workflow, transitions )
    _initDCWorkflowWorklists( workflow, worklists )
    _initDCWorkflowScripts( workflow, scripts, context )


def _initWorkflowStates( workflow, states ):
    """ Initialize DCWorkflow & CPSWorkflow states
    """
    from Globals import PersistentMapping
    if workflow.meta_type == DCWorkflowDefinition.meta_type:
        from Products.DCWorkflow.States import StateDefinition
    elif workflow.meta_type == CPSWorkflowDefinition.meta_type:
        from Products.CPSWorkflow.states import StateDefinition

    for s_info in states:

        id = str( s_info[ 'state_id' ] ) # no unicode!
        s = StateDefinition( id )
        workflow.states._setObject( id, s )
        s = workflow.states._getOb( id )

        s.setProperties( title = s_info[ 'title' ]
                       , description = s_info[ 'description' ]
                       , transitions = s_info[ 'transitions' ]
                       )

        for k, v in s_info[ 'permissions' ].items():
            s.setPermission( k, isinstance(v, list), v )

        gmap = s.group_roles = PersistentMapping()

        for group_id, roles in s_info[ 'groups' ]:
            gmap[ group_id ] = roles

        vmap = s.var_values = PersistentMapping()

        for name, v_info in s_info[ 'variables' ].items():

            value = _convertVariableValue( v_info[ 'value' ]
                                         , v_info[ 'type' ] )

            vmap[ name ] = value

def _initWorkflowTransitions( workflow, transitions ):

    """ Initialize DCWorkflow & CPSWorkflow transitions
    """
    from Globals import PersistentMapping
    if workflow.meta_type == DCWorkflowDefinition.meta_type:
        from Products.DCWorkflow.Transitions import TransitionDefinition
    elif workflow.meta_type == CPSWorkflowDefinition.meta_type:
        from Products.CPSWorkflow.transitions import TransitionDefinition

    for t_info in transitions:

        id = str( t_info[ 'transition_id' ] ) # no unicode!
        t = TransitionDefinition( id )
        workflow.transitions._setObject( id, t )
        t = workflow.transitions._getOb( id )

        trigger_type = list( TRIGGER_TYPES ).index( t_info[ 'trigger' ] )

        action = t_info[ 'action' ]

        guard = t_info[ 'guard' ]
        props = { 'guard_roles' : ';'.join( guard[ 'roles' ] )
                , 'guard_permissions' : ';'.join( guard[ 'permissions' ] )
                , 'guard_groups' : ';'.join( guard[ 'groups' ] )
                , 'guard_expr' : guard[ 'expression' ]
                }

        t.setProperties( title = t_info[ 'title' ]
                       , description = t_info[ 'description' ]
                       , new_state_id = t_info[ 'new_state' ]
                       , trigger_type = trigger_type
                       , script_name = t_info[ 'before_script' ]
                       , after_script_name = t_info[ 'after_script' ]
                       , actbox_name = action[ 'name' ]
                       , actbox_url = action[ 'url' ]
                       , actbox_category = action[ 'category' ]
                       , props = props
                       )

        t.var_exprs = PersistentMapping( t_info[ 'variables' ].items() )


def _extractStateNodes( root, encoding=None ):

    result = []

    for s_node in root.getElementsByTagName( 'state' ):

        info = { 'state_id' : _getNodeAttribute( s_node, 'state_id', encoding )
               , 'title' : _getNodeAttribute( s_node, 'title', encoding )
               , 'description' : _extractDescriptionNode( s_node, encoding )
               }

        info[ 'transitions' ] = [ _getNodeAttribute( x, 'transition_id'
                                                   , encoding )
                                  for x in s_node.getElementsByTagName(
                                                        'exit-transition' ) ]

        info[ 'permissions' ] = permission_map = {}

        for p_map in s_node.getElementsByTagName( 'permission-map' ):

            name = _getNodeAttribute( p_map, 'name', encoding )
            acquired = _getNodeAttributeBoolean( p_map, 'acquired' )

            roles = [ _coalesceTextNodeChildren( x, encoding )
                        for x in p_map.getElementsByTagName(
                                            'permission-role' ) ]

            if not acquired:
                roles = tuple( roles )

            permission_map[ name ] = roles

        info[ 'groups' ] = group_map = []

        for g_map in s_node.getElementsByTagName( 'group-map' ):

            name = _getNodeAttribute( g_map, 'name', encoding )

            roles = [ _coalesceTextNodeChildren( x, encoding )
                        for x in g_map.getElementsByTagName(
                                            'group-role' ) ]

            group_map.append( ( name, tuple( roles ) ) )

        info[ 'variables' ] = var_map = {}

        for assignment in s_node.getElementsByTagName( 'assignment' ):

            name = _getNodeAttribute( assignment, 'name', encoding )
            type_id = _getNodeAttribute( assignment, 'type', encoding )
            value = _coalesceTextNodeChildren( assignment, encoding )

            var_map[ name ] = { 'name'  : name
                              , 'type'  : type_id
                              , 'value' : value
                              }

        result.append( info )

    return result


def _extractTransitionNodes(root, encoding=None):

    result = []

    for t_node in root.getElementsByTagName('transition'):

        info = {
            'transition_id' : _getNodeAttribute(t_node, 'transition_id',
                                                encoding),
            'title' : _getNodeAttribute(t_node, 'title', encoding),
            'description' : _extractDescriptionNode(t_node, encoding),
            'new_state' : _getNodeAttribute(t_node, 'new_state', encoding),
            'trigger' : _getNodeAttribute(t_node, 'trigger', encoding),
            'before_script' : _getNodeAttribute(t_node, 'before_script',
                                                encoding),
            'after_script' : _getNodeAttribute(t_node, 'after_script',
                                               encoding),
            'action' : _extractActionNode(t_node, encoding),
            'guard' : _extractGuardNode(t_node, encoding),
            ## transition behaviours
            #'transition_behavior': _getNodeAttribute(t_node,
            #                                         'transition_behavior',
            #                                         encoding),
            ## Transitions allowed at destination
            #'clone_allowed_transitions': _getNodeAttribute(t_node,
            #                                               'clone_allowed_transitions',
            #                                               encoding),
            #'checkout_allowed_initial_transitions': _getNodeAttribute(t_node,
            #                                                          'checkout_allowed_initial_transitions',
            #                                                          encoding),
            #'checkin_allowed_transitions': _getNodeAttribute(t_node,
            #                                                 'checkin_allowed_transitions',
            #                                                 encoding),
            ## Stack workflow transition flags
            #'push_on_workflow_variable': _getNodeAttribute(t_node,
            #                                               'push_on_workflow_variable',
            #                                               encoding),
            #'pop_on_workflow_variable': _getNodeAttribute(t_node,
            #                                              'pop_on_workflow_variable',
            #                                              encoding),
            #'workflow_up_on_workflow_variable': _getNodeAttribute(t_node,
            #                                                      'workflow_up_on_workflow_variable',
            #                                                      encoding),
            #'workflow_down_on_workflow_variable': _getNodeAttribute(t_node,
            #                                                        'workflow_down_on_workflow_variable',
            #                                                        encoding),
            #'workflow_reset_on_workflow_variable': _getNodeAttribute(t_node,
            #                                                         'workflow_reset_on_workflow_variable',
            #                                                         encoding),
            }

        info['variables'] = var_map = {}

        for assignment in t_node.getElementsByTagName('assignment'):

            name = _getNodeAttribute(assignment, 'name', encoding)
            expr = _coalesceTextNodeChildren(assignment, encoding)
            var_map[name] = expr

        LOG("_extractTransitionNodes", DEBUG, "info=%s"%(info,))
        result.append(info)

    return result

def _getScriptFilename( workflow_id, script_id, meta_type ):

    """ Return the name of the file which holds the script.
    """
    wf_dir = workflow_id.replace( ' ', '_' )
    suffix = _METATYPE_SUFFIXES[ meta_type ]
    return 'workflows/%s/scripts/%s.%s' % ( wf_dir, script_id, suffix )
