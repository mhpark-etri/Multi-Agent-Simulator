#!/bin/bash
######################################################################
# Multi-Agent-Simulator 재시작 전 정리 스크립트
#
# 사용:
#   ./stop_sim.sh        → Gazebo/ROS/JnP 스택만 정리 (GUI 창은 유지)
#   ./stop_sim.sh all    → GUI 창까지 전부 정리
#
# 배경: GUI 창만 닫으면 그 밑에서 뜬 roslaunch/gzserver/rosmaster 가
#   고아로 살아남아, 다음 실행이 그 위에 겹쳐 꼬인다(실측 2026-08-07).
# 주의:
#  - pkill 패턴의 대괄호([l] 등)는 이 스크립트/셸 자신이 패턴에
#    매칭되어 같이 죽는 것을 막기 위한 것 — 지우지 말 것.
#  - 이 스크립트를 roslaunch 등 시작 명령과 한 줄로 묶어 실행하지 말 것.
#  - gnome-terminal(에이전트 콘솔)도 닫는다. MobaXterm/ssh 셸에서 실행할 것.
######################################################################

echo "[1/3] 시뮬레이션 스택 정리 (roslaunch / Gazebo / rosmaster)"
pkill -f "ros[l]aunch"
sleep 1
pkill -9 -f "gz[s]erver"
pkill -9 -f "gz[c]lient"
pkill -f "ros[m]aster"
pkill -f "ro[s]out"
# rtabmap SLAM 잔여 DB — 남으면 재시작 후 지도/항법이 꼬일 수 있음
rm -f /root/.ros/rtabmap*.db 2>/dev/null

echo "[2/3] JnP 에이전트/그룹/모니터 tap/터미널 정리"
pkill -f "jnp_0.8.1/scripts/jnp_[a]gent"
pkill -f "jnp_0.8.1/scripts/jnp_grou[p]"
pkill -f "catkin_ws_jnp/.*jnp_[a]gent"     # 구 0.2.1 에이전트
pkill -f "jnp_mon_ta[p]"                   # JnP Monitor 창의 토픽 tap
pkill -f "loco_init_al[l]"
pkill -f "goal_label[s]"                   # relay goal 라벨 마커 노드
pkill -f "rviz -f map -d .*relay_2d[.]rviz"   # 늦게 띄운 2D RViz (rviz 실행형태만 — 넓히면 roslaunch 오살)
pkill -f "loco_ready_ini[t]"               # 자동 팔 초기화 대기 스크립트
pkill -f "relay_runne[r]"                  # 릴레이 실행 프로세스 (중단 지원)
pkill -f "multigoal_runne[r]"              # 다목적 이동 legacy 실행 프로세스
pkill -f "mutual_obstacle[s]"              # 그룹 위치공유 장애물 주입 노드
pkill -f "traffic_zone[s]"                 # 존-토큰 교통관제 노드
pkill -f "[g]nome-terminal"                # 에이전트 콘솔 창들

if [ "$1" = "all" ]; then
    echo "[3/3] GUI 창 종료"
    # 절대경로 실행(python3 /...Multi-Agent-Simulator/main.py)용
    pkill -9 -f "Multi-Agent-Simulator/main.p[y]"
    # 상대경로 실행(cd 후 python3 main.py)용 — cwd 로 판별해 정확히 GUI 만 종료.
    # ★ -9 필수: 협업 Start 를 마스터 없이 누르면 GUI 내부 rospy 가 SIGTERM
    #   핸들러를 가로채 일반 kill 이 안 듣는다 (2026-08-08 실측)
    for pid in $(pgrep -f "python3 main.p[y]"); do
        cwd=$(readlink /proc/$pid/cwd 2>/dev/null)
        case "$cwd" in
            *Multi-Agent-Simulator*) kill -9 "$pid" 2>/dev/null;;
        esac
    done
else
    echo "[3/3] GUI 창은 유지 (전부 정리하려면: $0 all)"
fi

sleep 2
LEFT=$(pgrep -af "gz[sc]|ros[m]aster|ros[l]aunch|jnp_[a]gent|test[g]roup" | head -5)
if [ -z "$LEFT" ]; then
    echo "== 정리 완료 — 남은 프로세스 없음 =="
else
    echo "== 아직 남은 프로세스: =="
    echo "$LEFT"
    echo "(한 번 더 실행하거나 kill -9 <pid>)"
fi
