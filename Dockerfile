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

# 1-1. 다운로드 미러 변경
RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://kr.archive.ubuntu.com/ubuntu/|g' /etc/apt/sources.list

# 2. 환경 변수 설정
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV DEBIAN_FRONTEND=noninteractive

# 3. 로케일 설정 및 한글 글꼴 설치
RUN apt-get clean && rm -rf /var/lib/apt/lists/* \
    && apt-get update --fix-missing \
    && apt-get install -y locales fonts-nanum \
    && locale-gen ko_KR.UTF-8 \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=ko_KR.UTF-8 LC_ALL=ko_KR.UTF-8 LANGUAGE=ko_KR.UTF-8

# 환경 변수 설정
ENV LANG ko_KR.UTF-8
ENV LANGUAGE ko_KR:ko
ENV LC_ALL ko_KR.UTF-8

# 한글 로케일 확인을 위해 기본 패키지 설치
RUN apt-get install -y sudo git curl wget python3-pip gedit

# Python3 심볼릭 링크 추가
RUN ln -s /usr/bin/python3 /usr/bin/python

# Flask 설치
RUN pip3 install --ignore-installed flask
RUN apt-get update && apt-get install -y gnome-terminal


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
RUN echo '# add by tesla : ROS Collaboration' >> /root/.bashrc && \
    echo 'export TURTLEBOT3_MODEL=burger' >> /root/.bashrc

# .bashrc를 source하여 환경 변수를 적용
RUN echo 'source ~/.bashrc' >> ~/.bash_profile

# 5. ROS 관련 기능들
# 5-1. Navigation
RUN mkdir -p /root/tesla/ros
COPY ros /root/tesla/ros/
# Launch
COPY ros/navi/launch/turtlebot/ /opt/ros/noetic/share/turtlebot3_navigation/launch/
# RViz
COPY ros/navi/rviz/turtlebot/ /opt/ros/noetic/share/turtlebot3_navigation/rviz/
# Map
RUN mkdir /opt/ros/noetic/share/turtlebot3_navigation/maps/backup
RUN mv /opt/ros/noetic/share/turtlebot3_navigation/maps/map.pgm /opt/ros/noetic/share/turtlebot3_navigation/maps/backup/
RUN mv /opt/ros/noetic/share/turtlebot3_navigation/maps/map.yaml /opt/ros/noetic/share/turtlebot3_navigation/maps/backup/
COPY ros/navi/maps/ /opt/ros/noetic/share/turtlebot3_navigation/maps/

##############################################
##### Multi-Agent-Simulator-Docker 설치 ######
##############################################
# 1. Multi-Agent-Simulator-Docker 코드 복사
COPY code/Multi-Agent-Simulator/ /root/tesla/code/Multi-Agent-Simulator
COPY models/ /root/tesla/models/
COPY worlds/ /root/tesla/worlds/

# 1-0. 라이선스 문서 — 이미지 안의 여러 파일(models/README, launch 헤더, World Info 팝업)이
#      'licenses/...' 를 가리키므로 이미지에도 함께 넣어 그 경로가 실제로 존재하게 한다.
COPY NOTICE LICENSE /root/tesla/
COPY licenses/ /root/tesla/licenses/

# 1-1. 검증된 GUI 설정(QSettings) 시드 — Nav 설정 '자동(기본)' 프로파일 포함.
#      설정을 바꿔 배포하려면: cp ~/.config/ETRI/ROSSimulator.conf docker/seed_config/ 후 커밋
RUN mkdir -p /root/.config/ETRI
COPY docker/seed_config/ROSSimulator.conf /root/.config/ETRI/ROSSimulator.conf

# 1-2. 팝업 창 올리기 (물건찾기 결과 창)
RUN apt-get install -y wmctrl

# ※ 물건찾기(분산 탐색-물건 찾기) 태스크는 Ultralytics YOLOv8 을 사용한다.
#    Ultralytics 와 그 사전학습 가중치는 **AGPL-3.0** 이라 Apache-2.0 인 이 저장소/
#    이미지에 포함하지 않는다. 그 태스크를 쓰려면 컨테이너에서 아래를 직접 실행한다:
#      pip3 install torch==2.4.1+cpu torchvision==0.19.1+cpu \
#           --index-url https://download.pytorch.org/whl/cpu
#      pip3 install ultralytics          # AGPL-3.0
#      python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"   # 가중치 내려받기
#      mv yolov8n.pt /root/yolov8n.pt
#    (설치하지 않으면 다른 태스크는 모두 정상 동작하고 물건찾기만 비활성)

# 2. Multi-Agent-Simulator-Docker 관련 패키지 설치
RUN pip install pyyaml
RUN pip3 install PySide6
RUN echo "deb http://packages.ros.org/ros/ubuntu `lsb_release -cs` main" > /etc/apt/sources.list.d/ros-latest.list
RUN apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
RUN apt update
RUN apt install -y python3-colcon-common-extensions

# 3. 추가 프로그램 필요 패키지 복사
COPY init.sh /root/tesla/
COPY xslocobot_amd64_install4.sh /root/tesla/
RUN mkdir -p /root/tesla/jnp
COPY jnp /root/tesla/jnp/
RUN mkdir -p /root/tesla/robots
COPY robots /root/tesla/robots
RUN mkdir -p /root/tesla/I2I_Simulator
COPY I2I_Simulator /root/tesla/I2I_Simulator
RUN mkdir -p /root/tesla/particle_emitter
COPY particle_emitter /root/tesla/particle_emitter

##############################################
###### 협업 태스크 런타임 (v1.9 추가) ########
##############################################
# 1. 탐사/병합 스택 — third_party 의 '수정본' 패키지 (원본 라이선스 유지: NOTICE 참조)
#    rrt_exploration(MIT, 수정) : 프런티어 검출·필터 — use_global_merged_map 등 추가
#    map_merge(BSD-3, 수정)     : 다중 로봇 지도 병합 정렬 보정본
RUN apt-get install -y python3-sklearn python3-numpy python3-opencv \
    ros-noetic-slam-toolbox ros-noetic-dwa-local-planner \
    ros-noetic-global-planner ros-noetic-topic-tools
RUN mkdir -p /root/catkin_ws_explo/src
# 원본 소스+LICENSE+수정내역(README) 을 배포 경로에도 둔다 — 수동 재빌드·표기 확인용
COPY third_party /root/tesla/third_party/
COPY third_party/rrt_exploration /root/catkin_ws_explo/src/rrt_exploration
COPY third_party/map_merge       /root/catkin_ws_explo/src/map_merge
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && cd /root/catkin_ws_explo && catkin_make -DCMAKE_BUILD_TYPE=Release"
RUN echo "source /root/catkin_ws_explo/devel/setup.bash" >> /root/.bashrc

# 2. JnP 0.8.1 워크스페이스 — 협업 태스크(릴레이·다목적 이동·충돌회피·지도제작·물건찾기)
RUN mkdir -p /root/catkin_ws_jnp081/src \
 && ln -s /opt/ros/noetic/share/catkin/cmake/toplevel.cmake /root/catkin_ws_jnp081/src/CMakeLists.txt \
 && ln -s /root/tesla/jnp/jnp_0.8.1 /root/catkin_ws_jnp081/src/jnp
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && cd /root/catkin_ws_jnp081 && catkin_make -DCMAKE_BUILD_TYPE=Release"

