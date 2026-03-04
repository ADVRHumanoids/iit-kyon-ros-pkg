#!/bin/bash

# current script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# docker dir
cd $SCRIPT_DIR/../../docker/iit-kyon-ros-pkg-isaac

# make shared directory to host sockets
mkdir -p /tmp/.xbot2_isaac

# build and run the docker container
docker compose up -d dev --no-recreate

# execute simulation script
docker compose exec dev bash -ic "python /workspace/iit-kyon-ros-pkg/kyon_isaac/lib/src/run_sim.py"
