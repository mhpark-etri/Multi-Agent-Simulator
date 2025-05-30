rosservice call /gazebo/unpause_physics
sleep 1
rostopic pub /locobot_0/shoulder_controller/command std_msgs/Float64 "data: -0.5" --once
sleep 1
rostopic pub /locobot_0/elbow_controller/command std_msgs/Float64 "data: 1.6" --once
sleep 1
rostopic pub /locobot_0/tilt_controller/command std_msgs/Float64 "data: 0.0" --once
sleep 2
rostopic pub /locobot_1/shoulder_controller/command std_msgs/Float64 "data: -0.5" --once
sleep 1
rostopic pub /locobot_1/elbow_controller/command std_msgs/Float64 "data: 1.6" --once
sleep 1
rostopic pub /locobot_1/tilt_controller/command std_msgs/Float64 "data: 0.0" --once


