# Copyright (c) 2005 Nuxeo SAS <http://nuxeo.com>
# Authors: Anahide Tchertchian <at@nuxeo.com>
#          Florent Guillaume <fg@nuxeo.com>
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
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
# $Id$
"""Workflow tool import/export for GenericSetup

Knows about :
- transition and state flags
- stacks
"""

import os
from xml.dom.minidom import parseString

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Globals import package_home
from Globals import PersistentMapping
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

# utilities formerly in CMFSetup
from Products.DCWorkflow.exportimport import _getNodeAttribute
from Products.DCWorkflow.exportimport import _queryNodeAttribute
from Products.DCWorkflow.exportimport import _getNodeAttributeBoolean
from Products.DCWorkflow.exportimport import _coalesceTextNodeChildren
from Products.DCWorkflow.exportimport import _extractDescriptionNode

from Products.DCWorkflow.exportimport import TRIGGER_TYPES

from Products.DCWorkflow.exportimport import WorkflowDefinitionConfigurator
from Products.DCWorkflow.exportimport import _initDCWorkflowVariables
from Products.DCWorkflow.exportimport import _initDCWorkflowWorklists
from Products.DCWorkflow.exportimport import _initDCWorkflowScripts

from Products.DCWorkflow.exportimport import _convertVariableValue
from Products.DCWorkflow.exportimport import _extractVariableNodes
from Products.DCWorkflow.exportimport import _extractWorklistNodes
from Products.DCWorkflow.exportimport import _extractPermissionNodes
from Products.DCWorkflow.exportimport import _extractScriptNodes
from Products.DCWorkflow.exportimport import _extractActionNode
from Products.DCWorkflow.exportimport import _extractGuardNode

from Products.CPSWorkflow.workflow import (
    WorkflowDefinition as CPSWorkflowDefinition)
from Products.CPSWorkflow.states import (
    StateDefinition as CPSStateDefinition)
from Products.CPSWorkflow.transitions import (
    TransitionDefinition as CPSTransitionDefinition)

from Products.GenericSetup.utils import BodyAdapterBase
from Products.GenericSetup.utils import XMLAdapterBase

from Products.CPSWorkflow.constants import TRANSITION_FLAGS_EXPORT
from Products.CPSWorkflow.constants import TRANSITION_FLAGS_IMPORT
from Products.CPSWorkflow.constants import STATE_FLAGS_EXPORT
from Products.CPSWorkflow.constants import STATE_FLAGS_IMPORT


from zope.component import adapts
from zope.interface import implements
from Products.CPSWorkflow.interfaces import ICPSWorkflowDefinition
from Products.CPSWorkflow.interfaces import ILocalWorkflowConfiguration
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron

_pkgdir = package_home(globals())
_xmldir = os.path.join(_pkgdir, 'xml')


class CPSWorkflowDefinitionBodyAdapter(BodyAdapterBase):
    """Body importer and export for CPSWorkflowDefinition.
    """

    adapts(ICPSWorkflowDefinition, ISetupEnviron)
    implements(IBody)

    mime_type = 'text/xml'
    suffix = '/definition.xml'

    def _exportBody(self):
        """Export the object as a file body.
        """
        wfdc = CPSWorkflowDefinitionConfigurator(self.context)
        wfdc = wfdc.__of__(self.context) # need aq context to use zpt
        return wfdc.generateWorkflowXML()

    def _importBody(self, body):
        """Import the object from the file body.
        """
        encoding = 'utf-8'
        wfdc = CPSWorkflowDefinitionConfigurator(self.context)

        (workflow_id,
         title,
         state_variable,
         initial_state,
         states,
         transitions,
         variables,
         worklists,
         permissions,
         scripts,
         ) = wfdc.parseWorkflowXML(body, encoding)

        _initCPSWorkflow(self.context,
                         title,
                         state_variable,
                         initial_state,
                         states,
                         transitions,
                         variables,
                         worklists,
                         permissions,
                         scripts,
                         self.environ)

    body = property(_exportBody, _importBody)


class CPSWorkflowDefinitionConfigurator(WorkflowDefinitionConfigurator):
    """ Synthesize XML description of site's workflows.
    """
    security = ClassSecurityInfo()

    #
    # Export
    #

    def getWorkflowInfo(self, workflow_id):
        """Get info on a CPS Workflow Definition.
        """
        workflow = self._obj
        meta_type = workflow.meta_type
        workflow_info = {
            'id': workflow_id,
            'meta_type': meta_type,
            'title': workflow.title_or_id().encode('iso-8859-15'),
            }

        if meta_type == CPSWorkflowDefinition.meta_type:
            # Calls overriden methods (for states, transitions)
            self._extractDCWorkflowInfo(workflow, workflow_info)

            # Sort permissions
            permissions = list(workflow_info['permissions'])
            permissions.sort()
            workflow_info['permissions'] = permissions

        return workflow_info

    _workflowConfig = PageTemplateFile('cpswfexport.xml',
                                       _xmldir, __name__='workflowConfig')

    def _extractTransitions(self, workflow):
        """Return a sequence of mappings describing DCWorkflow transitions.

        In addition to DCWorkflow export, adds transition flags and
        stack properties.
        """
        result = WorkflowDefinitionConfigurator._extractTransitions(
            self, workflow)

        for info in result:
            v = workflow.transitions[info['id']]

            # encoding...
            info['title'] = info['title'].encode('iso-8859-15')
            info['description'] = info['description'].encode('iso-8859-15')

            t_behaviors = [TRANSITION_FLAGS_EXPORT[b]
                           for b in v.transition_behavior]

            info.update({
                'transition_behavior': t_behaviors,

                # Transitions allowed at destination
                'clone_allowed_transition':
                    v.clone_allowed_transitions,
                'checkout_allowed_initial_transition':
                    v.checkout_allowed_initial_transitions,
                'checkin_allowed_transition':
                    v.checkin_allowed_transitions,

                # Stack workflow transition flags
                'push_on_workflow_variable':
                    v.push_on_workflow_variable,
                'pop_on_workflow_variable':
                    v.pop_on_workflow_variable,
                'workflow_up_on_workflow_variable':
                    v.workflow_up_on_workflow_variable,
                'workflow_down_on_workflow_variable':
                    v.workflow_down_on_workflow_variable,
                'workflow_reset_on_workflow_variable':
                    v.workflow_reset_on_workflow_variable,
                })

        return result

    def _extractStates(self, workflow):
        """Return a sequence of mappings describing DCWorkflow states.

        In addition to DCWorkflow export, adds state behaviours and
        stack definitions.
        """
        result = WorkflowDefinitionConfigurator._extractStates(
            self, workflow)

        for info in result:
            v = workflow.states[info['id']]

            # encoding...
            info['title'] = info['title'].encode('iso-8859-15')
            info['description'] = info['description'].encode('iso-8859-15')

            s_behaviors = [STATE_FLAGS_EXPORT[b] for b in v.state_behaviors]

            stackdefs_info = []
            stackdefs = v.getStackDefinitions()
            for stackdef_id, stackdef in stackdefs.items():
                managed_roles = []
                for role in stackdef.getManagedRoles():
                    expr = stackdef._managed_role_exprs.get(role, 'python:1')
                    managed_roles.append({
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
                    'managed_roles': managed_roles,
                    }

                guards = {
                    'empty_stack_manage_guard':
                        stackdef.getEmptyStackManageGuard(),
                    'edit_stack_element_guard':
                        stackdef.getEditStackElementGuard(),
                    'view_stack_element_guard':
                        stackdef.getViewStackElementGuard(),
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
                'stackdefs': stackdefs_info,
                'push_on_workflow_variable': v.push_on_workflow_variable,
                'pop_on_workflow_variable': v.pop_on_workflow_variable,
                'workflow_up_on_workflow_variable':
                    v.workflow_up_on_workflow_variable,
                'workflow_down_on_workflow_variable':
                    v.workflow_down_on_workflow_variable,
                'workflow_reset_on_workflow_variable':
                    v.workflow_reset_on_workflow_variable,
                })

        return result

    #
    # Import
    #

    def parseWorkflowXML(self, xml, encoding=None):
        """Parse workflow XML.
        """
        from xml.parsers.expat import ExpatError
        try:
            dom = parseString(xml)
        except ExpatError, err:
            raise ExpatError("%s: %s"%(err, xml))

        root = dom.getElementsByTagName('cps-workflow')[0]

        workflow_id = _getNodeAttribute(root, 'workflow_id', encoding)
        title = _getNodeAttribute(root, 'title', encoding)
        state_variable = _getNodeAttribute(root, 'state_variable', encoding)
        initial_state = _queryNodeAttribute(root, 'initial_state', None,
                                            encoding)

        states = _extractCPSStateNodes(root, encoding)
        transitions = _extractCPSTransitionNodes(root, encoding)
        variables = _extractVariableNodes(root, encoding)
        worklists = _extractWorklistNodes(root, encoding)
        permissions = _extractPermissionNodes(root, encoding)
        scripts = _extractScriptNodes(root, encoding)

        return (workflow_id,
                title,
                state_variable,
                initial_state,
                states,
                transitions,
                variables,
                worklists,
                permissions,
                scripts)


InitializeClass(CPSWorkflowDefinitionConfigurator)

def _initCPSWorkflow(workflow,
                     title,
                     state_variable,
                     initial_state,
                     states,
                     transitions,
                     variables,
                     worklists,
                     permissions,
                     scripts,
                     context):
    """Initialize a CPS Workflow using values parsed from XML.
    """
    workflow.title = title
    workflow.state_var = state_variable
    workflow.initial_state = initial_state

    permissions = list(permissions)
    permissions.sort()
    workflow.permissions = tuple(permissions)

    _initDCWorkflowVariables(workflow, variables)
    _initCPSWorkflowStates(workflow, states)
    _initCPSWorkflowTransitions(workflow, transitions)
    _initDCWorkflowWorklists(workflow, worklists)
    _initDCWorkflowScripts(workflow, scripts, context)


def _initCPSWorkflowStates(workflow, states):
    """Initialize CPSWorkflow states.
    """
    for s_info in states:
        id = str(s_info['state_id']) # no unicode!
        s = CPSStateDefinition(id)
        if not workflow.states.hasObject(id):
            workflow.states._setObject(id, s)
            s = workflow.states._getOb(id)

            s.setProperties(
                title = s_info['title'],
                description = s_info['description'],
                transitions = s_info['transitions'],
                # CPS:
                state_behaviors = [STATE_FLAGS_IMPORT[b]
                                   for b in s_info['state_behaviors']],
                push_on_workflow_variable = s_info['push_on_workflow_variable'],
                pop_on_workflow_variable = s_info['pop_on_workflow_variable'],
                workflow_up_on_workflow_variable =
                    s_info['workflow_up_on_workflow_variable'],
                workflow_down_on_workflow_variable =
                    s_info['workflow_down_on_workflow_variable'],
                workflow_reset_on_workflow_variable =
                    s_info['workflow_reset_on_workflow_variable'],
                stackdefs = s_info['stackdefs'],
                )

            for k, v in s_info['permissions'].items():
                s.setPermission(k, isinstance(v, list), v)

            s.group_roles = PersistentMapping(s_info['groups'])

            s.var_values = PersistentMapping()
            for name, v_info in s_info['variables'].items():
                value = _convertVariableValue(v_info['value'],
                                              v_info['type'])
                s.var_values[name] = value

def _initCPSWorkflowTransitions(workflow, transitions):
    """Initialize CPSWorkflow transitions.
    """
    for t_info in transitions:
        id = str(t_info['transition_id']) # no unicode!
        t = CPSTransitionDefinition(id)
        if not workflow.transitions.hasObject(id):
            workflow.transitions._setObject(id, t)
            t = workflow.transitions._getOb(id)

            trigger_type = list(TRIGGER_TYPES).index(t_info['trigger'])

            action = t_info['action']

            guard = t_info['guard']
            props = {'guard_roles': ';'.join(guard['roles']),
                     'guard_permissions': ';'.join(guard['permissions']),
                     'guard_groups': ';'.join(guard['groups']),
                     'guard_expr': guard['expression'],
                    }

            t.setProperties(
                title = t_info['title'],
                description = t_info['description'],
                new_state_id = t_info['new_state'],
                trigger_type = trigger_type,
                script_name = t_info['before_script'],
                after_script_name = t_info['after_script'],
                actbox_name = action['name'],
                actbox_url = action['url'],
                actbox_category = action['category'],
                props = props,
                # CPS:
                transition_behavior = [TRANSITION_FLAGS_IMPORT[b]
                                       for b in t_info['transition_behavior']],
                clone_allowed_transitions = t_info['clone_allowed_transition'],
                checkout_allowed_initial_transitions =
                    t_info['checkout_allowed_initial_transition'],
                checkin_allowed_transitions =
                    t_info['checkin_allowed_transition'],
                push_on_workflow_variable = t_info['push_on_workflow_variable'],
                pop_on_workflow_variable = t_info['pop_on_workflow_variable'],
                workflow_up_on_workflow_variable =
                    t_info['workflow_up_on_workflow_variable'],
                workflow_down_on_workflow_variable =
                    t_info['workflow_down_on_workflow_variable'],
                workflow_reset_on_workflow_variable =
                    t_info['workflow_reset_on_workflow_variable'],
                )

            t.var_exprs = PersistentMapping(t_info['variables'].items())


def _extractCPSStateNodes(root, encoding=None):
    result = []
    for s_node in root.getElementsByTagName('state'):
        info = {'state_id': _getNodeAttribute(s_node, 'state_id', encoding),
                'title': _getNodeAttribute(s_node, 'title', encoding),
                'description': _extractDescriptionNode(s_node, encoding),
                }

        info['transitions'] = [_getNodeAttribute(x, 'transition_id', encoding)
                               for x in s_node.getElementsByTagName(
                                                        'exit-transition')]

        info['permissions'] = permission_map = {}
        for p_map in s_node.getElementsByTagName('permission-map'):
            name = _getNodeAttribute(p_map, 'name', encoding)
            acquired = _getNodeAttributeBoolean(p_map, 'acquired')
            roles = [_coalesceTextNodeChildren(x, encoding)
                     for x in p_map.getElementsByTagName('permission-role')]
            if not acquired:
                roles = tuple(roles)
            permission_map[name] = roles

        info['groups'] = group_map = []
        for g_map in s_node.getElementsByTagName('group-map'):
            name = _getNodeAttribute(g_map, 'name', encoding)
            roles = [_coalesceTextNodeChildren(x, encoding)
                     for x in g_map.getElementsByTagName('group-role')]
            group_map.append((name, tuple(roles)))

        info['variables'] = var_map = {}
        for assignment in s_node.getElementsByTagName('assignment'):
            name = _getNodeAttribute(assignment, 'name', encoding)
            type_id = _getNodeAttribute(assignment, 'type', encoding)
            value = _coalesceTextNodeChildren(assignment, encoding)
            var_map[name] = {'name': name,
                             'type': type_id,
                             'value': value,
                             }

        # CPS:
        # state behaviours
        behavior_elements = s_node.getElementsByTagName('state-behavior')
        info['state_behaviors'] = [_getNodeAttribute(x, 'behavior_id',
                                                     encoding)
                                   for x in behavior_elements]

        # Stack workflow state flags
        keylist = [
            'push_on_workflow_variable',
            'pop_on_workflow_variable',
            'workflow_up_on_workflow_variable',
            'workflow_down_on_workflow_variable',
            'workflow_reset_on_workflow_variable',
            ]
        for key in keylist:
            elt = key.replace('_', '-')
            stack_vars = s_node.getElementsByTagName(elt)
            info[key] = [_getNodeAttribute(x, 'variable_id', encoding)
                         for x in stack_vars]

        # Stack definitions
        info['stackdefs'] = _extractStackDefinitionNodes(s_node, encoding)

        result.append(info)

    return result


def _extractCPSTransitionNodes(root, encoding=None):
    result = []
    for t_node in root.getElementsByTagName('transition'):
        info = {
            'transition_id': _getNodeAttribute(t_node, 'transition_id',
                                               encoding),
            'title': _getNodeAttribute(t_node, 'title', encoding),
            'description': _extractDescriptionNode(t_node, encoding),
            'new_state': _getNodeAttribute(t_node, 'new_state', encoding),
            'trigger': _getNodeAttribute(t_node, 'trigger', encoding),
            'before_script': _getNodeAttribute(t_node, 'before_script',
                                               encoding),
            'after_script': _getNodeAttribute(t_node, 'after_script',
                                              encoding),
            'action': _extractActionNode(t_node, encoding),
            'guard': _extractGuardNode(t_node, encoding),
            }

        info['variables'] = var_map = {}
        for assignment in t_node.getElementsByTagName('assignment'):
            name = _getNodeAttribute(assignment, 'name', encoding)
            expr = _coalesceTextNodeChildren(assignment, encoding)
            var_map[name] = expr

        # CPS:

        # transition behaviours
        behavior_elements = t_node.getElementsByTagName('transition-behavior')
        info['transition_behavior'] = [_getNodeAttribute(x, 'behavior_id',
                                                         encoding)
                                       for x in behavior_elements]

        # Transitions allowed at destination
        keylist = [
            'clone_allowed_transition',
            'checkout_allowed_initial_transition',
            'checkin_allowed_transition',
            ]
        for key in keylist:
            elt = key.replace('_', '-')
            dest_trans = t_node.getElementsByTagName(elt)
            info[key] = [_getNodeAttribute(x, 'transition_id', encoding)
                         for x in dest_trans]

        # Stack workflow transition flags
        keylist = [
            'push_on_workflow_variable',
            'pop_on_workflow_variable',
            'workflow_up_on_workflow_variable',
            'workflow_down_on_workflow_variable',
            'workflow_reset_on_workflow_variable',
            ]
        for key in keylist:
            elt = key.replace('_', '-')
            stack_vars = t_node.getElementsByTagName(elt)
            info[key] = [_getNodeAttribute(x, 'variable_id', encoding)
                         for x in stack_vars]

        result.append(info)

    return result


def _extractStackDefinitionNodes(root, encoding=None):
    result = {}
    nodes = root.getElementsByTagName('stack-definition')
    for node in nodes:
        # attributes
        stackdef_id = _getNodeAttribute(node, 'stackdef_id', encoding)
        stackdef_id = str(stackdef_id) # no unicode!
        var_id = _getNodeAttribute(node, 'variable_id', encoding)
        var_id = str(var_id) # no unicode !
        info = {
            'stackdef_type': _getNodeAttribute(node, 'meta_type', encoding),
            'stack_type': _getNodeAttribute(node, 'stack_type', encoding),
            'var_id': var_id,
            'manager_stack_ids':
                [_getNodeAttribute(x, 'stack_id', encoding)
                 for x in node.getElementsByTagName('manager-stack-id')],
            'managed_role_exprs': _extractCPSManagedRolesNode(node, encoding),
            'empty_stack_manage_guard': _extractCPSGuardNode(
                node, 'empty-stack-manage-guard', encoding),
            'edit_stack_element_guard': _extractCPSGuardNode(
                node, 'edit-stack-element-guard', encoding),
            'view_stack_element_guard': _extractCPSGuardNode(
                node, 'view-stack-element-guard', encoding),
            }
        result[stackdef_id] = info

    return result


def _extractCPSGuardNode(parent, guard_name, encoding=None):
    """
    Extract a guard node, possible to specify the guard name in parameters
    """

    nodes = parent.getElementsByTagName(guard_name)
    assert len(nodes) <= 1, nodes

    if not nodes:
        return {'permissions': (), 'roles': (), 'groups': (), 'expr': ''}

    node = nodes[0]

    expr_nodes = node.getElementsByTagName('guard-expression')
    assert len(expr_nodes) <= 1, expr_nodes

    if expr_nodes:
        expr_text = _coalesceTextNodeChildren(expr_nodes[0] , encoding)
    else:
        expr_text = ''

    guard_perm_nodes = node.getElementsByTagName('guard-permission')
    guard_role_nodes = node.getElementsByTagName('guard-role')
    guard_group_nodes = node.getElementsByTagName('guard-group')
    return {
        'guard_permissions': ';'.join([_coalesceTextNodeChildren(x, encoding)
                                       for x in guard_perm_nodes]),
        'guard_roles': ';'.join([_coalesceTextNodeChildren(x, encoding)
                                 for x in guard_role_nodes]),
        'guard_groups': ';'.join([_coalesceTextNodeChildren(x, encoding)
                                  for x in guard_group_nodes]),
        'guard_expr': expr_text,
        }

def _extractCPSManagedRolesNode(parent, encoding):
    """
    Extract managed roles expressions in stack definitions
    """

    nodes = parent.getElementsByTagName('managed-roles')
    assert len(nodes) <= 1, nodes

    if not nodes:
        return {}

    roles_node = nodes[0]

    res = {}
    nodes = roles_node.getElementsByTagName('managed-role')
    for node in nodes:
        name = _getNodeAttribute(node, 'name', encoding)
        expression = _getNodeAttribute(node, 'expression', encoding)
        res[name] = expression

    return res


class LocalWorkflowConfigurationXMLAdapter(XMLAdapterBase):
    """XML importer and export for CPS Local Workflow Configuration.
    """

    adapts(ILocalWorkflowConfiguration, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = 'cpsworkflow'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractChains())
        self._logger.info("Local workflow configuration exported.")
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeChains()
        self._initChains(node)
        self._logger.info("Local workflow configuration imported.")

    node = property(_exportNode, _importNode)

    def _extractChains(self):
        conf = self.context
        fragment = self._doc.createDocumentFragment()
        local, below = conf.getChains()
        for mapping, tag in ((local, 'local-workflows'),
                             (below, 'below-workflows')):
            if not mapping:
                continue
            node = self._doc.createElement(tag)
            items = mapping.items()
            items.sort()
            for portal_type, chain in items:
                child = self._doc.createElement('type')
                child.setAttribute('name', portal_type)
                child.setAttribute('wf', chain)
                node.appendChild(child)
        return fragment

    def _purgeChains(self):
        self.context.clear()

    def _initChains(self, node):
        conf = self.context
        local, below = {}, {}
        for child in node.childNodes:
            if child.nodeName == 'local-workflows':
                mapping = local
            elif child.nodeName == 'below-workflows':
                mapping = below
            else:
                continue
            for subchild in child.childNodes:
                if subchild.nodeName != 'type':
                    continue
                portal_type = str(subchild.getAttribute('name'))
                chain = str(subchild.getAttribute('wf'))
                mapping[portal_type] = chain
        conf.setChains(local, below)
