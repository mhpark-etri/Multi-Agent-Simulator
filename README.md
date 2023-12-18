<div style="text-align: left;">

# Multi-Agent-Simulator v1.0
  <img src="https://github.com/etri-clara2/Multi-Agent-Simulator/assets/147698192/302eb4a3-75df-4144-9007-56de4f4c202a" width="70%" height="70%"/>

- 가상환경에서의 멀티에이전트 학습을 위한 3D 기반 에이전트 시뮬레이터.
### 프로젝트 실행 환경
- Ubuntu 20.04.
- Docker v24.0.7 이상.
<br><br><br>

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
<br><br>

---
# 사용 방법
### 프로그램 실행
  - 터미널을 열고 아래의 명령어를 차례대로 입력.
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
