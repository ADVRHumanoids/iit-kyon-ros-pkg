cmake_minimum_required(VERSION 3.1.0)
project(CETC_SAT_description)

add_compile_options(-std=c++14)

find_package(catkin REQUIRED COMPONENTS
             roscpp)

install(DIRECTORY examples/launch/
    DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
    FILES_MATCHING PATTERN "*.launch"
    PATTERN ".svn" EXCLUDE
    )

