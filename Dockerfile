####################
###### OS 설치 ######
####################
# 1. 베이스 이미지로 Ubuntu 20.04를 사용합니다.
FROM ubuntu:20.04

######################
###### 기본 설정 ######
######################
# 1. 작성자 정보
LABEL maintainer="tspark@teslasystem.co.kr"

# 2. 환경 변수 설정
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" keyboard-configuration

# 3. 작업 디렉토리 설정
# WORKDIR /root/tesla

# 4. 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    curl \
    wget \
    python3-pip \
    gedit \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8   
RUN apt-get install -y gnome-terminal

############################
###### Turtlebot3 설치 ######
############################
# 1. ROS Noetic 설치 (TurtleBot3와 종속성)
RUN apt-get update && apt-get upgrade -y
RUN wget https://raw.githubusercontent.com/ROBOTIS-GIT/robotis_tools/master/install_ros_noetic.sh
RUN chmod 755 ./install_ros_noetic.sh
RUN bash ./install_ros_noetic.sh

 # 2. ROS Noetic 관련 종속적 패키지 설치
RUN apt-get install -y ros-noetic-joy ros-noetic-teleop-twist-joy \
   ros-noetic-teleop-twist-keyboard ros-noetic-laser-proc \
   ros-noetic-rgbd-launch ros-noetic-rosserial-arduino \
   ros-noetic-rosserial-python ros-noetic-rosserial-client \
   ros-noetic-rosserial-msgs ros-noetic-amcl ros-noetic-map-server \
   ros-noetic-move-base ros-noetic-urdf ros-noetic-xacro \
   ros-noetic-compressed-image-transport ros-noetic-rqt* ros-noetic-rviz \
   ros-noetic-gmapping ros-noetic-navigation ros-noetic-interactive-markers

# 3. TurtleBot3 패키지 다운로드 및 설치
RUN apt-get install -y ros-noetic-dynamixel-sdk \
    ros-noetic-turtlebot3-msgs \
    ros-noetic-turtlebot3

# 4. ROS 환경 설정
RUN echo "source /opt/ros/noetic/setup.bash" >> /root/.bashrc

# 5. ROS 관련 기능들
# 5-1. Navigation
# Launch
COPY ros/navi/launch/ /opt/ros/noetic/share/turtlebot3_navigation/launch/
# RViz
COPY ros/navi/rviz/ /opt/ros/noetic/share/turtlebot3_navigation/rviz/
# Map
RUN sudo mkdir /opt/ros/noetic/share/turtlebot3_navigation/maps/backup
RUN sudo mv /opt/ros/noetic/share/turtlebot3_navigation/maps/map.pgm /opt/ros/noetic/share/turtlebot3_navigation/maps/backup/
RUN sudo mv /opt/ros/noetic/share/turtlebot3_navigation/maps/map.yaml /opt/ros/noetic/share/turtlebot3_navigation/maps/backup/
COPY ros/navi/maps/ /opt/ros/noetic/share/turtlebot3_navigation/maps/

##############################################
##### Multi-Agent-Simulator-Docker 설치 ######
##############################################
## 1. Multi-Agent-Simulator-Docker 코드 복사
COPY code/Multi-Agent-Simulator/ /root/tesla/code/Multi-Agent-Simulator
COPY models/ /root/tesla/models/
COPY worlds/ /root/tesla/worlds/

# 2. Multi-Agent-Simulator-Docker 관련 패키지 설치
RUN pip install pyyaml
RUN pip3 install PySide6
RUN sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -cs` main" > /etc/apt/sources.list.d/ros-latest.list'
RUN sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
RUN sudo apt update
RUN sudo apt install -y python3-colcon-common-extensions
    
# 3. AWS Robomaker 관련 복사 및 빌드
# COPY models_aws/ /root/tesla/models_aws/

# 4. Locobot - xslocobot 설치
# 차후 구현 예정

# 5. 프로그램 필요 초기화
COPY init.sh /root/tesla/


#######################################################
###### PyLobot 설치 (기본적으로 Gazebo 같이 설치 됨 ######
#######################################################
# 1. PyLobot 설치
# RUN mkdir -p /mnt/temp2/
# COPY code/pyrobot/ /mnt/temp2/
# COPY code/pyrobot/ /root/
# RUN chmod +x /root/locobot_install_all_focal_p3.sh 
# RUN bash ./root/locobot_install_all_focal_p3.sh -t sim_only -p 3 -l interbotix

#############################
##### 여기까지 pashse 2 ######
#############################


