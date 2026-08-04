import argparse
import unittest
import pytest
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from xbot_msgs.msg import JointState


TOPIC = '/xbotcore/joint_states'
TIMEOUT_SEC = 5.0


def pytest_addoption(parser):
    parser.addoption('--wheels', required=True, type=str,
                     help='Whether the robot has wheels (true/false)')
    parser.addoption('--arms', required=True, type=str,
                     help='Whether the robot has arms (true/false)')


def _parse_bool(value: str) -> bool:
    return value.lower() in ('true', '1', 'yes', 'y')

# Match the most permissive QoS to be compatible with any publisher
QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)

class ExpectedJointState:
    def __init__(self, arms: bool, wheels: bool):
        self.joint_names = []
        self.joint_names += [f'hip_roll_{i}' for i in range(1, 5)]
        self.joint_names += [f'hip_pitch_{i}' for i in range(1, 5)]
        self.joint_names += [f'knee_pitch_{i}' for i in range(1, 5)]
        if arms:
            self.joint_names += [f'shoulder_yaw_{i}' for i in range(1, 3)]
            self.joint_names += [f'shoulder_pitch_{i}' for i in range(1, 3)]
            self.joint_names += [f'elbow_pitch_{i}' for i in range(1, 3)]
            self.joint_names += [f'wrist_pitch_{i}' for i in range(1, 3)]
            self.joint_names += [f'wrist_yaw_{i}' for i in range(1, 3)]
            self.joint_names += [f'dagana_{i}_clamp_joint' for i in range(1, 3)]
        if wheels:
            self.joint_names += [f'ankle_yaw_{i}' for i in range(1, 5)]
            self.joint_names += [f'wheel_joint_{i}' for i in range(1, 5)]

    def __len__(self):
        return len(self.joint_names)
    
    def check(self, joint_state_msg: JointState):
        missing_joints = [name for name in self.joint_names if name not in joint_state_msg.name]
        too_many_joints = [name for name in joint_state_msg.name if name not in self.joint_names]
        if missing_joints:
            raise AssertionError(f'Missing joints in received JointState: {missing_joints}')
        if too_many_joints:
            raise AssertionError(f'Unexpected joints in received JointState: {too_many_joints}')
        

class JointStateListener(Node):
    def __init__(self):
        super().__init__('test_joint_state_listener')
        self.latest_msg = None
        self.sub = self.create_subscription(
            JointState,
            TOPIC,
            self._cb,
            QOS,
        )

    def _cb(self, msg):
        self.latest_msg = msg


class TestJointStateTopic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = JointStateListener()

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_receives_joint_state(self, request=None):
        """Fail if no message is received on /xbotcore/joint_states within TIMEOUT_SEC."""
        import time
        deadline = time.time() + TIMEOUT_SEC
        while time.time() < deadline and self.node.latest_msg is None:
            rclpy.spin_once(self.node, timeout_sec=0.1)

        self.assertIsNotNone(
            self.node.latest_msg,
            f'No message received on {TOPIC} within {TIMEOUT_SEC} seconds.',
        )

        msg = self.node.latest_msg
        self.get_logger_info(f'Received joint state with {len(msg.name)} joints: {msg.name}')

        if request is not None:
            # running via pytest
            arms = _parse_bool(request.config.getoption('--arms'))
            wheels = _parse_bool(request.config.getoption('--wheels'))
        else:
            # running via python3 directly
            arms = args.arms
            wheels = args.wheels
        expected = ExpectedJointState(arms=arms, wheels=wheels)
        expected.check(msg)

    def get_logger_info(self, text):
        self.node.get_logger().info(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wheels', required=True, type=lambda x: x.lower() in ('true', '1', 'yes', 'y'),
                        help='Whether the robot has wheels (true/false)')
    parser.add_argument('--arms', required=True, type=lambda x: x.lower() in ('true', '1', 'yes', 'y'),
                        help='Whether the robot has arms (true/false)')
    args, remaining = parser.parse_known_args()

    # Pass remaining args to unittest so it doesn't choke on --wheels
    unittest.main(argv=[''] + remaining)
