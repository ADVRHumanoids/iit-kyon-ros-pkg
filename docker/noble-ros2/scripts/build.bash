#!/bin/bash
set -e

# chown to user (needed after mounting volumes)
sudo chown user:user ~/test_ws ~/test_ws/src

# rebuild the mounted packages (deps are already built in the Docker image)
cd ~/test_ws
source ~/env/bin/activate
source /opt/ros/jazzy/setup.bash
source setup.bash

export HHCM_FOREST_CLONE_DEFAULT_PROTO=https
export PYTHONUNBUFFERED=1
cd src/xbot2_mujoco
git pull 
cd ~/test_ws/build/xbot2_mujoco
make install

# build tests
cd build/iit-kyon-ros-pkg
cmake -DXBOT2_IFC_BUILD_TESTS=1 .
make -j ${FOREST_JOBS:-1}
