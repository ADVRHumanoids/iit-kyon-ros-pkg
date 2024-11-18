cmake_minimum_required(VERSION 3.8)
project(kyon_srdf)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(rclcpp REQUIRED)
find_package(srdfdom REQUIRED)
find_package(urdf REQUIRED) 

# mark srdf files for installation
install(DIRECTORY srdf
  DESTINATION share/${PROJECT_NAME}
)

# main srdf, with acm
# generate_srdf(
#   XACRO ${ROBOT_NAME}.srdf.xacro
#   CONFIG config/${ROBOT_NAME}.urdf.xacro
#   ADD_TO_ALL TRUE
#  GEN_ACM TRUE
# )

# updated acm for capsule model
#generate_capsule_srdf_acm(
#  CONFIG_NAME ${ROBOT_NAME}
#  ADD_TO_ALL TRUE
#)

# plain srdf for virtual frame model
#generate_srdf(
#  XACRO ${ROBOT_NAME}.srdf.xacro
#  CONFIG config/${ROBOT_NAME}_virtual_frame.urdf.xacro
#  ADD_TO_ALL TRUE
#)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
