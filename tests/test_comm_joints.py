import unittest
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from xbot_msgs.msg import JointState


TOPIC = '/xbotcore/joint_states'
TIMEOUT_SEC = 5.0

# Match the most permissive QoS to be compatible with any publisher
QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)


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

    def test_receives_joint_state(self):
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

    def get_logger_info(self, text):
        self.node.get_logger().info(text)


if __name__ == '__main__':
    unittest.main()
