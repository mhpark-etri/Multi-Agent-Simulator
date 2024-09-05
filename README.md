<div style="text-align: left;">

# Multi-Agent-Simulator v1.3
  <img src="https://github.com/etri-clara2/Multi-Agent-Simulator/assets/147698192/302eb4a3-75df-4144-9007-56de4f4c202a" width="70%" height="70%"/>

- Copyright (C) ETRI. All rights reserved.
- This software is a 3D simulator software for learning multi-agents in virtual environments (가상환경에서의 멀티에이전트 학습을 위한 3D 기반 에이전트 시뮬레이터).
- You can download worlds or models at the following sites. After that, you should move them to "worlds" or "models" directory.
  - https://github.com/gazebosim/gazebo-classic/tree/gazebo11/worlds
  - https://github.com/chaolmu/gazebo_models_worlds_collection
  - https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps
  - https://github.com/osrf/gazebo_models
  - https://dev.px4.io/v1.11_noredirect/en/simulation/gazebo_worlds.html
  - https://automaticaddison.com/useful-world-files-for-gazebo-and-ros-2-simulations/
  - https://data.nvision2.eecs.yorku.ca/3DGEMS/
  - https://github.com/eliabntt/gazebo_resources
- Any questions about our use of licensed work can be sent to roger618@etri.re.kr

---
# 프로젝트 실행 환경
- Ubuntu 20.04.
- Docker v24.0.7 이상.

---
# 설치 방법
### 1. 전체 프로젝트 다운로드
- Git사용을 하거나 또는 전체 프로젝트 Zip 다운로드.
### 2. Docker Image 생성
- 다운로드 받은 프로젝트안 Dockerfile이 있는 폴더에서 터미널을 열고 아래의 명령어를 입력.
```
sudo docker build --no-cache -t img_mas .
```
- 위 명령어에서 "img_mas"는 이미지 이름이므로 자유롭게 입력.
- 15 ~ 20분 정도의 시간 소요

### 3. Docker Container 생성
- 터미널을 열고 아래의 명령어를 입력.
```
sudo docker run -it --privileged --gpus all --net=host -e DISPLAY=$DISPLAY -e USER=$USER -e XDG_RUNTIME_DIR=/tmp -v /root/.Xauthority:/root/.Xauthority -v /tmp/.X11-unix:/temp/.X11 -v /mnt/Shared:/mnt --name ct_mas img_mas
```
- 위 명령어에서 "ct_mas"는 컨테이너의 이름이므로 자유롭게 입력.
- Container 생성 완료 시 컨테이너로 진입.

### 4. 필수 패키지 인스톨
- 위에서 생성 된 Container를 시작하고 아래의 명령어를 차례대로 입력.
```
cd
cd tesla
source init.sh
```

### 4.1 Interbotix 설치
- 필수패키지 설치 도중 Interbotix 설치 화면이 나오면 차례대로 y를 입력.
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/871c7299-c07c-4e2d-8f92-1d1770b40e7d" width="50%" height="50%"/>
<br>
<br>
- 설치가 완료되면 y를 입력해 docker종료
<br>
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/f10a5d3e-70e4-4585-b752-0a818a33cc12" width="50%" height="50%"/>
<br><br>

### 4.2 Jnp 설치
- 우분투 터미널에서 아래의 명령어를 입력하여 docker에 다시 접속.(ct_mas는 위에서 설치했던 docker 컨테이너 이름)
```
sudo docker start -i ct_mas
```
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/641dd3a6-f908-4120-be77-02f07c291f39" width="50%" height="50%"/>
<br><br>

- docker 접속 후에 아래의 명령어를 차례대로 입력하여 jnp make 실행
```
rm -r /root/catkin_ws_jnp/build /root/catkin_ws_jnp/devel
cd /root/catkin_ws_jnp
catkin_make
```
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/e07af797-ef12-4767-a422-4c191fd1f04e" width="50%" height="50%"/>
<br><br>

### 4.3 ketg_ai_bot_platform 설치
## 4.3.1 uni_description 설치
- 아래의 명령어를 차례대로 입력
```
rm -r /root/catkin_ws_ai_bot/build /root/catkin_ws_ai_bot/devel
cd /root/catkin_ws_ai_bot
catkin_make
```
<img src="https://github.com/user-attachments/assets/d13f42ab-88ec-4733-b78e-03302dfc3174" width="50%" height="50%"/>
<br><br>

## 4.3.2. uni_gazebo 설치
- 아래의 명령어를 차례대로 입력
```
rm -r /root/catkin_ws_ai_bot_gazebo/build /root/catkin_ws_ai_bot_gazebo/devel
cd /root/catkin_ws_ai_bot_gazebo
catkin_make
```
<img src="https://github.com/user-attachments/assets/c56bb392-e3c5-4824-9d17-8b75584a9af7" width="50%" height="50%"/>
<br><br>

---
# 사용 방법
### 프로그램 실행
  - 터미널을 열고 도커를 실행한 후 아래의 명령어를 차례대로 입력.
```
cd
cd tesla
cd code
cd Multi-Agent-Simulator
python3 main.py
```

<details>
  <summary>Display 에러 발생 시 대처 방법.</summary>
    <img src="https://github.com/etri-clara2/Multi-Agent-Simulator/assets/147698192/20c1c527-a696-42d7-85f6-caea933150bc" width="70%" height="70%"/>
   
  - 위 그림과 같이 display 관련 에러 발생시 **Docker 터미널이 아닌 Ubuntu 터미널을 열고** 아래의 명령어 입력.
```
  xhost +
```
  - 이후 다시 프로그램 실행.
</details>
<br>

### 프로그램 사용 방법
<img src="https://github.com/etri-clara2/Multi-Agent-Simulator/assets/147698192/60ad5330-c16f-46b5-9c6a-64409329adde" width="70%" height="70%"/>

### 1. World 선택
   - World 패널에서 실행 하려는 가상 환경 선택.
### 2. Robot 추가
   - Robot 패널에서 Add를 눌러 에이전트 생성.
### 3. 시작
   - 우측 하단 Start 버튼을 눌러 가상 환경 실행.

</div>
