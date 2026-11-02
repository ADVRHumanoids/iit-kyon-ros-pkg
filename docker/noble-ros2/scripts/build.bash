#!/bin/bash
set -e

# chown to user (needed after mounting volumes)
sudo chown user:user ~/test_ws ~/test_ws/src

# update recipes
(cd ~/test_ws/recipes/multidof_recipes; git pull origin ros2)

# rebuild the mounted packages (deps are already built in the Docker image)
cd ~/test_ws
source ~/env/bin/activate
source /opt/xbot/setup.sh
source /opt/ros/jazzy/setup.bash
source setup.bash
forest grow iit-kyon-ros-pkg

export HHCM_FOREST_CLONE_DEFAULT_PROTO=https
export PYTHONUNBUFFERED=1
cd src/xbot2_mujoco
git pull 
cd ~/test_ws/build/xbot2_mujoco
make install
