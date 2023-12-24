# iit-kyon-ros-pkg
## Dependencies
We suggest to use the `forest` tool to install the main dependencies of the controller in an easier way:
```
[sudo] pip3 install hhcm-forest
mkdir forest_ws && cd forest_ws
forest init
echo ". ~/forest_ws/setup.bash" >> ~/.bashrc
forest add-recipes git@github.com:advrhumanoids/multidof_recipes.git
```
Once `forest` has been sucessfully installed, you can now install the package dependencies:
```
cd ~/forest_ws
forest grow realsense_gazebo_description
forest grow velodyne_description
forest grow velodyne_gazebo_plugins
forest grow iit-dagana-ros-pkg
```

You can now clone the `iit-kyon-ros-pkg` repository in a source folder:
```
cd ~/forest_ws/ros_src
git clone https://github.com/robot-21/iit-kyon-ros-pkg.git
```

