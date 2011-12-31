# (C) Copyright 2010 CPS-CMS Community <http://cps-cms.org/>
# Authors:
#     G. Racinet <georges@racinet.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest

from Products.CPSDefault.tests.CPSTestCase import CPSPermWorkflowTestCase

from Products.CMFCore.utils import getToolByName

class WorkflowToolIntegrationTests(CPSPermWorkflowTestCase):

    def afterSetUp(self):
        CPSPermWorkflowTestCase.afterSetUp(self)
        self.login('manager')

    def test_content_before_wf(self):
        # see #2495 (here we test the default behavior)
        # we add a workflow variable duplicating the proxy's content Title.
        # At creation time, this cannot work if insertion is done before
        # content creation. Our variable expression is made to return 'missing'
        # in that case

        wf = self.wftool['workspace_content_wf']
        wf.variables.addVariable('titlevar')
        wf.variables['titlevar'].setProperties(
            "This var duplicates content Title",
            for_status=True, # have it updated in transitions
            default_expr="python:state_change.object.getContent() and "
            "state_change.object.getContent().getDataModel()['Title'] "
            "or 'missing'")

        # now create a File document and check the workflow var on it
        ws = self.portal.workspaces
        self.wftool.invokeFactoryFor(ws, 'File', 'a_file', Title='the tite')
        proxy = ws.a_file
        self.assertEquals(self.wftool.getInfoFor(proxy, 'titlevar'),
                          proxy.getContent().getDataModel()['Title'])

        # to validate that this test is meaningful, we invert the ordering
        ws = self.portal.workspaces
        self.wftool.invokeFactoryFor(ws, 'File', 'bad_file',
                                     Title='the tite',
                                     wf_before_content=True)

        self.assertEquals(self.wftool.getInfoFor(ws.bad_file, 'titlevar'),
                          'missing')


    def test_wf_before_content(self):
        # see #2495 (here we test the new optionnal behavior)

        # change the Title field so that it duplicates the workflow state.
        # this would be None if insertion is done before datamodel commit
        stool = getToolByName(self.portal, 'portal_schemas')
        field = stool['metadata']['Title']
        field.manage_changeProperties(
            write_process_expr="python:portal.portal_workflow."
            "getInfoFor(proxy, 'review_state')")

        # now create a File document and check that Title has indeed been set
        # to the review state value
        ws = self.portal.workspaces
        self.wftool.invokeFactoryFor(ws, 'File', 'a_file',
                                     wf_before_content=True)
        proxy = ws.a_file
        self.assertEquals(proxy.getContent().getDataModel()['Title'],
                          self.wftool.getInfoFor(proxy, 'review_state'))

        # now check that the assumptions we've made are true: with the default
        # ordering, we'd get None. If that'd become False, the test above
        # should be updated.
        ws = self.portal.workspaces
        self.wftool.invokeFactoryFor(ws, 'File', 'bad_file')

        self.assertEquals(ws.bad_file.getContent().getDataModel()['Title'],
                          None)


def test_suite():
    return unittest.makeSuite(WorkflowToolIntegrationTests)
