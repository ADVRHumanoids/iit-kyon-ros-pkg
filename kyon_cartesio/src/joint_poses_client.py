#!/usr/bin/env python3
import argparse

import rospy
from control_msgs.msg import FollowJointTrajectoryAction, FollowJointTrajectoryGoal
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

import rospy 
import actionlib

poses = dict()

poses['home_left'] = {
    'shoulder_yaw_1': 0.0,
    'shoulder_pitch_1': 1.5,
    'elbow_pitch_1': 2.6,
    'wrist_pitch_1': 0.7,
    'wrist_yaw_1': 0.0,
}

poses['home_right'] = {k.replace('1', '2'): -v for k, v in poses['home_left'].items()}

poses['home_lr'] = {**poses['home_left'], **poses['home_right']}

poses['reach_to_grasp_left'] = {
    'shoulder_yaw_1': 0.0,
    'shoulder_pitch_1': -0.5,
    'elbow_pitch_1': 1.0,
    'wrist_pitch_1': 0.1,
    'wrist_yaw_1': 1.57,
}

poses['reach_to_grasp_right'] = {k.replace('1', '2'): -v for k, v in poses['reach_to_grasp_left'].items()}

# use argparse to get the pose name from the command line
parser = argparse.ArgumentParser(description='Send joint poses to the robot.')
parser.add_argument('pose_name', type=str, choices=list(poses.keys()), help='Name of the pose to send to the robot.')
args = parser.parse_args()
pose_name = args.pose_name
pose = poses[pose_name]

# connect to the action server
rospy.init_node('joint_poses_client_node') # Give your node a name
rospy.loginfo("Sending pose: {}".format(pose_name))

client = actionlib.SimpleActionClient('/xbotcore/joint_trajectory_action', FollowJointTrajectoryAction) # Replace with your action name
rospy.loginfo("Waiting for action server to start...")
client.wait_for_server()
rospy.loginfo("Action server started, sending goal.")

# send goal
goal = FollowJointTrajectoryGoal()
goal.trajectory = JointTrajectory()
goal.trajectory.joint_names = pose.keys()
trjpt = JointTrajectoryPoint()
trjpt.positions = list(pose.values())
trjpt.velocities = [0.0] * len(pose)
trjpt.accelerations = [0.0] * len(pose)
trjpt.time_from_start = rospy.Duration(1.0) # Time to reach the goal
goal.trajectory.points.append(trjpt)

def feedback_cb(feedback):
    pass

def active_cb():
    rospy.loginfo("Goal active!")

def done_cb(status, result):
    rospy.loginfo("Action finished with status: {}".format(status))
    rospy.loginfo("Result: {}".format(result))
    if status == actionlib.GoalStatus.SUCCEEDED:
        rospy.loginfo("Action succeeded!")
    elif status == actionlib.GoalStatus.PREEMPTED:
        rospy.loginfo("Goal was preempted!")
    elif status == actionlib.GoalStatus.ABORTED:
        rospy.loginfo("Goal was aborted!")
    rospy.signal_shutdown("Action finished") # Shutdown the node after the action is done

client.send_goal(goal, done_cb=done_cb, active_cb=active_cb, feedback_cb=feedback_cb) # Send the goal

rospy.spin() # Keep the node alive to receive callbacks