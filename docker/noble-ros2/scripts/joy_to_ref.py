#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.wait_for_message import wait_for_message
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist, Pose, PoseStamped


class JoyToRef(Node):

    def __init__(self):
        super().__init__('joy_to_ref')
        self.declare_parameter('linear_scale', 1.0)
        self.declare_parameter('angular_scale', 1.0)
        self._linear_scale = self.get_parameter('linear_scale').value
        self._angular_scale = self.get_parameter('angular_scale').value

        self._pub_base_vel = self.create_publisher(Twist, '/policy_deploy_node/commands/base_velocity', 10)
        self._dagana_1_pub = self.create_publisher(PoseStamped, '/cartesian/dagana_1_base/reference', 10)
        self._dagana_2_pub = self.create_publisher(PoseStamped, '/cartesian/dagana_2_base/reference', 10)
        self._sub = self.create_subscription(Joy, 'joy', self._joy_callback, 10)

        self.linear_ee_vel = 0.2
        self._dt = 0.01
        self._last_joy = None

        self._dagana_1_curr_ref = self._wait_for_current_reference(
            '/cartesian/dagana_1_base/current_reference')
        self._dagana_2_curr_ref = self._wait_for_current_reference(
            '/cartesian/dagana_2_base/current_reference')

        self._timer = self.create_timer(self._dt, self._timer_callback)

    def _wait_for_current_reference(self, topic: str):
        success, msg = wait_for_message(PoseStamped, self, topic, time_to_wait=5.0)
        if not success:
            print(f'WARNING: no message received on "{topic}" after 5 seconds')
            return None
        return msg.pose

    def _joy_callback(self, msg: Joy):
        self._last_joy = msg

    def _timer_callback(self):
        msg = self._last_joy
        if msg is None:
            return

        if msg.buttons[5]:
            if self._dagana_2_curr_ref is not None:
                pose = PoseStamped()
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose = self._dagana_2_curr_ref
                pose.pose.position.x += msg.axes[1] * self.linear_ee_vel * self._dt
                pose.pose.position.y += msg.axes[0] * self.linear_ee_vel * self._dt
                pose.pose.position.z += msg.axes[4] * self.linear_ee_vel * self._dt
                self._dagana_2_pub.publish(pose)
        if msg.buttons[4]:
            if self._dagana_1_curr_ref is not None:
                pose = PoseStamped()
                pose.header.stamp = self.get_clock().now().to_msg()
                pose.pose = self._dagana_1_curr_ref
                pose.pose.position.x += msg.axes[1] * self.linear_ee_vel * self._dt
                pose.pose.position.y += msg.axes[0] * self.linear_ee_vel * self._dt
                pose.pose.position.z += msg.axes[4] * self.linear_ee_vel * self._dt
                self._dagana_1_pub.publish(pose)
        if not msg.buttons[5] and not msg.buttons[4]:
            twist = Twist()
            twist.linear.x = self._linear_scale * msg.axes[1]
            twist.linear.y = self._linear_scale * msg.axes[0]
            twist.angular.z = self._angular_scale * msg.axes[3]
            self._pub_base_vel.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = JoyToRef()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
