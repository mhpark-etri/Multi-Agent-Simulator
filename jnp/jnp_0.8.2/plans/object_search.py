# Task Description: Distributed Search (Find Object) — patrol the known map with several robots in parallel and detect the target objects with the camera
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '분산 탐색-물건 찾기' 의 작업 분할 계획. 그룹이 payload(robots=…;targets=…;count=…)로 ROBOTS 를 채운다.
# 구조: 로봇별 가지 병렬 — 순찰(search) 과 탐지 서비스(가상, 상시). 병목 양보/통과 task 는 실행 중 그룹이 가지에 추가한다.

# GENERAL TASK DECOMPOSITION
# One branch per robot, all branches in parallel. In each branch the robot patrols its waypoints while the
# object detector (YOLO service) runs alongside and reports found objects.

# CODE
ROBOTS = []   # ["robot"] (bound at run time)

def search_objects(robot):
    # 0: patrol the assigned waypoints
    Patrol(robot)
    # 1: detect target objects with the camera (service, always on)
    Detect(robot)

import threading
threads = []
for robot in ROBOTS:
    t = threading.Thread(target=search_objects, args=(robot,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Task Distributed Search (Find Object) is done
