#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
# $Id$
"""Base Test case for workflows imported/exported with CMFSetup
"""

import os

from Testing import ZopeTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from OFS.Folder import Folder

from Products.PythonScripts.PythonScript import PythonScript
# this import adds the dc_workflow workflow factory
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
# this import adds the cps_workflow workflow factory
from Products.CPSWorkflow.workflow import WorkflowDefinition as CPSWorkflowDefinition

# install products
ZopeTestCase.installProduct('CPSWorkflow', quiet=1)

class DummyRoot(Folder):
    def getPhysicalRoot(self):
        return self

class SetupWorkflowTestCase(BaseRegistryTests):
    """Test workflows setup with CMFSetup
    """

    #
    # Test case methods
    #

    def setUp(self):
        BaseRegistryTests.setUp(self)

        from Products.CPSWorkflow.workflowtool import addWorkflowTool
        addWorkflowTool(self.root)

        from Products.CMFCore.WorkflowTool import addWorkflowFactory
        addWorkflowFactory(DCWorkflowDefinition, id='dc_workflow',
                           title = '(Web-configurable workflow)')
        addWorkflowFactory(CPSWorkflowDefinition, id='cps_workflow',
                           title = '(Web-configurable workflow for CPS)')

        self.wftool = self.root.portal_workflow

    def tearDown(self):
        self.root._delObject('portal_workflow')
        from Products.CMFCore.WorkflowTool import _removeWorkflowFactory
        _removeWorkflowFactory(DCWorkflowDefinition, id='dc_workflow')
        _removeWorkflowFactory(CPSWorkflowDefinition, id='cps_workflow')

        self.app.REQUEST.close() # should be done by BaseRegistryTests
        BaseRegistryTests.tearDown(self)

    def _setupAdapters(self):
        from zope.app.testing import ztapi
        from zope.interface import classImplements
        from Products.GenericSetup.interfaces import ISetupEnviron
        from Products.GenericSetup.interfaces import IBody

        from Products.CMFCore.interfaces import IWorkflowTool
        from Products.CMFCore.exportimport.workflow import (
            WorkflowToolXMLAdapter)
        ztapi.provideAdapter((IWorkflowTool, ISetupEnviron), IBody,
                             WorkflowToolXMLAdapter)

        from Products.PythonScripts.PythonScript import PythonScript
        from Products.GenericSetup.PythonScripts.interfaces import (
            IPythonScript)
        from Products.GenericSetup.PythonScripts.exportimport import (
            PythonScriptBodyAdapter)
        ztapi.provideAdapter((IPythonScript, ISetupEnviron), IBody,
                             PythonScriptBodyAdapter)
        classImplements(PythonScript, IPythonScript)

        from Products.CPSWorkflow.interfaces import ICPSWorkflowDefinition
        from Products.CPSWorkflow.exportimport import (
            CPSWorkflowDefinitionBodyAdapter)
        ztapi.provideAdapter((ICPSWorkflowDefinition, ISetupEnviron), IBody,
                             CPSWorkflowDefinitionBodyAdapter)

    def _setupRegistrations(self):
        # Five-like registration, will move to ZCML later
        import Products
        from Products.CMFCore.permissions import ManagePortal
        from zope.interface import implementedBy
        cls = CPSWorkflowDefinition
        meta_type = cls.meta_type
        if not [1 for x in Products.meta_types if x['name'] == meta_type]:
            info = {'name': meta_type,
                    'action': '',
                    'product': 'CPSWorkflow',
                    'permission': ManagePortal, #XXX
                    'visibility': None,
                    'interfaces': tuple(implementedBy(cls)),
                    'instance': cls,
                    'container_filter': None}
            Products.meta_types += (info,)

    #
    # Helper methods
    #

    def assertEqual(self, first, second):
        """Overloaded to sort list items
        """
        if isinstance(first, list) and isinstance(second, list):
            first.sort()
            second.sort()
        return BaseRegistryTests.assertEqual(self, first, second)

    def _getXMLdirectory(self):
        """Get the directory path where wml files are kept

        This method is supposed to be overloaded
        """
        # default dir
        return 'xml/'

    def _getFileData(self, path):
        """Get the file content from its path relative to here (tests directory)
        """
        from Products.CPSWorkflow import tests as here
        xml_dir = self._getXMLdirectory()
        test_file = os.path.join(here.__path__[0], xml_dir, path)
        data = open(test_file, 'r').read()
        return data

    def _setUpTestWorkflow(self, wfdef):
        # wf
        wfid = wfdef['wfid']
        wftype = wfdef['wftype']
        self.wftool.manage_addWorkflow(id=wfid, workflow_type=wftype)
        wf = self.wftool[wfid]

        # permissions
        for p in wfdef['permissions']:
            wf.addManagedPermission(p)

        # variables
        wf.variables.setStateVar(wfdef['state_var'])
        variables = wfdef['variables']
        for varid, vardef in variables.items():
            wf.variables.addVariable(varid)
            var = wf.variables[varid]
            var.setProperties(**vardef)

        # states
        states = wfdef['states']
        for stateid, statedef in states.items():
            wf.states.addState(stateid)
            state = wf.states.get(stateid)
            for permission in statedef['permissions'].keys():
                state.setPermission(permission, 0,
                                    statedef['permissions'][permission])
            state.setProperties(**statedef)
            # XXX add variables management

        # transitions
        transitions = wfdef['transitions']
        for transid, transdef in transitions.items():
            wf.transitions.addTransition(transid)
            trans = wf.transitions.get(transid)
            trans.setProperties(**transdef)
            # variables
            variables = transdef.get('variables', {})
            for var_id, expr_text in variables.items():
                trans.addVariable(var_id, expr_text)

        # scripts
        scripts = wfdef['scripts']
        for scriptid, scriptdef in scripts.items():
            wf.scripts._setObject(scriptid, PythonScript(scriptid))
            script = wf.scripts[scriptid]
            script.write(scriptdef['script'])
            for attribute in ('title', '_proxy_roles', '_owner'):
                if scriptdef.has_key(attribute):
                    setattr(script, attribute, scriptdef[attribute])

