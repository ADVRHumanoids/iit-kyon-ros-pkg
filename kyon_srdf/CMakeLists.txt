project(kyon_srdf)

cmake_minimum_required(VERSION 3.20)

find_package(ament_cmake REQUIRED)

install(DIRECTORY srdf
  DESTINATION share/${PROJECT_NAME}
)

# Additional dependencies for ROS 2
ament_export_dependencies(xacro)

ament_package()
