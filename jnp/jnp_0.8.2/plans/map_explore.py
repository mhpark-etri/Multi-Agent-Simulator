# Task Description: Distributed Search (Mapping) — explore the unknown environment with several robots in parallel and merge their maps on the host robot
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '분산 탐색-지도 제작' 의 작업 분할 계획. 그룹이 payload(robots=…)와 멤버 컴퓨팅 등급으로 HOST/EXPLORERS 를 채운다.
# 구조: 로봇별 가지 병렬 — 탐색(explore) 와 지도 송신/병합(가상, 상시 서비스). 병목 양보/통과 task 는 실행 중 그룹이 가지에 추가한다.

# GENERAL TASK DECOMPOSITION
# One branch per robot, all branches in parallel. In each branch the robot explores frontiers; its map is continuously
# published (non-host) or merged (host). Exploring and map service run side by side within the branch.

# CODE
HOST = []        # ["robot"] — map-merge host (highest compute rank; bound at run time)
EXPLORERS = []   # ["robot"] — other robots (bound at run time)

def make_maps_host(robot):
    # 0: explore frontiers until the map is complete
    Explore(robot)
    # 1: merge the maps of all robots (service, always on)
    MergeMaps(robot)

def make_maps(robot):
    # 0: explore frontiers until the map is complete
    Explore(robot)
    # 1: publish own map to the host (service, always on)
    SendMap(robot)

import threading
threads = []
for robot in HOST:
    t = threading.Thread(target=make_maps_host, args=(robot,))
    threads.append(t)
    t.start()
for robot in EXPLORERS:
    t = threading.Thread(target=make_maps, args=(robot,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Task Distributed Search (Mapping) is done
