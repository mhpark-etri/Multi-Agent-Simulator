#!/bin/bash
# 시뮬 시작 직후: locobot 컨트롤러가 준비되는 즉시 unpause + 팔 내림 (2026-08-08)
# 2026-08-09: 기동 과부하 레이스로 컨트롤러 스포너가 죽는 경우(transport error)
#   로봇별로 감시하고, 미기동이면 재스폰을 시도하는 자가회복 추가.
source /opt/ros/noetic/setup.bash
CTRLS="joint_state_controller waist_controller shoulder_controller elbow_controller wrist_angle_controller wrist_rotate_controller left_finger_controller right_finger_controller pan_controller tilt_controller"
# ── 스폰 자가회복: 기동 경합으로 spawn 서비스가 실패한 로봇 재스폰 (2026-08-09) ──
sleep 12
for ns in locobot_0 locobot_1 tb3_waffle_0; do
    if ! rosparam get /$ns/robot_description >/dev/null 2>&1 &&        ! rosparam list 2>/dev/null | grep -q "^/$ns/robot_description"; then
        continue    # 이 태스크에 없는 로봇
    fi
    ok=$(timeout 8 rosservice call /gazebo/get_model_state "{model_name: '$ns'}" 2>/dev/null | grep -c "success: True")
    if [ "$ok" != "1" ]; then
        sx=$(rosparam get /$ns/spawn_x 2>/dev/null || echo 0.0)
        sy=$(rosparam get /$ns/spawn_y 2>/dev/null || echo 0.0)
        echo "[$ns] 모델 부재 감지 — 재스폰 시도 ($sx,$sy)"
        timeout 60 rosrun gazebo_ros spawn_model -urdf             -param /$ns/robot_description -model $ns -x $sx -y $sy -z 0.0
        sleep 3
    fi
done
for ns in locobot_0 locobot_1; do
    ok=""
    for i in $(seq 1 45); do
        if rostopic info /$ns/tilt_controller/command 2>/dev/null | grep -A2 "Subscribers:" | grep -q "\*"; then
            ok=1; break
        fi
        sleep 2
    done
    if [ -z "$ok" ]; then
        echo "[$ns] 컨트롤러 미기동 감지 — 재스폰 시도 (기동 레이스 자가회복)"
        for try in 1 2 3; do
            timeout 90 env ROS_NAMESPACE=$ns /opt/ros/noetic/lib/controller_manager/controller_manager spawn $CTRLS && break
            echo "[$ns] 재스폰 실패 ($try/3) — 10초 후 재시도"
            sleep 10
        done
    fi
done
sleep 2
bash /root/tesla/ros/navi/sh/loco_init_all.sh
