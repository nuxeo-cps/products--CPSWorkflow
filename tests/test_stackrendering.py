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

from layer import CMFDefaultLayer

from Products.CMFCore.utils import getToolByName

from Products.CPSWorkflow.stack import Stack
from Products.CPSWorkflow.basicstacks import SimpleStack
from Products.CPSWorkflow.basicstacks import HierarchicalStack

# GR TODO make a profile and layer ?
from Products.CMFCore.DirectoryView import createDirectoryView
SKINS = { 'cps_workflow_default':
              'Products.CPSWorkflow:skins/cps_workflow_default',
         }

class StackRenderingTestCase(ZopeTestCase.PortalTestCase):

    layer = CMFDefaultLayer

    portal_name = 'site'

    def __init__(self, id):
        ZopeTestCase.PortalTestCase.__init__(self, id)
        self.messages = []

    def getPortal(self):
        return self.app.site

    def afterSetUp(self):
        self.portal = self.getPortal()
        self.setUpSkins()

    def setUpSkins(self):
        portal = self.portal
        sktool = getToolByName(portal, 'portal_skins')
        to_add = []
        for skin, path in SKINS.items():
            createDirectoryView(sktool, path, skin)
            to_add.append(skin)

        all_skins = sktool.getSkinPaths()
        for skin, path in all_skins:
            path = ','.join(to_add) + ',' + path
            sktool.addSkinSelection(skin, path)

        portal.clearCurrentSkin()
        portal.setupCurrentSkin(self.app.REQUEST)

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
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StackRenderingTestCase))
    return suite
