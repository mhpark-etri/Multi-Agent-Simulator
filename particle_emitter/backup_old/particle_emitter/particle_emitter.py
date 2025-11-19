#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import random
import time
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState
from threading import Thread
from collections import deque

"""
사용자 설정 영역
- X_MIN, X_MAX, Y_MIN, Y_MAX: 불꽃(방출 위치) 랜덤 배치 범위
- Z_FIXED: 모든 위치의 z 고정값
- SEED: 재현 가능한 랜덤 배치를 원하면 정수로 설정 (예: 42). 랜덤 매 실행마다 달라지게 하려면 None.
- VZ_MIN, VZ_MAX: 그룹별 상승 속도 범위 생성의 전체 범위(선형 분포)
"""
X_MIN, X_MAX = -5.0, 5.0
Y_MIN, Y_MAX = -8.0, 8.0
Z_FIXED = 0.1
SEED = None          # 예: 42 로 설정하면 재현 가능
VZ_MIN, VZ_MAX = 0.10, 2.80

# === 전역 설정값 ===
PARTICLE_COUNT = 300
GROUP_COUNT = 15
GROUP_SIZE = PARTICLE_COUNT // GROUP_COUNT

SPAWN_INTERVAL = 0.02
LIFESPAN = 0.5

SPREAD_SCALE = 0.3
RIPPLE_NOISE = 0.005

def build_velocity_ranges(group_count, vz_min=0.1, vz_max=2.8):
    ranges = {}
    if group_count == 1:
        ranges[0] = (vz_min, vz_max)
        return ranges

    for gid in range(group_count):
        r = float(gid) / float(group_count - 1)
        vmax = vz_min + (vz_max - vz_min) * r
        vmin = max(vz_min * 0.8, vmax * 0.5)
        ranges[gid] = (vmin, vmax)
    return ranges

def generate_fire_locations(group_count, x_min, x_max, y_min, y_max, z_fixed, seed=None):
    state = random.getstate()
    if seed is not None:
        random.seed(seed)

    locations = [
        (random.uniform(x_min, x_max), random.uniform(y_min, y_max), z_fixed)
        for _ in range(group_count)
    ]

    random.setstate(state)
    return locations

# === 동적으로 생성되는 설정 ===
FIRE_LOCATIONS = generate_fire_locations(
    GROUP_COUNT, X_MIN, X_MAX, Y_MIN, Y_MAX, Z_FIXED, seed=SEED
)
assert len(FIRE_LOCATIONS) == GROUP_COUNT, "🔥 FIRE_LOCATIONS 개수는 GROUP_COUNT와 같아야 합니다!"

VELOCITY_RANGE_BY_GROUP = build_velocity_ranges(GROUP_COUNT, VZ_MIN, VZ_MAX)

# [수정 1] 모델 이름을 1부터 시작하도록 +1 보정
particle_groups = {
    i: deque([f"particle_{i * GROUP_SIZE + j + 1}" for j in range(GROUP_SIZE)])
    for i in range(GROUP_COUNT)
}

# 노드 초기화
rospy.init_node("multi_fire_particle_emitter")

# Gazebo 서비스 준비
rospy.wait_for_service("/gazebo/set_model_state")
set_model_state = rospy.ServiceProxy("/gazebo/set_model_state", SetModelState)

def animate_particle(model_name, origin, velocity_range):
    ox, oy, oz = origin

    base_x = random.uniform(-0.01, 0.01)
    base_y = random.uniform(-0.01, 0.01)
    base_z = random.uniform(0.0, 0.1)

    velocity_z = random.uniform(*velocity_range)

    spread_x = random.choice([-1, 1]) * random.uniform(SPREAD_SCALE * 0.5, SPREAD_SCALE)
    spread_y = random.uniform(-SPREAD_SCALE, SPREAD_SCALE)

    start_time = time.time()
    rate = rospy.Rate(1000)

    msg = ModelState()
    msg.model_name = model_name
    msg.reference_frame = "world"

    while not rospy.is_shutdown():
        elapsed = time.time() - start_time
        if elapsed > LIFESPAN:
            break

        t = elapsed / LIFESPAN

        x = ox + base_x + spread_x * t + RIPPLE_NOISE * random.uniform(-1, 1)
        y = oy + base_y + spread_y * t + RIPPLE_NOISE * random.uniform(-1, 1)
        z = oz + base_z + velocity_z * elapsed

        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = z
        set_model_state(msg)

        rate.sleep()

    # 비활성화 (지하 이동)
    msg.pose.position.z = -1.0
    set_model_state(msg)

    # [수정 2] 그룹 계산 시 1부터 시작한 인덱스 보정(-1) 후 그룹 산출
    idx = int(model_name.split("_")[1]) - 1
    group_id = idx // GROUP_SIZE
    particle_groups[group_id].append(model_name)

def emitter_loop_at_location(group_id, location):
    rospy.loginfo(f"🔥 위치 {group_id}에서 입자 방출 시작... (origin={location}, vz_range={VELOCITY_RANGE_BY_GROUP[group_id]})")
    rate = rospy.Rate(1.0 / SPAWN_INTERVAL)
    threads = deque()
    velocity_range = VELOCITY_RANGE_BY_GROUP[group_id]

    while not rospy.is_shutdown():
        if particle_groups[group_id]:
            model = particle_groups[group_id].popleft()
            thread = Thread(target=animate_particle, args=(model, location, velocity_range))
            thread.start()
            threads.append(thread)

        # 종료된 스레드 정리
        while threads and not threads[0].is_alive():
            threads.popleft()

        rate.sleep()

if __name__ == "__main__":
    try:
        rospy.loginfo("🔥 랜덤 최대 높이로 타오르는 화재 입자 시작")
        rospy.loginfo(f"🎯 그룹 수: {GROUP_COUNT}, 그룹당 입자: {GROUP_SIZE}")
        rospy.loginfo(f"📍 랜덤 위치 범위: X[{X_MIN}, {X_MAX}], Y[{Y_MIN}, {Y_MAX}], Z={Z_FIXED}")
        for i, loc in enumerate(FIRE_LOCATIONS):
            Thread(target=emitter_loop_at_location, args=(i, loc)).start()
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("🧹 입자 방출 중단")

