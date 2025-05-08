#!/usr/bin/env python3

import time
import numpy as np
np.set_printoptions(precision=2, suppress=True)
import argparse
import os
import tf
import tf.transformations as tft
import rospy

os.environ['XBOT_VERBOSE'] = '2'
from xbot_interface import xbot_interface as xb
from cartesian_interface.pyci_all import *

from geometry_msgs.msg import WrenchStamped

from fiducial_msgs.msg import FiducialTransformArray, FiducialTransform
from geometry_msgs.msg import Transform, PoseStamped

def transform_to_matrix(transform):
    # Extract translation and rotation
    translation = [transform.translation.x, transform.translation.y, transform.translation.z]
    rotation = [transform.rotation.x, transform.rotation.y,
                transform.rotation.z, transform.rotation.w]

    # Convert to 4x4 matrix
    matrix = tft.concatenate_matrices(
        tft.translation_matrix(translation),
        tft.quaternion_matrix(rotation)
    )
    return matrix



rospy.init_node('grasp_aruco_node')
listener = tf.TransformListener()
fiducials: FiducialTransformArray = rospy.wait_for_message('/aruco_base/fiducial_transforms', FiducialTransformArray, timeout=5.0)
aruco_id = 0
goal_found = False
for ft in fiducials.transforms:
    if ft.fiducial_id != aruco_id:
        continue
    goal_found = True
    goal = transform_to_matrix(ft.transform)
    print(goal)

if not goal_found:
    exit(1)

# transform into pelvis frame
listener.waitForTransform('pelvis', fiducials.header.frame_id, time=rospy.Time(0), timeout=rospy.Duration(5.0))
trans, rot = listener.lookupTransform('pelvis', fiducials.header.frame_id, time=rospy.Time(0))
pelvis_T_of = tft.concatenate_matrices(
        tft.translation_matrix(trans),
        tft.quaternion_matrix(rot)
    )

print(pelvis_T_of)

# and into ci/world
listener.waitForTransform('ci/world', 'ci/pelvis', time=rospy.Time(0), timeout=rospy.Duration(5.0))
trans, rot = listener.lookupTransform('ci/world', 'ci/pelvis', time=rospy.Time(0))
w_T_pelvis = tft.concatenate_matrices(
        tft.translation_matrix(trans),
        tft.quaternion_matrix(rot)
    )
# w_T_pelvis = np.eye(4)

w_T_aruco = w_T_pelvis @ pelvis_T_of @ goal
print(w_T_aruco)

aruco_T_dagana = np.eye(4)
aruco_T_dagana[:3, 0] = [-1, 0, 0]
aruco_T_dagana[:3, 1] = [0, 1, 0]
aruco_T_dagana[:3, 2] = [0, 0, -1.]
aruco_T_dagana[:3, 3] = [0., -0.03, 0.35]

w_T_dagana_mat = w_T_aruco @ aruco_T_dagana
print(w_T_dagana_mat)

w_T_dagana = Affine3()
w_T_dagana.translation = w_T_dagana_mat[:3, 3]
w_T_dagana.linear = w_T_dagana_mat[:3, :3]
print(w_T_dagana)

# init cartesio
ci = pyci.CartesianInterfaceRos()

larm = ci.getTask('dagana_1_base')
larm.disable()

rarm = ci.getTask('dagana_2_base')

trj_time = 10.0
rarm.setPoseTarget(w_T_dagana, trj_time)
rarm.waitReachCompleted(-1)

input('OPEN hand, then press ENTER')

w_T_dagana.translation[2] -= 0.20
trj_time = 3.0
rarm.setPoseTarget(w_T_dagana, trj_time)
rarm.waitReachCompleted(-1)

input('CLOSE hand, then press ENTER')

w_T_dagana.translation[2] += 0.40
trj_time = 3.0
rarm.setPoseTarget(w_T_dagana, trj_time)
rarm.waitReachCompleted(-1)
