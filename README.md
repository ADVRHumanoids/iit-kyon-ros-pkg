# CETC_SAT_description

The package contains the urdf and srdf of the quadruped robot for the CETC-SAT project. The files are generated thousgh xacro and robot's components can be removed using specific parameters.

Xacro takes in input a .yaml file for the robot's kinematic properties (links' length, position and orientation). The file is in:

`./cetc_sat_urdf/urdf/config/kinematics_properties.yaml`

An example of usage can be found in `./examples/launch/cetc_sat_example_urdf.launch` that spawns the robot in rviz with the `robot_state_publisher` and moves it with the `joint_state_publisher_gui`

## Source
To make the repository visible, clone it in a sourced folder or, alternatively, export the main folder:

```
echo "export ROS_PACKAGE_PATH=$ROS_PACKAGE_PATH:/path/to/robot_pkg" >> ~/.bashrc
source .bashrc
```

## Use in your project
Generate the urdf and srdf in your project using the xacro command in your `.launch` file:

```
<param name="robot_description"
		 command="$(find xacro)/xacro $(find cetc_sat_urdf)/urdf/cetc_sat.urdf.xacro floating_joint:=$(arg floating_base) upper_body:=$(arg arms) legs:=$(arg legs)"/>
		 
<param name="robot_description_semantic"
		 command="$(find xacro)/xacro $(find cetc_sat_srdf)/srdf/cetc_sat.srdf.xacro floating_joint:=$(arg floating_base) upper_body:=$(arg arms) legs:=$(arg legs)"/>
