cmake_minimum_required(VERSION 2.8.3)

project(ketg_description)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  sensor_msgs
  urdf
  xacro
  gazebo_ros
)

catkin_package()

find_package(roslaunch)

foreach(dir . urdf)
	install(DIRECTORY ${dir}/
		DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/${dir})
endforeach(dir)
