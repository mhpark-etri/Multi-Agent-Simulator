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

# -------------------- 특정 그룹 시작 위치 고정 설정 --------------------
# 고정하고 싶은 그룹 ID (0 ~ GROUP_COUNT-1 중 하나, 예: 0)
# 고정 기능을 끄고 싶으면 FIXED_GROUP_ID = None 로 설정
FIXED_GROUP_ID = 0
FIXED_X = 2.90
FIXED_Y = 0.66
# Z 는 기존 Z_FIXED 를 그대로 사용
# -------------------------------------------------------------------

# 중앙 영역 제외 조건 (x, y 모두 이 구간 밖에 있어야 함)
EXCLUDE_X_MIN, EXCLUDE_X_MAX = -4.0, 4.0
EXCLUDE_Y_MIN, EXCLUDE_Y_MAX = -4.0, 4.0

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

        # 인자 바인딩
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

        # 그룹 위치 배열 초기화
        FIRE_LOCATIONS = [None] * GROUP_COUNT

        # 4개 코너 영역 정의
        # (x < -4 또는 x > 4) AND (y < -4 또는 y > 4)
        corner_regions = [
            ("left_bottom",  X_MIN,         EXCLUDE_X_MIN, Y_MIN,         EXCLUDE_Y_MIN),  # (-5 ~ -4, -8 ~ -4)
            ("left_top",     X_MIN,         EXCLUDE_X_MIN, EXCLUDE_Y_MAX, Y_MAX),          # (-5 ~ -4,  4 ~  8)
            ("right_bottom", EXCLUDE_X_MAX, X_MAX,         Y_MIN,         EXCLUDE_Y_MIN),  # ( 4 ~  5, -8 ~ -4)
            ("right_top",    EXCLUDE_X_MAX, X_MAX,         EXCLUDE_Y_MAX, Y_MAX),          # ( 4 ~  5,  4 ~  8)
        ]

        for gid in range(GROUP_COUNT):
            # 고정 그룹이면 지정된 좌표 사용
            if FIXED_GROUP_ID is not None and gid == FIXED_GROUP_ID:
                FIRE_LOCATIONS[gid] = (FIXED_X, FIXED_Y, Z_FIXED)
                rospy.loginfo(
                    f"📍 고정 그룹 {FIXED_GROUP_ID} 원점: "
                    f"x={FIXED_X}, y={FIXED_Y}, z={Z_FIXED}"
                )
            else:
                # 4개 코너에 골고루 분배되도록 gid % 4 사용
                _, xmin, xmax, ymin, ymax = corner_regions[gid % 4]
                x = random.uniform(xmin, xmax)
                y = random.uniform(ymin, ymax)
                FIRE_LOCATIONS[gid] = (x, y, Z_FIXED)

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
        rospy.loginfo(f"📍 전체 위치 범위: X[{X_MIN}, {X_MAX}], Y[{Y_MIN}, {Y_MAX}], Z={Z_FIXED}")
        rospy.loginfo(f"🚫 중앙 제외 영역: X[{EXCLUDE_X_MIN}, {EXCLUDE_X_MAX}], Y[{EXCLUDE_Y_MIN}, {EXCLUDE_Y_MAX}]")

        for i, loc in enumerate(FIRE_LOCATIONS):
            rospy.loginfo(f"  ➜ 그룹 {i} 위치: {loc}")
            Thread(target=emitter_loop_at_location, args=(i, loc)).start()

        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("🧹 입자 방출 중단")
    except Exception as e:
        print(f"[에러] {e}")
        raise

