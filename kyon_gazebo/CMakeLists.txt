cmake_minimum_required(VERSION 3.8)
project(kyon_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_eigen REQUIRED)
find_package(Eigen3 REQUIRED)

# gz hesai_qt128 cloud -> Hesai QT128 driver cloud
add_executable(sim_hesai_adapter src/sim_hesai_adapter.cpp)
target_compile_features(sim_hesai_adapter PRIVATE cxx_std_17)
target_link_libraries(sim_hesai_adapter Eigen3::Eigen)
ament_target_dependencies(sim_hesai_adapter rclcpp sensor_msgs nav_msgs tf2 tf2_ros tf2_eigen)

install(DIRECTORY launch worlds urdf config
  DESTINATION share/${PROJECT_NAME}
)

install(TARGETS sim_hesai_adapter
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  src/reset_initial_state.bash
  DESTINATION lib/${PROJECT_NAME}
)

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
