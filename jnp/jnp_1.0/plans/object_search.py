# Task Description: Distributed Search – Find Object — robots patrol their own partition of a known map while an object detector watches each camera; done when every target class is found or all partitions are covered
# Plan Source: example — hand-written template in the LLM-TDM layout for this basic task; NOT produced by the LLM-TDM module
# (예시 계획: 기본 협업 태스크용으로 사람이 LLM-TDM 형식에 맞춰 직접 작성한 분할. LLM-TDM 모듈이 생성한 것이 아님)
# [JnP-0.9.0 2026-10-18] 기본 협업 태스크 '분산 탐색-물건 찾기' 의 작업 분할 계획. 역할 = 수색자(searcher1…) — 로봇을 지정하지 않는다.
# 그룹이 요청된 로봇 수로 SEARCHERS 를 역할 이름으로 바인딩한다.
# 구조: 모든 가지가 병렬 — 역할마다 순찰(Patrol) 가지와 탐지 서비스(Detect, 그 역할의 로봇에 붙는 상시 가상 서비스) 가지. 둘 사이에 순서는 없다.

# GENERAL TASK DECOMPOSITION
# Per searcher role, two independent activities run side by side: (a) patrol the way-points of its own partition,
# (b) a standing detection service (YOLO on the robot's camera) that reports found objects to the group.
# Nothing waits on anything else; a robot that fails to patrol does not end the mission (optional).

# CODE
import threading

SEARCHERS = []   # searcher roles, e.g. ["searcher1", "searcher2"] (bound at run time)

def patrol_area(role):
    # 0: patrol the way-points of this role's partition
    Patrol(role)

def detect_objects(role):
    # 0: standing service: detect target objects in this robot's camera images
    Detect(role)

threads = []
for role in SEARCHERS:
    t1 = threading.Thread(target=patrol_area, args=(role,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=detect_objects, args=(role,))
    t2.start()
    threads.append(t2)
for t in threads:
    t.join()

# Task Distributed Search – Find Object is done
