#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import random
import time
import argparse
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState
from threading import Thread
from collections import deque

"""
사용자 설정 영역 (고정 또는 필요 시 인자화 가능)
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

# 스폰/수명 등 타이밍 파라미터(고정)
SPAWN_INTERVAL = 0.02
LIFESPAN = 0.5

# 전역으로 사용할 가변 파라미터(인자에서 채움)
PARTICLE_COUNT = None
GROUP_COUNT = None
GROUP_SIZE = None
SPREAD_SCALE = None

RIPPLE_NOISE = 0.005

# 런타임에 main에서 할당될 전역 레퍼런스(ROS 서비스 및 동적 구성)
set_model_state = None
VELOCITY_RANGE_BY_GROUP = None
particle_groups = None
FIRE_LOCATIONS = None

def parse_args():
    p = argparse.ArgumentParser(description="Gazebo 다중 화재 입자 방출기")
    p.add_argument("--particle-count", "-p", type=int, required=True,
                   help="전체 입자 개수 (예: 300)")
    p.add_argument("--group-count", "-g", type=int, required=True,
                   help="그룹 개수 (예: 15) — 균등 분할 가정")
    p.add_argument("--spread-scale", "-s", type=float, required=True,
                   help="수평 확산 스케일 (예: 0.3)")
    return p.parse_args()

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

def animate_particle(model_name, origin, velocity_range):
    # 전역 읽기(할당 안 하므로 global 키워드 불필요)
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

    # 그룹 복귀
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
        args = parse_args()

        # 인자 바인딩 (최상위 레벨에서는 global 키워드가 필요/허용되지 않습니다)
        PARTICLE_COUNT = args.particle_count
        GROUP_COUNT = args.group_count
        SPREAD_SCALE = args.spread_scale

        # 입력 검증
        if GROUP_COUNT <= 0 or PARTICLE_COUNT <= 0:
            raise ValueError("PARTICLE_COUNT와 GROUP_COUNT는 양의 정수여야 합니다.")
        if PARTICLE_COUNT % GROUP_COUNT != 0:
            raise ValueError("균등 분할 가정에 따라 PARTICLE_COUNT는 GROUP_COUNT로 나누어떨어져야 합니다. "
                             f"(예: 300과 15) 현재: {PARTICLE_COUNT} % {GROUP_COUNT} = {PARTICLE_COUNT % GROUP_COUNT}")
        if SPREAD_SCALE < 0.0:
            raise ValueError("SPREAD_SCALE은 0 이상이어야 합니다.")

        GROUP_SIZE = PARTICLE_COUNT // GROUP_COUNT

        # 동적 설정 생성
        FIRE_LOCATIONS = generate_fire_locations(
            GROUP_COUNT, X_MIN, X_MAX, Y_MIN, Y_MAX, Z_FIXED, seed=SEED
        )
        assert len(FIRE_LOCATIONS) == GROUP_COUNT, "🔥 FIRE_LOCATIONS 개수는 GROUP_COUNT와 같아야 합니다!"
        VELOCITY_RANGE_BY_GROUP = build_velocity_ranges(GROUP_COUNT, VZ_MIN, VZ_MAX)

        # 모델 이름을 1부터 시작
        particle_groups = {
            i: deque([f"particle_{i * GROUP_SIZE + j + 1}" for j in range(GROUP_SIZE)])
            for i in range(GROUP_COUNT)
        }

        # ROS 준비
        rospy.init_node("multi_fire_particle_emitter")
        rospy.wait_for_service("/gazebo/set_model_state")
        set_model_state = rospy.ServiceProxy("/gazebo/set_model_state", SetModelState)

        rospy.loginfo("🔥 랜덤 최대 높이로 타오르는 화재 입자 시작")
        rospy.loginfo(f"🎯 그룹 수: {GROUP_COUNT}, 그룹당 입자: {GROUP_SIZE} (총 {PARTICLE_COUNT})")
        rospy.loginfo(f"🌊 스프레드 스케일: {SPREAD_SCALE}")
        rospy.loginfo(f"📍 랜덤 위치 범위: X[{X_MIN}, {X_MAX}], Y[{Y_MIN}, {Y_MAX}], Z={Z_FIXED}")

        for i, loc in enumerate(FIRE_LOCATIONS):
            Thread(target=emitter_loop_at_location, args=(i, loc)).start()

        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("🧹 입자 방출 중단")
    except Exception as e:
        # 초기화 단계 오류(인자/검증 등)
        print(f"[에러] {e}")
        raise

