# kyon_isaac
IsaacLab powered simulation for the Kyon robot, integrated with XBot2.

## Prerequisites

1. You have the official IsaacLab image available. If not:
    - `git clone https://github.com/isaac-sim/IsaacLab`
    - `cd IsaacLab/docker`
    - `python3 container.py start`

2. If you're running XBot2 via Docker, make sure that the shared folder `/tmp/.xbot2_isaac` exists and is mounted
    - `mkdir -p /tmp/.xbot2_isaac`
    - make sure that `/tmp/.xbot2_isaac:/tmp/.xbot2_isaac:rw` is listed inside the *volumes* section of the Docker compose file

3. You compiled the `xbot2_zmq` package inside the machine (or contained) that runs XBot2

## How to run

1. `./lib/src/run_sim_host.bash` -> this will launch the `run_sim.py` script inside Isaac's Docker container; IsaacSim's window should appear, and the Kyon robot should be visible, standing still in its homing configuration
2. `cd ../kyon_config` 
3. `xbot2-core -C kyon_basic.yaml --hw isaac`

