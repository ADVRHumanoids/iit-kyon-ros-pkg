cmake_minimum_required(VERSION 3.0)
project(cetc_sat_cartesio)

find_package(catkin REQUIRED)

catkin_package()

install(
  FILES 
  config/cetc_test_stack.yaml
  DESTINATION 
  ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
