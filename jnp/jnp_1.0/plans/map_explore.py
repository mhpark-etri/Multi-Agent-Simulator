# Task Description: Distributed Search – Mapping — every robot explores the unknown area; one robot (the merge host) merges all maps, the others send theirs
# Plan Source: example — hand-written template in the LLM-TDM layout for this basic task; NOT produced by the LLM-TDM module
# (예시 계획: 기본 협업 태스크용으로 사람이 LLM-TDM 형식에 맞춰 직접 작성한 분할. LLM-TDM 모듈이 생성한 것이 아님)
# [JnP-0.9.0 2026-10-18] 기본 협업 태스크 '분산 탐색-지도 제작' 의 작업 분할 계획. 역할 = 병합 호스트(host) 1개 + 탐사자(explorer1…) —
# 로봇을 지정하지 않는다. 그룹이 요청된 로봇 수로 HOST·EXPLORERS 를 역할 이름으로 바인딩하고, 호스트 역할은 ROLE_PREFER 의 compute_x86
# (탑재 컴퓨팅 성능)을 가진 로봇을 우선 할당한다. 구조: 모든 가지가 병렬 — 역할마다 탐사(Explore) 가지와 지도 서비스(MergeMaps 또는
# SendMap, 그 역할의 로봇에 붙는 상시 가상 서비스) 가지. 둘 사이에 순서는 없다.

# GENERAL TASK DECOMPOSITION
# Per role, two independent activities run side by side: (a) exploring frontiers until the area is covered,
# (b) a standing map service — the host role merges every robot's map into /map, every explorer publishes its own map.
# Nothing waits on anything else; a robot that fails to explore does not end the mission (optional).

# CODE
import threading

HOST = []        # ["host"] — the single map-merge host role (bound at run time)
EXPLORERS = []   # explorer roles, e.g. ["explorer1", "explorer2"] (bound at run time)
ROLE_PREFER = {"host": ["compute_x86"]}   # the host role prefers a robot with x86-class on-board computing (map merge is heavy)

def navigate(role):
    # 0: explore frontiers assigned by the group's feeder until coverage is complete
    Explore(role)

def merge_maps(role):
    # 0: standing service on the host: merge all robots' maps into /map
    MergeMaps(role)

def send_map(role):
    # 0: standing service: publish this robot's map for the host
    SendMap(role)

threads = []
for role in HOST:
    t1 = threading.Thread(target=navigate, args=(role,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=merge_maps, args=(role,))
    t2.start()
    threads.append(t2)
for role in EXPLORERS:
    t1 = threading.Thread(target=navigate, args=(role,))
    t1.start()
    threads.append(t1)
    t2 = threading.Thread(target=send_map, args=(role,))
    t2.start()
    threads.append(t2)
for t in threads:
    t.join()

# Task Distributed Search – Mapping is done
