project(cetc_sat_srdf)

find_package(catkin REQUIRED)

catkin_package()

# main srdf, with acm
generate_srdf(
  XACRO cetc_sat.srdf.xacro 
  CONFIG config/cetc_sat.urdf.xacro 
  ADD_TO_ALL TRUE
  GEN_ACM TRUE
)

# updated acm for capsule model
generate_capsule_srdf_acm(
  CONFIG_NAME cetc_sat
  ADD_TO_ALL TRUE
)

# plain srdf for virtual frame model
#generate_srdf(
#  XACRO cetc_sat.srdf.xacro 
#  CONFIG config/cetc_sat_virtual_frame.urdf.xacro 
#  ADD_TO_ALL TRUE
#)

# mark srdf for installation
install(DIRECTORY srdf
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
