**🇰🇷 한국어** | [🇺🇸 English](README.en.md)

# Multi-Agent-Simulator v1.9
  <img src="https://github.com/user-attachments/assets/d64baddb-d154-4b10-8420-6c84a019a44e" width="70%" />

- Copyright (C) 2024-2026 ETRI. Licensed under the Apache License, Version 2.0 (see LICENSE). Third-party components and their licenses are listed in NOTICE.
- This software is a 3D simulator software for learning multi-agents in virtual environments (가상환경에서의 멀티에이전트 학습을 위한 3D 기반 에이전트 시뮬레이터).
- You can download worlds or models at the following sites. After that, you should move them to "worlds" or "models" directory.
  - https://github.com/gazebosim/gazebo-classic/tree/gazebo11/worlds
  - https://github.com/leonhartyao/gazebo_models_worlds_collection
  - https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps
  - https://github.com/osrf/gazebo_models
  - https://docs.px4.io/main/en/sim_gazebo_gz/worlds
  - https://github.com/PX4/PX4-SITL_gazebo-classic/tree/main/worlds
  - https://automaticaddison.com/useful-world-files-for-gazebo-and-ros-2-simulations/
  - https://data.nvision2.eecs.yorku.ca/3DGEMS/
  - https://github.com/eliabntt/gazebo_resources
- Any questions about our use of licensed work can be sent to dongoh@etri.re.kr

> [!NOTE]
> 위 월드·모델은 출처마다 라이선스가 다릅니다. 내려받거나 재배포하기 전에
> $\textsf{\color{red}{반드시 월드·모델 출처와 라이선스}}$ 를 확인해 주십시오.
> → [해당 절로 이동](#월드모델-출처와-라이선스)

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
sudo docker run -it --gpus all --net=host --privileged \
--ipc=host --shm-size=2g \
-e DISPLAY=$DISPLAY \
-e XDG_RUNTIME_DIR=/tmp/runtime-root \
-e QT_X11_NO_MITSHM=1 \
-e NVIDIA_VISIBLE_DEVICES=all \
-e NVIDIA_DRIVER_CAPABILITIES=all \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v $HOME/.Xauthority:/root/.Xauthority:ro \
-v /mnt/Shared:/mnt \
--name ct_mas img_mas
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

> **어디까지 해야 하나요?** (Docker 이미지를 쓰는 경우)
>
> | 절 | 내용 | 실행 |
> |---|---|---|
> | 4.1 | Interbotix 설치 | **필수** (설치 화면에서 y 입력) |
> | 4.2 | JnP 0.2.1 빌드 | **필수** |
> | 4.2.1 | JnP 0.8.1 | 불필요 — 이미지·init.sh 가 이미 빌드 |
> | 4.2.2 | 탐사 스택 | 불필요 — 이미지·init.sh 가 이미 빌드 |
> | 4.2.3 | YOLO | 선택 — 물건 찾기 태스크를 쓸 때만 |
> | 4.3 / 4.4 | Ai-Bot / Stretch2 | 해당 로봇을 쓸 때 |

### 4.1 Interbotix 설치
- 필수패키지 설치 도중 Interbotix 설치 화면이 나오면 차례대로 y를 입력.
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/871c7299-c07c-4e2d-8f92-1d1770b40e7d" width="50%" />
<br>
<br>
- 설치가 완료되면 y를 입력해 docker종료
<br>
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/f10a5d3e-70e4-4585-b752-0a818a33cc12" width="50%" />
<br><br>

### 4.2 Jnp 설치 (필수)
- 우분투 터미널에서 아래의 명령어를 입력하여 docker에 다시 접속.(ct_mas는 위에서 설치했던 docker 컨테이너 이름)
```
sudo docker start -i ct_mas
```
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/641dd3a6-f908-4120-be77-02f07c291f39" width="50%" />
<br>
<br>
- docker 접속 후에 아래의 명령어를 차례대로 입력하여 Jnp make 실행

```
cd /root/catkin_ws_jnp
catkin_make
chmod +x /root/catkin_ws_jnp/src/jnp/scripts/jnp_agent.py
```
<img src="https://github.com/mhpark-etri/Multi-Agent-Simulator/assets/147698192/e07af797-ef12-4767-a422-4c191fd1f04e" width="50%" />
<br><br>

### 4.2.1 JnP 0.8.1 (v1.9 협업 태스크) — 참고용, 실행 불필요

> 이미지와 `init.sh` 가 이미 빌드합니다. **건너뛰어도 됩니다.**
> 소스를 고쳐 다시 빌드하거나, 이미지 없이 구성할 때만 보십시오.

- v1.9 협업 태스크는 JnP **0.8.1** 을 사용합니다.
  - 릴레이 / 다목적 이동 / 충돌회피 / 분산 탐색-지도 제작 / 분산 탐색-물건 찾기
- 소스에서 다시 빌드하려면 아래를 실행합니다.

```
mkdir -p /root/catkin_ws_jnp081/src
ln -s /opt/ros/noetic/share/catkin/cmake/toplevel.cmake /root/catkin_ws_jnp081/src/CMakeLists.txt
ln -s /root/tesla/jnp/jnp_0.8.1 /root/catkin_ws_jnp081/src/jnp
cd /root/catkin_ws_jnp081 && catkin_make
```

### 4.2.2 탐사 스택 (third_party) — 참고용, 실행 불필요

> 이미지와 `init.sh` 가 이미 빌드합니다. **건너뛰어도 됩니다.**
> 소스를 고쳐 다시 빌드하거나, 이미지 없이 구성할 때만 보십시오.

**무엇을 쓰나**

- 분산 탐색(지도 제작 · 물건 찾기)에 **프런티어 검출**과 **지도 병합** 패키지를 씁니다.
- 두 패키지는 `third_party/` 에 담아 함께 배포합니다.
- 라이선스는 각 원본을 따릅니다 → `NOTICE`, `third_party/README.md`

| 패키지 | 라이선스 | 역할 | apt 패키지로 대체 |
| --- | --- | --- | --- |
| `rrt_exploration` | MIT (**수정본**) | 프런티어 검출·필터 | **불가** — `~use_global_merged_map` 등 다중 로봇용 파라미터가 추가됨 |
| `map_merge` | BSD-3-Clause (상류 **2.1.5** 원본) | 다중 로봇 지도 병합 | **불가** — apt 판(2.1.4)은 병합 지도가 어긋남 |

**이미지에서 다시 빌드할 때**

- 소스는 `/root/catkin_ws_explo/src/` 에 **이미 복사·빌드되어 있습니다.**
- 소스를 고친 뒤 아래만 실행합니다.

```
cd /root/catkin_ws_explo
catkin_make -DCMAKE_BUILD_TYPE=Release
source /root/catkin_ws_explo/devel/setup.bash
```

**이미지 없이 직접 구성할 때** (호스트에 clone 한 저장소에서)
```
mkdir -p /root/catkin_ws_explo/src
cp -a <저장소>/third_party/rrt_exploration /root/catkin_ws_explo/src/
cp -a <저장소>/third_party/map_merge       /root/catkin_ws_explo/src/
sudo apt-get install -y python3-sklearn ros-noetic-slam-toolbox \
     ros-noetic-dwa-local-planner ros-noetic-global-planner ros-noetic-topic-tools
cd /root/catkin_ws_explo && catkin_make -DCMAKE_BUILD_TYPE=Release
echo "source /root/catkin_ws_explo/devel/setup.bash" >> /root/.bashrc
```

### 4.2.3 물건 찾기(YOLO) — 선택 (해당 태스크를 쓸 때만)
- **분산 탐색-물건 찾기** 태스크만 물체 인식에 Ultralytics YOLOv8 을 사용합니다.
- Ultralytics 와 그 사전학습 가중치는 **AGPL-3.0** 이라, Apache-2.0 인 본
  저장소/이미지에는 **포함하지 않습니다.** 이 태스크를 쓰려면 컨테이너에서
  아래를 직접 설치하십시오(설치하지 않아도 나머지 태스크는 모두 동작합니다).
```
pip3 install torch==2.4.1+cpu torchvision==0.19.1+cpu \
     --index-url https://download.pytorch.org/whl/cpu
pip3 install ultralytics                       # AGPL-3.0
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"   # 가중치 내려받기
mv yolov8n.pt /root/yolov8n.pt
```
- 설치 후 GUI 의 Behavior (Action) 패널에서 **분산 탐색-물건 찾기** 를 선택해
  실행합니다. 인식 결과는 RViz 상단에 노란색으로 표시되고, 발견 순간의 YOLO
  결과(경계 상자·신뢰도)가 팝업으로 뜹니다.

### 4.3 Ai-Bot 설치
- 터미널에서 아래의 명령어를 차례대로 입력하여 Ai-Bot make 실행
```
cd /root/catkin_ws_ai_bot/
catkin_make
```
<img src="https://github.com/user-attachments/assets/66ad2411-201c-402f-ab46-c3c6c2e2a293" width="50%" />
<br><br>

### 4.4 Hello_Robot Stretch2 설치
- 터미널에서 아래의 명령어를 차례대로 입력하여 작업공간 생성 및 튜토리얼 패키지를 복사
```
cd
mkdir -p ~/catkin_ws_stretch2/src
cd ~/catkin_ws_stretch2
git clone https://github.com/hello-robot/stretch_tutorials.git
```
<img src="https://github.com/user-attachments/assets/55508fb9-d1de-4f0f-9d5d-b420cdcaf9c7" width="50%" />
<br><br>

- 초기 빌드 진행
```
catkin_make -DCATKIN_ENABLE_TESTING=OFF
```
<img src="https://github.com/user-attachments/assets/8cc461bf-375a-4a06-b191-8faa81bedf8b" width="50%" />
<br><br>

- Realsense 카메라 패키지 설치(미리 설치되어 있을 수도 있음)
```
apt-get install ros-noetic-realsense2-camera
```
<img src="https://github.com/user-attachments/assets/b8cc655d-e96d-42dc-bf99-3595b9ff82b4" width="50%" />
<br><br>

- Stretch 및 Gazebo 관련 패키지 클론
```
cd ~/catkin_ws_stretch2/src
git clone https://github.com/hello-robot/stretch_ros
git clone -b melodic-devel https://github.com/pal-robotics/realsense_gazebo_plugin
git clone https://github.com/hello-robot/stretch_tutorials.git
```
<img src="https://github.com/user-attachments/assets/2a02e079-9bb2-47dc-ae6c-e1a457d014a3" width="50%" />
<br><br>

- 의존성 설치 및 전체 패키지 빌드
```
cd ~/catkin_ws_stretch2
rosdep install --from-paths src --ignore-src -r -y
catkin_make -DCATKIN_ENABLE_TESTING=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5
```
<img src="https://github.com/user-attachments/assets/c6d20058-19f3-45be-a686-f9b9df911ce4" width="50%" />
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
    <img src="https://github.com/etri-clara2/Multi-Agent-Simulator/assets/147698192/20c1c527-a696-42d7-85f6-caea933150bc" width="70%" />
   
  - 위 그림과 같이 display 관련 에러 발생시 **Docker 터미널이 아닌 Ubuntu 터미널을 열고** 아래의 명령어 입력.
```
  xhost +
```
  - 이후 다시 프로그램 실행.
</details>
<br>

### 프로그램 사용 방법
<img src="https://github.com/user-attachments/assets/00242774-51e8-4c2f-a77e-76ed0ae89952" width="70%" />

### 1. World 선택
   - World 패널에서 실행 하려는 가상 환경 선택.
### 2. Robot 추가
   - Robot 패널에서 Add를 눌러 에이전트 생성.
### 3. 시작
   - 우측 하단 Start 버튼을 눌러 가상 환경 실행.

### 4. 협업 태스크 (v1.9)
   - Behavior (Action) 패널의 **Collaboration Tasks** 에서 태스크를 고르고 Start.
   - 제공 태스크: 릴레이 / 다목적 이동 / 충돌회피 / 분산 탐색-지도 제작 /
     분산 탐색-물건 찾기.
   - **Execution** 콤보에서 `JnP 0.8.1` 을 선택하면 에이전트들이 coalition 을
     형성해 태스크를 수행합니다.
   - **Nav 설정** 버튼: 태스크별 항법 파라미터(속도·팽창 반경·플래너 등)를
     지정합니다. 저장한 항목만 그 태스크에 적용되고, 나머지는 공통 설정 →
     기본값 순으로 적용됩니다.
   - **JnP Monitor**: coalition 구성과 task tree 를 실시간으로 표시합니다
     (제목줄 최대화 또는 F11 로 전체화면).

### 기타
  - ※ 본 프로젝트의 Image-to-Image 가상환경향상 기능을 실행하기 위해서는 모델파일(.pkl)이 필요합니다.


# 라이선스
- 본 저장소의 코드는 **Apache License 2.0** 을 따릅니다 (`LICENSE`).
- 제3자 구성요소(TurtleBot3, Interbotix, rrt_exploration, map_merge, Gazebo 모델)
  의 출처와 라이선스는 **`NOTICE`** 에 정리되어 있습니다.
- `third_party/` 의 패키지는 각 원본 라이선스(MIT / BSD-3-Clause)를 따르며,
  수정 내역은 `third_party/README.md` 에 있습니다.
- **YOLO(Ultralytics)** 는 AGPL-3.0 이며 본 저장소·이미지에 포함되지 않습니다.
  물건 찾기 태스크를 사용하는 경우 해당 구성요소에 AGPL-3.0 이 적용됩니다.


---
# 월드·모델 출처와 라이선스

> 이 절은 **월드나 모델을 내려받아 쓰거나 재배포하기 전에 읽어야 할 내용**입니다.
> 저장소에 동봉된 것과 그렇지 않은 것, 그리고 라이선스를 단정할 수 없는 것을 구분해 두었습니다.

## 이 저장소가 함께 배포하는 것

| 대상 | 출처 | 라이선스 |
| --- | --- | --- |
| `ros/navi/worlds/no_roof_small_warehouse.world` + `models/aws_robomaker_warehouse_*` (14종) | [AWS RoboMaker Small Warehouse](https://github.com/aws-robotics/aws-robomaker-small-warehouse-world) | **MIT-0** — 전문은 `licenses/aws-robomaker-small-warehouse-world-MIT-0.txt` |
| `ros/navi/worlds/` 의 나머지 월드 3종 | 이 저장소 자체 제작 (ETRI) | Apache-2.0 |
| `third_party/rrt_exploration` | [hasauino/rrt_exploration](https://github.com/hasauino/rrt_exploration) | MIT (수정본) |
| `third_party/map_merge` | [hrnr/m-explore](https://github.com/hrnr/m-explore) | BSD-3-Clause |

자세한 내용은 `NOTICE` 에 있습니다.

## AWS RoboMaker 월드 (선택 — 동봉하지 않음)

World 패널의 `Hospital › hospital`, `HouseCafe › small_house` 항목은 월드 파일이 있어야 동작합니다.
AWS RoboMaker 월드로 채울 수 있으며, 모두 **MIT-0(MIT No Attribution)** 이라 자유롭게 사용·재배포할 수 있습니다.
용량이 커서(합계 약 230 MB) 저장소에는 담지 않았습니다.

| 월드 | 저장소 | models 용량 |
| --- | --- | --- |
| hospital | https://github.com/aws-robotics/aws-robomaker-hospital-world | 76 MB |
| small house | https://github.com/aws-robotics/aws-robomaker-small-house-world | 105 MB |
| bookstore | https://github.com/aws-robotics/aws-robomaker-bookstore-world | 48 MB |

ROS 패키지로 빌드할 필요 없이 파일만 제자리에 놓으면 Gazebo 가 찾습니다.
세 저장소 모두 **기본 브랜치가 `archive` 이고 파일은 `ros1` 브랜치에 있으므로 `-b ros1` 이 반드시 필요합니다.**
(기본 브랜치를 그냥 받으면 README 만 딸려옵니다.)

```bash
# 예: hospital — 저장소 이름만 바꾸면 나머지 둘도 동일합니다
git clone --depth 1 -b ros1 \
  https://github.com/aws-robotics/aws-robomaker-hospital-world.git /tmp/aws_hospital

cp -r /tmp/aws_hospital/models/*        ~/.gazebo/models/             # 3D 모델
cp    /tmp/aws_hospital/worlds/*.world  /usr/share/gazebo-11/worlds/  # 월드 파일
```

- 컨테이너를 다시 만들어도 유지하려면 위 두 폴더 대신 이 저장소의 `models/` 와 `worlds/` 에 넣으십시오. `init.sh` 가 같은 위치로 복사해 줍니다.
- `bookstore` 는 World 패널에 항목이 없고, 추가하려면 코드 수정이 필요합니다. 패널 목록은 enum 이 아니라 `code/Multi-Agent-Simulator/main.py` 의 `InitWorld()` 가 만드는 월드 목록에서 생성됩니다. `simulator.py` 의 `ENUM_WORLD_CATEGORY_SUB` 에서 `BOOKSTORE` 주석을 해제하고 **동시에 `main.py` 목록에 `World_Sub` 항목(썸네일 포함)을 추가**해야 합니다.
- `Hospital › hospital_2_floors` / `hospital_3_floors` 를 쓰려면 파일 이름을 바꿔야 합니다. AWS 는 `hospital_two_floors.world` / `hospital_three_floors.world` 로 배포합니다.
- 협업 태스크(릴레이·다목적 이동·충돌회피·분산 탐색)는 이 월드들을 쓰지 않으므로, 받지 않아도 정상 동작합니다.

## 공개 수집처에서 받을 때 주의할 점

머리말의 다운로드 목록에 있는 사이트들입니다. **수집처의 라이선스가 그 안의 개별 파일 라이선스와 같지 않을 수 있습니다.**

- [leonhartyao/gazebo_models_worlds_collection](https://github.com/leonhartyao/gazebo_models_worlds_collection) 은 **여러 프로젝트에서 모아 놓은 수집처**입니다. 저장소 루트 LICENSE 는 GPL-3.0 이지만, 그 안의 파일들은 자기 readme 의 `Source` 절이 밝히듯 3DGEMS / RotorS / TU Delft / ARTI-Robots / Clearpath Robotics / Fetch Robotics 에서 온 것이고 **원저작물의 라이선스는 각 원출처를 따릅니다**(예: Fetch·Clearpath 는 BSD, RotorS 는 ASL 2.0, TU Delft 는 GPL-3.0). 수집처 루트가 GPL-3.0 이라는 사실과 개별 파일이 GPL 로 재라이선스되었다는 것은 다른 이야기이므로, 재배포하려면 원출처 조건을 직접 확인하십시오. **World 패널 각 항목의 원출처는 GUI 의 `World Info` 버튼으로 확인할 수 있습니다.**
- [mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps](https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps) 는 AWS 월드를 재호스팅합니다. 다만 **그 저장소에는 라이선스 파일이 하나도 없습니다**(압축 8개 전부 2,696개 항목 확인, `LICENSE`/`COPYING`/`NOTICE` 0건). MIT-0 는 귀속 표시를 요구하지 않으므로 그 자체가 위반은 아니지만, **라이선스 근거가 필요하면 AWS 저장소에서 직접 받으십시오.**
- 같은 수집처의 `office` 는 `AWS Office` 로 적혀 있으나 AWS 의 공개 저장소를 확인하지 못했고(aws-robotics 조직 저장소 43개·GitHub 검색 모두 0건), `factory` 는 `Custom Factory` 로 표기돼 있을 뿐 저작권이 그 수집처에 있다는 근거는 아닙니다. **두 월드는 원저작자와 라이선스를 단정할 수 없습니다.**
- PX4 링크 두 개는 Gazebo 세대가 다릅니다. [PX4-gazebo-models](https://github.com/PX4/PX4-gazebo-models) 는 BSD-3-Clause 이지만 **신형 Gazebo(gz)용 `.sdf`** 라 Gazebo Classic 에서는 그대로 쓸 수 없습니다. Classic 용은 [PX4-SITL_gazebo-classic](https://github.com/PX4/PX4-SITL_gazebo-classic/tree/main/worlds) 의 `.world` 19개이며, 그 저장소에는 `LICENSE` 파일이 없고 `package.xml` 이 BSD, 소스 헤더가 Apache-2.0 으로 표기돼 있습니다 — **재배포 전 직접 확인이 필요합니다.**
- [osrf/gazebo_models](https://github.com/osrf/gazebo_models) 의 저장소 수준 LICENSE 는 **CC BY 3.0** 입니다. 다만 upstream 도 일부 개별 모델의 출처·권리관계가 불명확함을 인정하고 있으므로, 개별 모델을 재배포할 때는 별도 확인이 필요합니다.
- 나머지 사이트(automaticaddison, 3DGEMS, eliabntt/gazebo_resources)는 **라이선스를 확인하지 않았습니다.** 이 저장소는 이들을 담고 있지 않습니다.
