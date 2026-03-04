#!/bin/bash

# current script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# docker dir
cd $SCRIPT_DIR/../docker/iit-kyon-ros-pkg-isaac

# build and run the docker container
docker compose up -d dev 

# execute simulation script
docker compose exec dev python /workspace/iit-kyon-ros-pkg/kyon_isaac/src/run_sim.py
