cmake_minimum_required(VERSION 3.0)

set(ROBOT_NAME cetc_sat)
project(CETC_SAT_description VERSION 1.0.0)

include(GenerateXrdf.cmake)

## add sub-packages
add_subdirectory(cetc_sat_urdf)
add_subdirectory(cetc_sat_srdf)
add_subdirectory(cetc_sat_gazebo)
#add_subdirectory(cetc_sat_config)
add_subdirectory(cetc_sat_cartesio)

enable_testing()
#add_subdirectory(cetc_sat_test)

include(GenerateDeb.cmake)
