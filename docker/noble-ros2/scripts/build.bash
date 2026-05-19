#!/bin/bash
set -e

# chown to user (needed after mounting volumes)
sudo chown user:user ~/test_ws ~/test_ws/src

# rebuild the mounted packages (deps are already built in the Docker image)
cd ~/test_ws
source /opt/ros/jazzy/setup.bash
source setup.bash

export HHCM_FOREST_CLONE_DEFAULT_PROTO=https
export PYTHONUNBUFFERED=1
forest grow iit-kyon-ros-pkg --verbose --clone-depth 1 -j ${FOREST_JOBS:-1} --tag-override hesai_jt128
forest grow xbot2_mujoco --verbose --clone-depth 1 -j ${FOREST_JOBS:-1}

# build tests
cd build/iit-kyon-ros-pkg
cmake -DXBOT2_IFC_BUILD_TESTS=1 .
make -j ${FOREST_JOBS:-1}
