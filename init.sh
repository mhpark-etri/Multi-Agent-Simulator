#!/bin/bash
## gnome-terminal config ##
cd /etc/default/
echo 'LANG=en_US.UTF-8' | sudo tee -a /etc/default/locale

## AWS Robomaker - AWS 모델들은 당분간 사용하지 않음 ##
# warehouse build
# cd /root/tesla/models_aws/aws-robomaker-small-warehouse-world-ros1/
# rosdep install --from-paths . --ignore-src -r -y
# colcon build
# source install/setup.sh

# hospital
# cd /root/tesla/models_aws/aws-robomaker-hospital-world-ros1/
# rosws update
# rosdep install --from-paths . --ignore-src -r -y
# chmod +x setup.sh
# ./setup.sh
# colcon build
# source install/setup.sh

# small house
# cd /root/tesla/models_aws/aws-robomaker-small-house-world-ros1/
# rosws update
# rosdep install --from-paths . --ignore-src -r -y
# colcon build
# source install/setup.sh

# book store
# cd /root/tesla/models_aws/aws-robomaker-bookstore-world-ros1/
# rosws update
# rosdep install --from-paths . --ignore-src -r -y
# colcon build
# source install/setup.sh

## Interbotix 설치
sudo chmod 1777 /tmp
sudo apt-get update
cd /root/tesla
sudo chmod a+x xslocobot_amd64_install4.sh
source xslocobot_amd64_install4.sh -b create3 -d noetic

## Copy gazebo models & world
mkdir -p ~/.gazebo/models
cd /root/tesla/models/
cp -r * ~/.gazebo/models
cd /root/tesla/worlds/
cp -r * /usr/share/gazebo-11/worlds

## Chmod gazebo local model & world folder ##
cd ~/.gazebo
chmod -R 777 models/
cd /usr/share/gazebo-11
chmod -R 777 worlds/

# back
cd /root/tesla/
