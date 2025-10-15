project(kyon_urdf)

find_package(ament_cmake REQUIRED)
cmake_policy(SET CMP0057 NEW)

# mark urdf, meshes and launch files for installation
install(DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}
)

# install(DIRECTORY launch
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
# )

install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

