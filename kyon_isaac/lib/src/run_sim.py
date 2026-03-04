# Copyright (c) 2022-2025, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""This script demonstrates how to use the interactive scene interface to setup a scene with multiple prims.

.. code-block:: bash

    # Usage
    ./isaaclab.sh -p scripts/tutorials/02_scene/create_scene.py --num_envs 32

"""

"""Launch Isaac Sim Simulator first."""


import argparse
import sys

from isaaclab.app import AppLauncher

# local imports
# import cli_args  # isort: skip

# add argparse arguments
parser = argparse.ArgumentParser(description="Train an RL agent with RSL-RL.")
parser.add_argument("--video", action="store_true", default=False, help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video (in steps).")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument(
    "--agent", type=str, default="rsl_rl_cfg_entry_point", help="Name of the RL agent configuration entry point."
)
parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
parser.add_argument(
    "--use_pretrained_checkpoint",
    action="store_true",
    help="Use the pre-trained checkpoint from Nucleus.",
)
parser.add_argument("--real-time", action="store_true", default=False, help="Run in real-time, if possible.")
# append RSL-RL cli arguments
# cli_args.add_rsl_rl_args(parser)
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli, hydra_args = parser.parse_known_args()
# always enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import torch
import math
import time

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.assets.articulation import Articulation
from isaaclab.sensors.imu import Imu
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.sim import SimulationContext
from isaaclab.utils import configclass

import os
import socket
import yaml

##
# Pre-defined configs
##
from kyon_isaac.assets.kyon_play import KYON_WHEEL_BODY_CFG_PLAY  # isort:skip


@configclass
class KyonSceneCfg(InteractiveSceneCfg):
    """Configuration for the simulation scene."""

    # ground plane
    ground = AssetBaseCfg(prim_path="/World/defaultGroundPlane", spawn=sim_utils.GroundPlaneCfg())

    # lights
    dome_light = AssetBaseCfg(
        prim_path="/World/Light", spawn=sim_utils.DomeLightCfg(intensity=3000.0, color=(0.75, 0.75, 0.75))
    )

    # articulation
    robot: ArticulationCfg = KYON_WHEEL_BODY_CFG_PLAY.replace(prim_path="{ENV_REGEX_NS}/Robot")


def run_simulator(sim: sim_utils.SimulationContext, scene: InteractiveScene):
    """Runs the simulation loop."""
    
    # Extract scene entities
    robot : Articulation = scene["robot"]
    imu_sensors: dict[str, Imu] = {}
    for sn, s in scene.sensors.items():
        print(f"Sensor name: {sn}, type: {type(s)}")
        if isinstance(s, Imu):
            print(f"IMU sensor found: {sn}")
            imu_sensors[sn] = s
    
    # Define simulation stepping
    sim_dt = sim.get_physics_dt()
    count = 0
    time_sim = 0
    # real-time factor tracking
    rtf_last_print = time.time()
    rtf_sim_elapsed = 0.0
    rtf_steps = 0

    # Socket for communication
    server_socket_path = "/tmp/.xbot2_isaac/xbot2_isaac_server.sock"
    if os.path.exists(server_socket_path):
        os.unlink(server_socket_path)
    
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.bind(server_socket_path)
    sock.setblocking(False)
    os.chmod(server_socket_path, 0o777)

    print(f"Server socket created at {server_socket_path}")

    client_sockets = set()
    
    # Simulation loop
    qinit = robot.data.default_joint_pos.clone()
    robot.write_joint_position_to_sim(qinit)
    robot.set_joint_position_target(qinit)
    print(f'Initial joint positions set to: {qinit.cpu().numpy().flatten().tolist()}')

    while simulation_app.is_running():

        tic = time.time()

        # broadcast robot state to all clients
        state_msg = {'type': 'state'}
        state_msg['time'] = time_sim
        state_msg['q'] = robot.data.joint_pos.cpu().numpy().flatten().tolist()
        state_msg['dq'] = robot.data.joint_vel.cpu().numpy().flatten().tolist()
        state_msg['tau'] = robot.data.applied_torque.cpu().numpy().flatten().tolist()
        state_msg['k'] = robot.data.joint_stiffness.cpu().numpy().flatten().tolist()
        state_msg['d'] = robot.data.joint_damping.cpu().numpy().flatten().tolist()
        state_msg['qref'] = robot.data.joint_pos_target.cpu().numpy().flatten().tolist()
        state_msg['vref'] = robot.data.joint_vel_target.cpu().numpy().flatten().tolist()
        state_msg['tauref'] = robot.data.joint_effort_target.cpu().numpy().flatten().tolist()
        
        state_msg['imu'] = dict()
        for imu_name, imu_sensor in imu_sensors.items():
            imu_data = imu_sensor.data
            state_msg['imu'][imu_name] = {
                'quat_w': imu_data.quat_w.cpu().numpy().flatten().tolist(),
                'lin_acc_b': imu_data.lin_acc_b.cpu().numpy().flatten().tolist(),
                'ang_vel_b': imu_data.ang_vel_b.cpu().numpy().flatten().tolist(),
            }

        state_msg = yaml.dump(state_msg)
        sockets_to_remove = []
        for cli_addr in client_sockets:
            try:
                sock.sendto(state_msg.encode(), cli_addr)
            except ConnectionRefusedError as e:
                print(f"Client at {cli_addr} disconnected.")
                sockets_to_remove.append(cli_addr)
            except Exception as e:
                print(f"Error sending state to {cli_addr}: {e}")

        for s in sockets_to_remove:
            client_sockets.remove(s)
        
        sockets_to_remove.clear()

        # handle client connections
        try:
            # recv, if not message available, will raise BlockingIOError
            data, cli_addr = sock.recvfrom(4096)

            # consume buffer 
            while True:
                try:
                    data, cli_addr = sock.recvfrom(4096)
                except BlockingIOError:
                    break

            # decode data
            data = data.decode('utf-8')
            data = yaml.safe_load(data)
            data_type = data['type']
            if data_type == 'discovery':
                response = {'type': 'discovery'}
                response['joint_names'] = robot.joint_names
                response['imu_sensors'] = list(imu_sensors.keys())
                try:
                    sock.sendto(yaml.dump(response).encode('utf-8'), cli_addr)
                except Exception as e:
                    print(f"Error sending discovery response to {cli_addr}: {e}")
                client_sockets.add(cli_addr)
                print(f"Client at {cli_addr} connected.")

            elif data_type == 'control':
                joint_pos_def = torch.tensor(data['q'], device=robot.device).unsqueeze(0)
                robot.set_joint_position_target(joint_pos_def)
                joint_vel_def = torch.tensor(data['dq'], device=robot.device).unsqueeze(0)
                robot.set_joint_velocity_target(joint_vel_def)
                joint_effort_def = torch.tensor(data['tau'], device=robot.device).unsqueeze(0)
                robot.set_joint_effort_target(joint_effort_def)

            else:
                print(f"Unknown data type received: {data_type}")

        except BlockingIOError:
            pass
        

        # simulation loop
        # -- write data to sim
        scene.write_data_to_sim()
        # Perform step
        sim.step()
        time_sim += sim_dt
        rtf_sim_elapsed += sim_dt
        rtf_steps += 1
        # Increment counter
        count += 1
        # Update buffers
        scene.update(sim_dt)

        # print real-time factor every ~1s
        now = time.time()
        real_elapsed = now - rtf_last_print
        if real_elapsed >= 1.0:
            real_time_factor = rtf_sim_elapsed / real_elapsed if real_elapsed > 0 else float('inf')
            print(
                f"[INFO] Real-time factor: {real_time_factor:.3f}x "
                f"(sim: {rtf_sim_elapsed:.3f}s, real: {real_elapsed:.3f}s, steps: {rtf_steps})"
            )
            rtf_last_print = now
            rtf_sim_elapsed = 0.0
            rtf_steps = 0

        # time delay for real-time evaluation
        toc = time.time()
        sleep_time = sim_dt - (toc - tic)
        if args_cli.real_time and sleep_time > 0:
            time.sleep(sleep_time)


def main():
    """Main function."""
    # Load kit helper
    sim_cfg = sim_utils.SimulationCfg(device=args_cli.device)
    sim = SimulationContext(sim_cfg)
    
    # Set main camera
    sim.set_camera_view([2.5, 0.0, 4.0], [0.0, 0.0, 2.0])
    
    # Design scene
    scene_cfg = KyonSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)
    
    # Play the simulator
    sim.reset()
    
    # Now we are ready!
    print("[INFO]: Setup complete...")
    
    # Run the simulator
    run_simulator(sim, scene)


if __name__ == "__main__":
    # run the main function
    main()
    # close sim app
    simulation_app.close()
