#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
source ~/test_ws/setup.bash

# Launch the simulator; if it is still running after 5 seconds, consider it a success.
xvfb-run ros2 launch kyon_mujoco kyon_world.launch.py &
LAUNCH_PID=$!

sleep 5

if kill -0 $LAUNCH_PID 2>/dev/null; then
    # Still running after 5 s — success
    kill $LAUNCH_PID
    wait $LAUNCH_PID 2>/dev/null || true
    echo "Simulator ran successfully for 5 seconds."
    exit 0
else
    # Died before 5 s — failure
    wait $LAUNCH_PID
    echo "Simulator exited prematurely with code $?."
    exit 1
fi
