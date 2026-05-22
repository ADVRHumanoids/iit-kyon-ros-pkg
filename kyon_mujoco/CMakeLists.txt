cmake_minimum_required(VERSION 3.20)
project(kyon_mujoco)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config mjcf world
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS src/simulator_wrapper.bash
  DESTINATION lib/${PROJECT_NAME})

ament_package()