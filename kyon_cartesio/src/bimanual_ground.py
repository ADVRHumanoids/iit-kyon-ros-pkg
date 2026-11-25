#!/usr/bin/env python3
"""Run the bimanual ground motion with an embedded CartesIO solver."""

import time
from pathlib import Path

import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from rclpy.wait_for_message import wait_for_message
from std_msgs.msg import String

from cartesian_interface import pyci
from xbot2_interface import pyxbot2_interface as xb


class BimanualGround:
    def __init__(self, node: Node):
        self.node = node
        self.dt = 0.01
        self.time = 0.0

        qos = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        descriptions = []
        for topic in ('robot_description', 'robot_description_semantic'):
            ok, msg = wait_for_message(
                String, node, f'/xbotcore/{topic}',
                qos_profile=qos, time_to_wait=5.0,
            )
            if not ok or msg is None:
                raise RuntimeError(f'Failed to receive /xbotcore/{topic}')
            descriptions.append(msg.data)

        urdf, srdf = descriptions
        self.robot = xb.RobotInterface2(urdf, srdf)
        deadline = time.monotonic() + 5.0
        while not self.robot.sense():
            if not rclpy.ok() or time.monotonic() >= deadline:
                raise RuntimeError('Failed to receive the robot state')
            time.sleep(self.dt)

        self.model = xb.ModelInterface2(urdf, srdf, 'pin')
        self.model.q = self.robot.getPositionReferenceFeedback()
        self.model.update()

        stack_path = (
            Path(get_package_share_directory('kyon_cartesio'))
            / 'config' / 'kyon_stack_stick_legs.yaml'
        )
        # The Python CartesianInterface factory constructs CartesianInterfaceImpl.
        self.ci = pyci.CartesianInterface.MakeInstance(
            solver='OpenSot', problem=stack_path.read_text(),
            model=self.model, dt=self.dt,
        )
        self.larm = self.ci.getTask('dagana_1_base')
        self.rarm = self.ci.getTask('dagana_2_base')
        for arm in (self.larm, self.rarm):
            arm.setWeight(np.diag([1.0, 1.0, 1.0, 1.0, 0.0, 1.0]))
        self.ros_server = pyci.RosServerClass(self.ci)

        # Command the legs and arms; leave the grippers and wheels uncontrolled.
        joints = [
            f'{joint}_{i+1}'
            for i in range(4)
            for joint in ('hip_roll', 'hip_pitch', 'knee_pitch')
        ] + [
            f'{joint}_{i+1}'
            for i in range(2)
            for joint in ('shoulder_yaw', 'shoulder_pitch', 'elbow_pitch',
                          'wrist_pitch', 'wrist_yaw')
        ]
        self.robot.setControlMode(xb.ControlMode.None_().type())
        self.robot.setControlMode({
            joint: xb.ControlMode.Position().type() for joint in joints
        })

    def solve_and_move(self):
        if not self.ci.update(self.time, self.dt):
            raise RuntimeError(f'CartesIO solver failed at t={self.time:.2f}s')
        self.model.q = self.model.sum(self.model.q, self.model.v * self.dt)
        self.model.update()
        self.ros_server.run()
        self.robot.setPositionReference(self.model.q)
        self.robot.move()
        self.time += self.dt

    def reach(self, left_target, right_target, duration):
        if not self.larm.setPoseTarget(left_target, duration):
            raise RuntimeError('Failed to set the left arm target')
        if not self.rarm.setPoseTarget(right_target, duration):
            raise RuntimeError('Failed to set the right arm target')

        # Local tasks advance only while update() is called; a blocking ROS
        # client wait would prevent the embedded solver from running.
        deadline = time.monotonic()
        while rclpy.ok():
            self.solve_and_move()
            if all(arm.getTaskState() == pyci.State.Online
                   for arm in (self.larm, self.rarm)):
                return
            rclpy.spin_once(self.node, timeout_sec=0.0)
            deadline += self.dt
            time.sleep(max(0.0, deadline - time.monotonic()))
        raise RuntimeError('ROS shut down before the motion completed')

    def run(self):
        left_target = self.larm.getPoseReference()[0].copy()
        right_target = self.rarm.getPoseReference()[0].copy()
        left_target.quaternion = [0.7, 0.7, 0.0, 0.0]
        right_target.quaternion = [0.7, 0.7, 0.0, 0.0]

        ground_height = self.model.getPose('contact_1').translation[2]

        TGT_1 = [0.80, 0.20, ground_height + 0.2]
        TGT_2 = [0.60, 0.20, ground_height + 1.0]

        for index, tgt in enumerate((TGT_1, TGT_2)):
            left_target.translation = tgt.copy()
            right_target.translation = [tgt[0], -tgt[1], tgt[2]]
            if index == 1:
                # Quaternion order is xyzw: tool Z -> world X, tool Y -> world Z.
                left_target.quaternion = [0.5, 0.5, 0.5, 0.5]
                right_target.quaternion = [0.5, 0.5, 0.5, 0.5]
            input(f'Press Enter to move to target {index + 1} at {tgt}...')
            self.reach(left_target, right_target, 8.0)
        self.node.get_logger().info('Bimanual motion completed')


def main(args=None):
    rclpy.init(args=args)
    node = Node('bimanual_ground')
    try:
        BimanualGround(node).run()
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
