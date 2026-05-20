#!/bin/bash
set -e

source /opt/xbot/setup.sh
source /opt/ros/jazzy/setup.bash
source ~/test_ws/setup.bash

# Launch the simulator; if it is still running after 5 seconds, consider it a success.
xvfb-run ros2 launch kyon_mujoco kyon_world.launch &
LAUNCH_PID=$!
sleep 2
xbot2-core -C ~/test_ws/src/iit-kyon-ros-pkg/kyon_config/kyon_basic.yaml &
sleep 5
python3 -m pytest ~/test_ws/src/iit-kyon-ros-pkg/tests/test_comm_joints.py

# sleep 5

# if kill -0 $LAUNCH_PID 2>/dev/null; then
#     # Still running after 5 s — success
#     kill $LAUNCH_PID
#     wait $LAUNCH_PID 2>/dev/null || true
#     echo "Simulator ran successfully for 5 seconds."
#     exit 0
# else
#     # Exited before 5 s: success only if clean exit code (0)
#     if wait $LAUNCH_PID; then
#         echo "Simulator exited cleanly before 5 seconds."
#         exit 0
#     else
#         EXIT_CODE=$?
#         echo "Simulator exited prematurely with code $EXIT_CODE."
#         exit 1
#     fi
# fi
