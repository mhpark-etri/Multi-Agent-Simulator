#!/bin/bash
## gnome-terminal config ##
cd /etc/default/
echo 'LANG=en_US.UTF-8' | sudo tee -a /etc/default/locale

## Jnp 복사(개별 빌드 필요 - 페이지 설치 메뉴얼 참고)
sudo mkdir -p /root/catkin_ws_jnp/src/jnp
cd /root/catkin_ws_jnp/src/jnp
sudo cp -r /root/tesla/jnp/jnp_0.2.1/* /root/catkin_ws_jnp/src/jnp

## UNI050_BASE 모델 복사(개별 빌드 필요 - 페이지 설치 메뉴얼 참고)
# uni_description
sudo mkdir -p ~/catkin_ws_ai_bot/src
sudo cp -r /root/tesla/robots/ketg_ai-bot_platform/* ~/catkin_ws_ai_bot/src

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

## Interbotix 설치
sudo chmod 1777 /tmp
sudo apt-get update
cd /root/tesla
sudo chmod a+x xslocobot_amd64_install4.sh
source xslocobot_amd64_install4.sh -b create3 -d noetic

# back
cd /root/tesla/
