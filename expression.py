# -*- coding: iso-8859-15 -*-
# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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

""" Expressions in a CPS web-configurable workflow.

Extends DCWorkflow Expression for CPS.
"""

from zLOG import LOG, DEBUG

from  Globals import InitializeClass

from Acquisition import aq_inner, aq_parent
from AccessControl import getSecurityManager

from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter

from Products.DCWorkflow.Expression import StateChangeInfo

class CPSStateChangeInfo(StateChangeInfo):
    """Provides information for expressions and scripts.

    Extends DCWorkflow Expression
    """

    def __init__(self, object, workflow, status=None, transition=None,
                 old_state=None, new_state=None, stacks=None, kwargs=None):

        StateChangeInfo.__init__(self, object, workflow, status, transition,
                                 old_state, new_state, kwargs)
        self.stacks = stacks

    def getLanguageRevisions(self):
        ob = self.object
        return {ob.getLanguage(): ob.getRevision()}

    def getStackFor(self, var_id=''):
        """Return the stack data structure object holding for the workflow
        variable var_id """
        stack = None
        if self.stacks is not None:
            stack = self.stacks.get(var_id, None)
            if stack is None:
                current_state = self.workflow._getWorkflowStateOf(self.object)
                LOG("Current ob state", DEBUG, str(current_state)+'x')
        return stack

InitializeClass(CPSStateChangeInfo)

def createExprContext(sci):
    '''
    An expression context provides names for TALES expressions.
    '''
    ob = sci.object
    wf = sci.workflow
    data = {
        'here':         ob,
        'container':    aq_parent(aq_inner(ob)),
        'nothing':      None,
        'root':         wf.getPhysicalRoot(),
        'request':      getattr( ob, 'REQUEST', None ),
        'modules':      SecureModuleImporter,
        'user':         getSecurityManager().getUser(),
        'state_change': sci,
        'transition':   sci.transition,
        'status':       sci.status,
        'stacks':       sci.stacks,
        'kwargs':       sci.kwargs,
        'workflow':     wf,
        'scripts':      wf.scripts,
        }
    return getEngine().getContext(data)
