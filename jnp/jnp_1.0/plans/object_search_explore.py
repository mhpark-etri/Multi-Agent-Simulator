# Task Description: Distributed Search – Find Object without a prior map — every robot explores the unknown area with its own map while an object detector watches its camera; done when every target is reported or the time limit ends
# Plan Source: example — hand-written template in the LLM-TDM layout for this basic task; NOT produced by the LLM-TDM module
# (예시 계획: 기본 협업 태스크용으로 사람이 LLM-TDM 형식에 맞춰 직접 작성한 분할. LLM-TDM 모듈이 생성한 것이 아님)
# [JnP-1.0 2026-11-07] 기본 협업 태스크 '분산 탐색-물건 찾기' 의 지도 없는 변형. 역할 = 수색자(searcher1…) — 로봇을 지정하지 않는다.
# 사전 지도가 없으므로 그룹이 구역 경유점을 줄 수 없고, 각 로봇이 자기 지도의 프론티어를 고르며 찾는다(순찰 Patrol 대신 탐사 Explore).
# 그룹은 ~search_known_map:=false 일 때 이 계획(변형 'explore')을 고른다. 구조: 모든 가지가 병렬 — 역할마다 탐사 가지와 탐지 서비스
# (Detect, 그 역할의 로봇에 붙는 상시 가상 서비스) 가지. 둘 사이에 순서는 없다. 합친 지도 제출은 없다.

# GENERAL TASK DECOMPOSITION
# Per searcher role, two independent activities run side by side: (a) explore the frontiers of its own map until the target is reported,
# (b) a standing detection service (YOLO on the robot's camera) that reports found objects to the group.
# Nothing waits on anything else; a robot that fails to explore does not end the mission (optional).

# CODE
import threading

SEARCHERS = []   # searcher roles, e.g. ["searcher1", "searcher2"] (bound at run time)

def explore_area(role):
    # 0: explore the frontiers of this role's own map (no prior map, no partition)
    Explore(role)

def detect_objects(role):
    # 0: standing service: detect target objects in this robot's camera images
    Detect(role)

threads = []
for role in SEARCHERS:
    t1 = threading.Thread(target=explore_area, args=(role,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=detect_objects, args=(role,))
    t2.start()
    threads.append(t2)
for t in threads:
    t.join()

# Task Distributed Search – Find Object without a prior map is done
