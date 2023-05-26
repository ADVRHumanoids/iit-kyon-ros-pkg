cmake_minimum_required(VERSION 3.0)

set(ROBOT_NAME kyon)
project(iit-kyon-ros-pkg VERSION 1.0.0)

include(GenerateXrdf.cmake)

## add sub-packages
add_subdirectory(kyon_urdf)
add_subdirectory(kyon_srdf)
add_subdirectory(kyon_gazebo)
add_subdirectory(kyon_config)
add_subdirectory(kyon_cartesio)

enable_testing()
#add_subdirectory(kyon_test)

include(GenerateDeb.cmake)
