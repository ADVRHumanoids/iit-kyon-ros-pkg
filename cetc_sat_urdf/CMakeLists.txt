project(cetc_sat_urdf)

find_package(catkin REQUIRED COMPONENTS)

catkin_package()

# mark urdf, meshes and launch files for installation
install(DIRECTORY meshes
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(DIRECTORY urdf
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

# main urdf
generate_urdf(
  XACRO cetc_sat.urdf.xacro 
  CONFIG config/cetc_sat.urdf.xacro 
  ADD_TO_ALL TRUE
)

# virtual frame urdf
generate_urdf(
  XACRO cetc_sat.urdf.xacro 
  #CONFIG config/cetc_sat_virtual_frame.urdf.xacro 
  ADD_TO_ALL TRUE
)

# capsule model for main urdf
generate_capsule_urdf(
  CONFIG_NAME cetc_sat
  ADD_TO_ALL TRUE
)
