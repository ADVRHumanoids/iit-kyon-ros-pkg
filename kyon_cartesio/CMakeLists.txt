cmake_minimum_required(VERSION 3.20)
project(kyon_cartesio)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS src/parking.py 
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
