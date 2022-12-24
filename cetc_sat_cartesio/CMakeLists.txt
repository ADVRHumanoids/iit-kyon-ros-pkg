cmake_minimum_required(VERSION 3.0)
project(cetc_sat_cartesio)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(
  FILES 
  config/cetc_sat_stack.yaml
  DESTINATION 
  ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
