# iit-kyon-ros-pkg

ROS 2 packages for simulating the KYON robot, designed and built at the Humanoids and Human-Centred Mechatronics Laboratory (HHCM).

The repository contains:

- [`kyon_urdf`](kyon_urdf/): URDF/Xacro robot description, including meshes, collision models, and visualization configuration.
- [`kyon_srdf`](kyon_srdf/): SRDF semantic descriptions for KYON model variants.
- [`kyon_mujoco`](kyon_mujoco/): MuJoCo simulation package, including the robot configuration, environments, and launch files.
- [`kyon_gazebo`](kyon_gazebo/): Gazebo simulation package, with robot sensor definitions, worlds, and launch files.
- [`kyon_cartesio`](kyon_cartesio/): Configuration files for [CartesI/O](https://github.com/ADVRHumanoids/CartesianInterface), the inverse-kinematics solver.
- [`kyon_config`](kyon_config/): Configuration files for the [XBot2](https://github.com/ADVRHumanoids/xbot2) middleware.

## URDF/SRDF generation

The robot models are built with `xacro`, which lets you enable or disable features to match the robot's modular configuration. Generate the URDF from the [`kyon_urdf`](kyon_urdf/) directory with:

```
xacro urdf/kyon.urdf.xacro -o kyon.urdf
```

This generates the KYON URDF for the legged configuration with both arms. Add `wheels:=true` to generate the wheeled configuration, or `arms:=false` to omit the arms. The available arguments are listed in [`kyon_urdf/urdf/config/kyon.urdf.xacro`](kyon_urdf/urdf/config/kyon.urdf.xacro).

Similarly, generate the SRDF from the [`kyon_srdf`](kyon_srdf/) directory with:

```
xacro srdf/kyon.srdf.xacro -o kyon.srdf
```
sharing the same arguments as for the URDF generation.

## Run in docker container
Optionally, the repository runs in a docker container that comes with the SDKs used to control the robot. We suggest using the docker to run the simulators to avoid dependencies problems.

### Build the docker
in the [`docker`](docker/noble-ros2/) folder, build and start the docker running `docker compose up -d`. Then, you can open a terminator on a separate window running `docker compose exec dev terminator`.


### Simulation
At this stage, the package provides two simulation frameworks for the KYON robot: [`gz-sim`](https://github.com/gazebosim/gz-sim) and [`MuJoCo`](https://github.com/google-deepmind/mujoco). Camera and perception tools are provided for `gz-sim` only.

To start the simulator run the command:

```
ros2 launch kyon_gazebo kyon_world.launch arms:=[TRUE/false] wheels:=[TRUE/false] 
```

The simulator starts spawning the robot in the configuration defined by the arguments (in capitals the default values).
Similarly, the MuJoCo simulator starts by running the command

```
ros2 launch kyon_mujoco kyon_world.launch arms:=[TRUE/false] wheels:=[TRUE/false] 
```

In both simulators, XBot2's libraries and bridges are loaded to start the communication between robot's devices (i.e., joints and sensors) and the simulator and open the communication with the XBot2 middleware. Please refer to [XBot2 Documentation](https://advrhumanoids.github.io/xbot2/master/index.html) for more details on how to use XBot.

### Playground
Use a single joystick to control KYON's locomotion policy and inverse-kinematics arm controller.

To start the simulation, open a Terminator terminal in the Docker container:

```bash
docker compose -f docker/noble-ros2/compose.yaml exec dev terminator
```

With a joystick connected to your computer, run the simulation and control pipeline inside the container:

```bash
/home/user/scripts/playground.bash
```

Wait until the following green message appears:

```text
################################################################
#                                                              #
#  Kyon playground stack is running. Press Ctrl-C to stop it.  #
#                                                              #
################################################################
```

You can then move the robot.

When running, you can control the left and right arm pushing the RT and LR buttons, respectively. You can move the end-effector on the x-y axes using the left axes, and the z-axes by using the vertical right axes. Arms are moved using the CartesI/O IK solver through the [`kyon_cartesio`](kyon_cartesio/) config and launch files. Alternatively, by not pushing either RT and LT, the joystick will generate a twist command for the base and the locomotion policy will drive the robot around.
