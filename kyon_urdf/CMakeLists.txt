cmake_minimum_required(VERSION 3.20)

project(kyon_urdf)

find_package(ament_cmake REQUIRED)

cmake_policy(SET CMP0057 NEW)

# mark urdf, meshes and launch files for installation
install(DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}
)

# install(DIRECTORY launch
#   DESTINATION share/${PROJECT_NAME}
# )

install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
