# Task Description: Multi-Goal Move — carry every item to its goal; each goal has several items and each item is one round trip (home -> goal -> home)
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '다목적 이동' 의 작업 분할 계획. 그룹이 payload(goals=G:x,y:count|…)로 ITEMS 를 채운다.
# 구조: 모든 왕복(trip) 이 병렬 — 할당기(MultiGoalAllocator)가 시작 위치–goal 거리로 로봇을 배정하고, goal 점유 순서는 그룹의 진입 허가 서비스가 제어한다.

# GENERAL TASK DECOMPOSITION
# Independent subtasks: one round trip per item. Items of different goals and of the same goal can all run in parallel
# (one agent per trip; the goal's entry permit serialises arrivals), so each trip is its own thread.

# CODE
ITEMS = []   # "goal_label:x,y:item_index" per item (bound at run time)

def carry_item(item):
    # 0: one round trip home -> goal -> home with one item
    Trip(item, item)    # item = 'goal_label:x,y:item_index'

import threading
threads = []
for item in ITEMS:
    t = threading.Thread(target=carry_item, args=(item,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

# Task Multi-Goal Move is done
