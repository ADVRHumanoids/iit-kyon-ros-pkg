# ~/xbot2_ws/src/kyon_config/launcher/kyon_launcher.bash
#!/bin/bash

# Define directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Source ROS environment
if [ -f /opt/ros/noetic/setup.bash ]; then
    source /opt/ros/noetic/setup.bash
fi

# Source workspace setup if it exists (prefer devel space)
if [ -f ~/xbot2_ws/devel/setup.bash ]; then
    echo "Sourcing devel space: ~/xbot2_ws/devel/setup.bash"
    source ~/xbot2_ws/devel/setup.bash
elif [ -f ~/xbot2_ws/install/setup.bash ]; then
    echo "Sourcing install space: ~/xbot2_ws/install/setup.bash"
    source ~/xbot2_ws/install/setup.bash
else
    echo "Warning: Could not find workspace setup.bash in devel/ or install/"
fi

# Source docker setup if it exists (use the non-xeno version for simulation)
if [ -f $SCRIPT_DIR/../../docker/kyon-cetc-focal-ros1/setup.sh ]; then
    source $SCRIPT_DIR/../../docker/kyon-cetc-focal-ros1/setup.sh
fi

# Check if concert_launcher is installed
if ! command -v concert_launcher &> /dev/null; then
    echo "Error: concert_launcher is not installed. Please install it first."
    echo "You can install it with: pip install --user concert_launcher"
    exit 1
fi

# Set default configuration file
export CONCERT_LAUNCHER_DEFAULT_CONFIG=$SCRIPT_DIR/concert_launcher_config.yaml

# Handle commands
case "$1" in
    sim)
        echo "Starting robot in simulation mode..."
        concert_launcher run sim_all
        ;;
    status)
        echo "Checking status of running processes..."
        concert_launcher status
        ;;
    kill)
        echo "Killing all running processes..."
        concert_launcher kill --all
        ;;
    monitor)
        echo "Starting monitoring session..."
        concert_launcher mon
        ;;
    *)
        echo "Usage: $0 {sim|status|kill|monitor}"
        exit 1
        ;;
esac