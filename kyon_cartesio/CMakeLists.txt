cmake_minimum_required(VERSION 3.20)
project(kyon_cartesio)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(
  FILES 
  config/kyon_stack.yaml
  DESTINATION 
  share/${PROJECT_NAME}/config
)

ament_package()
