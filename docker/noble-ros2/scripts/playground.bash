#!/usr/bin/env bash
# Start the Kyon playground stack.  Stop it with Ctrl-C; all processes started
# by this script will be terminated together.

source /opt/xbot/setup.sh
source /opt/ros/jazzy/setup.bash
source ~/test_ws/setup.bash

# ROS setup scripts intentionally inspect optional variables that may not yet
# exist, so enable nounset only after sourcing them.
set -Eeuo pipefail

process_groups=()

start() {
    setsid "$@" &
    process_groups+=("$!")
}

shutdown() {
    local pid
    trap - EXIT INT TERM
    for pid in "${process_groups[@]}"; do
        kill -- "-$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap shutdown EXIT INT TERM

start ros2 launch kyon_mujoco kyon_world.launch
sleep 5

start xbot2-core -S -C /home/user/test_ws/src/iit-kyon-ros-pkg/kyon_config/kyon_basic.yaml
sleep 5

start ros2 service call /xbotcore/homing/switch std_srvs/srv/SetBool "{data: true}"
sleep 5

start ros2 launch policy_deploy_toolkit run_example.launch.xml
sleep 5

start ros2 launch kyon_cartesio kyon_arms.launch
sleep 5

start /home/user/test_ws/src/iit-kyon-ros-pkg/docker/noble-ros2/scripts/joy_to_ref.py
start ros2 run joy joy_node
sleep 2

printf '\033[0;32m################################################################\033[0m\n'
printf '\033[0;32m#                                                              #\033[0m\n'
printf '\033[0;32m#  Kyon playground stack is running. Press Ctrl-C to stop it.  #\033[0m\n'
printf '\033[0;32m#                                                              #\033[0m\n'
printf '\033[0;32m################################################################\033[0m\n'

# Keep the script alive while the playground stack is running.
wait
