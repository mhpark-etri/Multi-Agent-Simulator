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


## ── v1.9 협업 태스크 런타임 ───────────────────────────────────────
## Docker 이미지에는 이미 빌드되어 있습니다. 이미지 없이 수동 구성할 때만 필요합니다.

## JnP 0.8.1 (릴레이·다목적 이동·충돌회피·분산 탐색)
mkdir -p /root/catkin_ws_jnp081/src
ln -sf /opt/ros/noetic/share/catkin/cmake/toplevel.cmake /root/catkin_ws_jnp081/src/CMakeLists.txt
ln -sf /root/tesla/jnp/jnp_0.8.1 /root/catkin_ws_jnp081/src/jnp
cd /root/catkin_ws_jnp081 && catkin_make

## 탐사 스택 (프런티어 검출 rrt_exploration + 지도 병합 map_merge)
##  ※ 원본 라이선스(MIT / BSD-3)는 NOTICE, third_party/README.md 참조
sudo apt-get install -y python3-sklearn ros-noetic-slam-toolbox \
     ros-noetic-dwa-local-planner ros-noetic-global-planner ros-noetic-topic-tools
mkdir -p /root/catkin_ws_explo/src
cp -r /root/tesla/third_party/* /root/catkin_ws_explo/src/
cd /root/catkin_ws_explo && catkin_make -DCMAKE_BUILD_TYPE=Release
grep -q catkin_ws_explo /root/.bashrc || \
  echo "source /root/catkin_ws_explo/devel/setup.bash" >> /root/.bashrc

# back
cd /root/tesla/
