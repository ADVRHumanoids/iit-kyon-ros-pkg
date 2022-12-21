cmake_minimum_required(VERSION 3.0)
project(cetc_sat_config)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY hal
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(FILES cetc_sat_basic.yaml 
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
