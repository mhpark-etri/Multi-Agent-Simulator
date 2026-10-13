# Task Description: Distributed Search – Find Object — robots patrol their own partition of a known map while an object detector watches each camera; done when every target class is found or all partitions are covered
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '분산 탐색-물건 찾기' 의 작업 분할 계획. 그룹이 payload(robots=…)로 ROBOTS 를 바인딩한다.
# 구조: 모든 가지가 병렬 — 로봇마다 순찰(Patrol) 가지와 탐지 서비스(Detect, 상시 가상 서비스) 가지. 둘 사이에 순서는 없다.

# GENERAL TASK DECOMPOSITION
# Per robot, two independent activities run side by side: (a) patrol the way-points of its own partition,
# (b) a standing detection service (YOLO on the robot's camera) that reports found objects to the group.
# Nothing waits on anything else; a robot that fails to patrol does not end the mission (optional).

# CODE
import threading

ROBOTS = []   # robots taking part (bound at run time)

def patrol_area(robot):
    # 0: patrol the way-points of this robot's partition
    Patrol(robot)

def detect_objects(robot):
    # 0: standing service: detect target objects in this robot's camera images
    Detect(robot)

threads = []
for robot in ROBOTS:
    t1 = threading.Thread(target=patrol_area, args=(robot,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=detect_objects, args=(robot,))
    t2.start()
    threads.append(t2)
for t in threads:
    t.join()

# Task Distributed Search – Find Object is done
