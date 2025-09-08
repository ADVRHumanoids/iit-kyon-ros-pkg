#!/usr/bin/env python3

import time
import numpy as np
np.set_printoptions(precision=2, suppress=True)
import argparse
import os

import rospy

os.environ['XBOT_VERBOSE'] = '2'
from xbot_interface import xbot_interface as xb
from cartesian_interface.pyci_all import *


# init cartesio API
ci = pyci.CartesianInterfaceRos()

# retrieve tasks
larm = ci.getTask('dagana_1_base')
rarm = ci.getTask('dagana_2_base')

larm.setWeight(np.diag([1.0, 1.0, 1.0, 0., 0., 0.]))
rarm.setWeight(np.diag([1.0, 1.0, 1.0, 0., 0., 0.]))

# get the initial pose reference for the arms
print(larm.getDistalLink(), larm.getPoseReference())
print(rarm.getDistalLink(), rarm.getPoseReference())

# compute a z offset to account for the height of the robot w.r.t. one 
# of the contact points
z_offset = -ci.getPoseFromTf('ci/contact_1', 'ci/world').translation[2]
print('z_offset', z_offset)

# define targets for the grippers
larm_target = larm.getPoseReference()[0]
larm_target.translation = [0.80, 0.20, -0.3]
larm_target.quaternion = [0.7, .7, 0., 0.]

rarm_target = rarm.getPoseReference()[0]
rarm_target.translation = larm_target.translation
rarm_target.translation[1] *= -1
rarm_target.quaternion = [0.7, .7, 0., 0.]

# send goals
trj_time = 8.0
larm.setPoseTarget(larm_target, trj_time)
rarm.setPoseTarget(rarm_target, trj_time)

# wait for the arms to reach the targets
larm.waitReachCompleted(-1.0)
rarm.waitReachCompleted(-1.0)

# go up
larm_target.translation = [0.80, 0.20, 0.8]
rarm_target.translation = larm_target.translation
rarm_target.translation[1] *= -1

larm.setPoseTarget(larm_target, trj_time)
rarm.setPoseTarget(rarm_target, trj_time)
larm.waitReachCompleted(-1.0)
rarm.waitReachCompleted(-1.0)

#
print('done')