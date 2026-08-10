#!/bin/bash
# locobot 초기화 — 물리 unpause 후 팔 내림 자세를 '즉시·동시' 전송 (2026-08-08 개편)
# (기존: 명령 사이 sleep 1 이 7개 → 시작까지 ~10초 지연. 지금은 전부 병렬 발행)
rosservice call /gazebo/unpause_physics
for r in locobot_0 locobot_1; do
    rostopic pub /$r/shoulder_controller/command std_msgs/Float64 "data: -0.5" --once &
    rostopic pub /$r/elbow_controller/command    std_msgs/Float64 "data: 1.6"  --once &
    rostopic pub /$r/tilt_controller/command     std_msgs/Float64 "data: 0.0"  --once &
done
wait
# 팔이 접히는 동안 잠깐 대기 (relay 주행 시작 전 정착)
sleep 2
echo "locobot 팔 초기화 완료"
