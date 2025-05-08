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

from geometry_msgs.msg import WrenchStamped


# # subscribe to force topics
# f_left = None
# f_right = None
# f_left_offset = None
# f_right_offset = None

# def force_callback_left(msg):
#     global f_left
#     global f_left_offset
#     if f_left_offset is None:
#         f_left_offset = np.array([msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z])
#         print("f_left_offset", f_left_offset)
#     f_left = np.array([msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z]) - f_left_offset
    
# def force_callback_right(msg):
#     global f_right
#     global f_right_offset
#     if f_right_offset is None:
#         f_right_offset = np.array([msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z])
#         print("f_right_offset", f_right_offset)
#     f_right = np.array([msg.wrench.force.x, msg.wrench.force.y, msg.wrench.force.z]) - f_right_offset
    
# lsub = rospy.Subscriber('/cartesian/force_estimation/dagana_1_base', WrenchStamped, force_callback_left)
# rsub = rospy.Subscriber('/cartesian/force_estimation/dagana_2_base', WrenchStamped, force_callback_right)
# rospy.init_node('bimanual', anonymous=True)


# init cartesio
ci = pyci.CartesianInterfaceRos()

larm = ci.getTask('dagana_1_base')
rarm = ci.getTask('dagana_2_base')

print(larm.getDistalLink(), larm.getPoseReference())
print(rarm.getDistalLink(), rarm.getPoseReference())

z_offset = -ci.getPoseFromTf('ci/contact_1', 'ci/world').translation[2]
print('z_offset', z_offset)

larm_target = larm.getPoseReference()[0]
larm_target.translation = [0.80, 0.20, 1.0 - z_offset]
larm_target.quaternion = [0.5, .5, 0.5, 0.5]

rarm_target = rarm.getPoseReference()[0]
rarm_target.translation = larm_target.translation
rarm_target.translation[1] *= -1
rarm_target.quaternion = [0.5, .5, 0.5, 0.5]

trj_time = 8.0
larm.setPoseTarget(larm_target, trj_time)
rarm.setPoseTarget(rarm_target, trj_time)

input('Press Enter to GLASPALE')

# f_left_offset = None
# f_right_offset = None
# rospy.loginfo("Waiting for force messages...")
# while f_left_offset is None or f_right_offset is None:
#     rospy.sleep(0.1)
# rospy.loginfo(f"Received force messages {f_left} {f_right}")

grasp_vel = 0.01
dt = 0.01
force_counter = 0

while True:
    try:
        larm_target.translation[1] -= grasp_vel * dt
        rarm_target.translation[1] += grasp_vel * dt
        larm.setPoseReference(larm_target)
        rarm.setPoseReference(rarm_target)
        # f_th = 10.0
        # print(f'{force_counter}  f_left = {f_left}  f_right = {f_right}')
        # if np.abs(f_left[0]) > f_th and np.abs(f_right[0]) > f_th:
        #     force_counter += 1
        #     if force_counter > 10:
        #         print("Force detected, stopping")
        #         break
        # else:
        #     force_counter = max(force_counter - 1, 0)
        
        time.sleep(dt)
    except KeyboardInterrupt:
        break