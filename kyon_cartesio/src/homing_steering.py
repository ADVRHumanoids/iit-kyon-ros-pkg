#!/usr/bin/env python3
"""Smoothly apply joint posture overrides with the wheel CartesIO stack."""

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from rclpy.wait_for_message import wait_for_message
from rclpy.utilities import remove_ros_args
from std_msgs.msg import String

from cartesian_interface import pyci
from xbot2_interface import pyxbot2_interface as xb

np.set_printoptions(precision=2, suppress=True)


def joint_override(value):
    joint, separator, position = value.partition('=')
    try:
        position = float(position)
    except ValueError:
        raise argparse.ArgumentTypeError('Expected JOINT=VALUE with a finite value') from None
    if not separator or not joint.strip() or not math.isfinite(position):
        raise argparse.ArgumentTypeError('Expected JOINT=VALUE with a finite value')
    return joint.strip(), position


def positive_duration(value):
    try:
        duration = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Duration must be finite and positive') from None
    if not math.isfinite(duration) or duration <= 0.0:
        raise argparse.ArgumentTypeError('Duration must be finite and positive')
    return duration


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--target-state', '-t', default='home_isaac', metavar='NAME',
        help='SRDF state used as the target baseline, or "current" for current qref '
             '(default: home_isaac). Motion always starts from current qref.',
    )
    parser.add_argument(
        '--override', '-o', action='append', type=joint_override, default=[],
        metavar='JOINT=VALUE',
        help='Override a target joint position in radians; repeat for multiple joints '
             '(last value wins).',
    )
    parser.add_argument(
        '--duration', '-t', type=positive_duration, default=5.0,
        help='Interpolation duration in seconds (default: 5).',
    )
    argv = sys.argv[1:] if args is None else args
    return parser.parse_args(remove_ros_args(args=['homing_steering', *argv])[1:])


class HomingSteeringIk:
    def __init__(self, node: Node):
        self.node = node
        self.dt = 0.01
        self.time = 0.0

        # receive urdf, srdf
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

        # build robot and model interfaces
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

        # get ik stack
        stack_path = (
            Path(get_package_share_directory('kyon_cartesio'))
            / 'config' / 'kyon_wheel_stack.yaml'
        )

        # construct ci
        self.ci = pyci.CartesianInterface.MakeInstance(
            solver='OpenSot', problem=stack_path.read_text(),
            model=self.model, dt=self.dt,
        )

        # # Disable Cartesian wheel position tracking; keep steering and rolling.
        # wheels = ['wheel_1', 'wheel_2', 'wheel_3', 'wheel_4']
        # for wheel in wheels:
        #     self.ci.getTask(wheel).setWeight(np.diag([0, 0, 0, 0, 0, 0]))

        self.ros_server = pyci.RosServerClass(self.ci)

        # get postural task
        self.postural = self.ci.getTask('Postural')
        self.postural.setWeight(np.diag([1.0] * self.model.nv))

        # Set control modes: position for the posture and velocity for the wheels.
        self.wheel_joints = [f'wheel_joint_{i}' for i in range(1, 5)]
        self.robot.setControlMode(xb.ControlMode.Position().type())
        self.robot.setControlMode({
            joint: xb.ControlMode.Velocity().type() for joint in self.wheel_joints
        })

    def solve_and_move(self):
        if not self.ci.update(self.time, self.dt):
            raise RuntimeError(f'CartesIO solver failed at t={self.time:.2f}s')
        self.model.q = self.model.sum(self.model.q, self.model.v * self.dt)
        self.model.update()
        self.ros_server.run()
        self.robot.setPositionReference(self.model.q)
        velocity = self.model.vToMap(self.model.v)
        self.robot.setVelocityReference({
            joint: velocity[joint] for joint in self.wheel_joints
        })
        self.robot.move()
        self.time += self.dt

    def reach(self, q_target, duration):
        """Interpolate the postural reference with zero endpoint speed/acceleration."""
        if not np.isfinite(duration) or duration <= 0.0:
            raise ValueError('Motion duration must be finite and positive')
        q_start = self.model.q.copy()
        delta_q = self.model.difference(q_target, q_start)
        start_time = self.time

        # Use model time for interpolation and monotonic time to pace the solver.
        deadline = time.monotonic()
        while rclpy.ok():
            tau = min((self.time - start_time) / duration, 1.0)
            alpha = tau**3 * (10.0 - 15.0 * tau + 6.0 * tau**2)
            alpha_dot = 30.0 * tau**2 * (1.0 - tau)**2 / duration
            q = self.model.sum(q_start, alpha * delta_q)
            self.postural.setReferencePosture(self.model.qToMap(q))

            # Steering reads wheel twists from model.v during ci.update().
            # Use the intended posture velocity, before rolling restricts it;
            # reusing the previous QP velocity creates a delayed feedback loop.
            self.model.v = alpha_dot * delta_q
            self.model.update()
            self.solve_and_move()
            if tau >= 1.0:
                return
            rclpy.spin_once(self.node, timeout_sec=0.0)
            deadline += self.dt
            time.sleep(max(0.0, deadline - time.monotonic()))
        raise RuntimeError('ROS shut down before the motion completed')


    def run(self, target_state='home_isaac', overrides=None, duration=5.0):

        # update robot
        deadline = time.monotonic() + 5.0
        while not self.robot.sense():
            if not rclpy.ok() or time.monotonic() >= deadline:
                raise RuntimeError('Failed to receive the robot state')
            time.sleep(self.dt)

        q_reference = self.robot.getPositionReferenceFeedback()
        self.model.q = q_reference
        self.model.update()
        self.ci.reset(self.time)

        if target_state != 'current':
            q_reference = self.robot.getRobotState(target_state)

        q_reference_map = self.robot.qToMap(q_reference)

        q_target_overrides = {} if overrides is None else dict(overrides)

        unknown_joints = q_target_overrides.keys() - q_reference_map.keys()
        if unknown_joints:
            raise ValueError(f'Unknown override joints: {sorted(unknown_joints)}')
        q_reference_map.update(q_target_overrides)
        q_target = self.model.mapToQ(q_reference_map)
        try:
            self.reach(q_target, duration=duration)
        finally:
            self.robot.setVelocityReference({joint: 0.0 for joint in self.wheel_joints})
            self.robot.move()
        self.node.get_logger().info('Postural interpolation completed')


def main(args=None):
    options = parse_args(args)
    rclpy.init(args=args)
    node = Node('homing_steering')
    try:
        HomingSteeringIk(node).run(
            target_state=options.target_state,
            overrides=options.override,
            duration=options.duration,
        )
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
