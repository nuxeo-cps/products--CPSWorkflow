#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# (C) Copyright 2004-2005 Nuxeo SARL <http://nuxeo.com>
# Author: Julien Anguenot <ja@nuxeo.com>
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

import os
import string
import unittest
from Testing import ZopeTestCase

ZopeTestCase.installProduct('CPSWorkflow')

from Products.CMFDefault.Portal import manage_addCMFSite
from Products.CMFCore.DirectoryView import createDirectoryView

from Products.CPSWorkflow.stack import Stack
from Products.CPSWorkflow.basicstacks import SimpleStack
from Products.CPSWorkflow.basicstacks import HierarchicalStack

SKINS = {'cps_workflow_default':
         'Products/CPSWorkflow/skins/cps_workflow_default',
         }

class StackRenderingTestCase(ZopeTestCase.PortalTestCase):

    portal_name = 'portal'

    def getPortal(self):
        if not hasattr(self.app, self.portal_name):
            manage_addCMFSite(self.app,
                              self.portal_name)
        return self.app[self.portal_name]

    def afterSetUp(self):
        self.portal = self.getPortal()
        self.verifySkins(SKINS)
        self._refreshSkinData()

    def verifySkins(self, skins):
        """Install or update skins.

        <skins> parameter is a dictionary of {<skin_name>: <skin_path>),}"""

        skin_installed = 0
        for skin, path in skins.items():
            path = path.replace('/', os.sep)
            if skin in self.portal.portal_skins.objectIds():
                dv = self.portal.portal_skins[skin]
                oldpath = dv.getDirPath()
                if oldpath == path:
                    pass
                else:
                    dv.manage_properties(dirpath=path)
            else:
                skin_installed = 1
                # Hack to Fix CMF 1.5 incompatibility
                if path.startswith("Products/"):
                    path = path[len("Products/"):]
                createDirectoryView(self.portal.portal_skins, path, skin)

        if skin_installed:
            all_skins = self.portal.portal_skins.getSkinPaths()
            for skin_name, skin_path in all_skins:
                # Plone skin names are needed to install
                # CPSIO skins on a Plone site when exporting a Plone site.
                if skin_name not in  ['Basic',
                                      'CPSSkins',
                                      'Plone Default',
                                      'Plone Tableless']:
                    continue
                path = [x.strip() for x in skin_path.split(',')]
                path = [x for x in path if x not in skins.keys()] # strip all
                if path and path[0] == 'custom':
                    path = path[:1] + \
                           [skin for skin in skins.keys()] + path[1:]
                else:
                    path = [skin[0] for skin in skins.keys()] + path
                npath = ', '.join(path)
                self.portal.portal_skins.addSkinSelection(skin_name, npath)
            self.portal_v_reset_skins = 1

    #############################################################
    # TESTS START HERE
    #############################################################

    def test_skins_ok(self):
        self.assert_(
            'cps_workflow_default' in self.portal.portal_skins.objectIds())
        all_skins = self.portal.portal_skins.getSkinPaths()

        flag = 0
        for skin_name, skin_path in all_skins:
            if string.find('cps_workflow_default', skin_path):
                flag = 1
                break

        self.assert_(flag)

        # test if we can find the default render methods
        #self.assert_(getattr(self.portal, 'stack_simple_method', 0))
        #self.assert_(getattr(self.portal, 'stack_hierarchical_method', 0))

    def test_bstack_rendering(self):
        bstack = Stack()
        bstack.render_method = 'xxx'

        # Pickle
        self.portal._setObject('bstack', bstack)
        stackob = getattr(self.portal, 'bstack')

        # Test on the bar stack def.
        self.assertRaises(RuntimeError, stackob.render, context=self.portal,
                          mode='view')
        self.assertRaises(RuntimeError, stackob.render, context=self.portal,
                          mode='edit')


    def test_sstack_rendering(self):
        sstack = SimpleStack()

        # Pickle
        self.portal._setObject('sstack', sstack)
        stackob = getattr(self.portal, 'sstack')

        stackob.render(context=self.portal, mode='view')

    def test_hstack_rendering(self):
        hstack = HierarchicalStack()

        # Pickle
        self.portal._setObject('hstack', hstack)
        stackob = getattr(self.portal, 'hstack')

        stackob.render(context=self.portal, mode='view')


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(StackRenderingTestCase)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
