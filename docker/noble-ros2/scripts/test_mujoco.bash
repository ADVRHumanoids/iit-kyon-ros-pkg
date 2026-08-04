#!/bin/bash
set -e

source /opt/xbot/setup.sh
source /opt/ros/jazzy/setup.bash
source ~/test_ws/setup.bash

# Test with legs
xvfb-run -a ros2 launch kyon_mujoco kyon_world.launch arms:=true wheels:=false&
LAUNCH_MUJOCO=$!
sleep 5
xbot2-core -C ~/test_ws/src/iit-kyon-ros-pkg/kyon_config/kyon_basic.yaml &
LAUNCH_XBOT=$!
sleep 5
python3 ~/test_ws/src/iit-kyon-ros-pkg/tests/test_comm_joints.py --arms true --wheels false
LAUNCH_TEST=$!

kill $LAUNCH_MUJOCO
kill $LAUNCH_XBOT
kill $LAUNCH_TEST
wait $LAUNCH_MUJOCO 2>/dev/null || true
wait $LAUNCH_XBOT 2>/dev/null || true
wait $LAUNCH_TEST 2>/dev/null || true
# kill robot_description_publisher if it's still running (it can be left hanging after killing the main process)
pkill -f robot_description_publisher 2>/dev/null || true

# Test with wheels
xvfb-run -a ros2 launch kyon_mujoco kyon_world.launch arms:=true wheels:=true&
LAUNCH_MUJOCO=$!
sleep 5
xbot2-core -C ~/test_ws/src/iit-kyon-ros-pkg/kyon_config/kyon_basic.yaml &
LAUNCH_XBOT=$!
sleep 5
python3 ~/test_ws/src/iit-kyon-ros-pkg/tests/test_comm_joints.py --arms true --wheels true
LAUNCH_TEST=$!

kill $LAUNCH_MUJOCO
kill $LAUNCH_XBOT
kill $LAUNCH_TEST
wait $LAUNCH_MUJOCO 2>/dev/null || true
wait $LAUNCH_XBOT 2>/dev/null || true
wait $LAUNCH_TEST 2>/dev/null || true
# kill robot_description_publisher if it's still running (it can be left hanging after killing the main process)
pkill -f robot_description_publisher 2>/dev/null || true