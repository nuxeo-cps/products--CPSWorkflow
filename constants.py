# Copyright (c) 2005 Nuxeo SAS <http://nuxeo.com>
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
"""Workflow constants.
"""

#
# Transition behaviors
#

TRANSITION_ALLOWSUB_CREATE = 10
TRANSITION_ALLOWSUB_DELETE = 11
TRANSITION_ALLOWSUB_MOVE = 12 # Into this container.
TRANSITION_ALLOWSUB_COPY = 13 # Same...
TRANSITION_ALLOWSUB_PUBLISHING = 14
TRANSITION_ALLOWSUB_CHECKOUT = 15

TRANSITION_INITIAL_CREATE = 20
TRANSITION_INITIAL_MOVE = 22
TRANSITION_INITIAL_COPY = 23
TRANSITION_INITIAL_PUBLISHING = 24
TRANSITION_INITIAL_CHECKOUT = 25
TRANSITION_ALLOW_CHECKIN = 26

TRANSITION_BEHAVIOR_DELETE = 31
TRANSITION_BEHAVIOR_MOVE = 32
TRANSITION_BEHAVIOR_COPY = 33
TRANSITION_BEHAVIOR_PUBLISHING = 34
TRANSITION_BEHAVIOR_CHECKOUT = 35
TRANSITION_BEHAVIOR_CHECKIN = 36
TRANSITION_BEHAVIOR_FREEZE = 37
TRANSITION_BEHAVIOR_MERGE = 38

TRANSITION_BEHAVIOR_PUSH_DELEGATEES = 41
TRANSITION_BEHAVIOR_POP_DELEGATEES = 42
TRANSITION_BEHAVIOR_WORKFLOW_UP = 44
TRANSITION_BEHAVIOR_WORKFLOW_DOWN = 45
TRANSITION_BEHAVIOR_WORKFLOW_RESET = 48

TRANSITION_FLAGS_EXPORT = {
    TRANSITION_ALLOWSUB_CREATE:     'allow-sub-create',
    TRANSITION_ALLOWSUB_DELETE:     'allow-sub-delete',
    TRANSITION_ALLOWSUB_MOVE:       'allow-sub-delete',
    TRANSITION_ALLOWSUB_COPY:       'allow-sub-copy',
    TRANSITION_ALLOWSUB_PUBLISHING: 'allow-sub-publishing',
    TRANSITION_ALLOWSUB_CHECKOUT:   'allow-sub-checkout',

    TRANSITION_INITIAL_CREATE:      'initial-create',
    TRANSITION_INITIAL_MOVE:        'initial-move',
    TRANSITION_INITIAL_COPY:        'initial-copy',
    TRANSITION_INITIAL_PUBLISHING:  'initial-clone',
    TRANSITION_INITIAL_CHECKOUT:    'initial-checkout',
    TRANSITION_ALLOW_CHECKIN:       'allow-checkin',

    TRANSITION_BEHAVIOR_DELETE:     'delete',
    TRANSITION_BEHAVIOR_MOVE:       'move',
    TRANSITION_BEHAVIOR_COPY:       'copy',
    TRANSITION_BEHAVIOR_PUBLISHING: 'clone',
    TRANSITION_BEHAVIOR_CHECKOUT:   'checkout',
    TRANSITION_BEHAVIOR_CHECKIN:    'checkin',
    TRANSITION_BEHAVIOR_FREEZE:     'freeze',
    TRANSITION_BEHAVIOR_MERGE:      'merge',

    TRANSITION_BEHAVIOR_PUSH_DELEGATEES: 'push-delegatees',
    TRANSITION_BEHAVIOR_POP_DELEGATEES:  'pop-delegatees',
    TRANSITION_BEHAVIOR_WORKFLOW_UP :    'workflow-up',
    TRANSITION_BEHAVIOR_WORKFLOW_DOWN :  'workflow-down',
    TRANSITION_BEHAVIOR_WORKFLOW_RESET : 'workflow-reset',
    }

TRANSITION_FLAGS_IMPORT = dict(
    [(v, k) for k, v in TRANSITION_FLAGS_EXPORT.items()])
del k, v

#
# State behaviors
#
# Used for workflow stacks right now.  They allow a behavior on the state.
# You might have shared transitions doing the same job on several states.
#

STATE_BEHAVIOR_PUSH_DELEGATEES = 101
STATE_BEHAVIOR_POP_DELEGATEES = 102
STATE_BEHAVIOR_WORKFLOW_UP = 103
STATE_BEHAVIOR_WORKFLOW_DOWN = 104
STATE_BEHAVIOR_WORKFLOW_RESET = 108

STATE_FLAGS_EXPORT = {
    STATE_BEHAVIOR_PUSH_DELEGATEES: 'push-delegatees',
    STATE_BEHAVIOR_POP_DELEGATEES:  'pop-delegatees',
    STATE_BEHAVIOR_WORKFLOW_UP:     'workflow-up',
    STATE_BEHAVIOR_WORKFLOW_DOWN:   'workflow-down',
    STATE_BEHAVIOR_WORKFLOW_RESET:  'workflow-reset',
    }

STATE_FLAGS_IMPORT = dict(
    [(v, k) for k, v in STATE_FLAGS_EXPORT.items()])
del k, v
