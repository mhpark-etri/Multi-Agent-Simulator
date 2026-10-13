# Task Description: Distributed Search – Mapping — every robot explores the unknown area; one robot (the merge host) merges all maps, the others send theirs
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '분산 탐색-지도 제작' 의 작업 분할 계획. 병합 호스트(탑재 컴퓨팅 성능 순, 멤버 capability)는
# 실행 환경 정보라 그룹이 고르고(jnp_group.py 의 _compute_rank) HOST·EXPLORERS 로 바인딩한다.
# 구조: 모든 가지가 병렬 — 로봇마다 탐사(Explore) 가지와 지도 서비스(MergeMaps 또는 SendMap, 상시 가상 서비스) 가지. 둘 사이에 순서는 없다.

# GENERAL TASK DECOMPOSITION
# Per robot, two independent activities run side by side: (a) exploring frontiers until the area is covered,
# (b) a standing map service — the host merges every robot's map into /map, every other robot publishes its own map.
# Nothing waits on anything else; a robot that fails to explore does not end the mission (optional).

# CODE
import threading

HOST = []        # [robot] — the single map-merge host (bound at run time)
EXPLORERS = []   # every other robot (bound at run time)

def navigate(robot):
    # 0: explore frontiers assigned by the group's feeder until coverage is complete
    Explore(robot)

def merge_maps(robot):
    # 0: standing service on the host: merge all robots' maps into /map
    MergeMaps(robot)

def send_map(robot):
    # 0: standing service: publish this robot's map for the host
    SendMap(robot)

threads = []
for robot in HOST:
    t1 = threading.Thread(target=navigate, args=(robot,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=merge_maps, args=(robot,))
    t2.start()
    threads.append(t2)
for robot in EXPLORERS:
    t1 = threading.Thread(target=navigate, args=(robot,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=send_map, args=(robot,))
    t2.start()
    threads.append(t2)
for t in threads:
    t.join()

# Task Distributed Search – Mapping is done
