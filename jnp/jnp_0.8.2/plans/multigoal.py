# Task Description: Multi-Goal Move — carry a given number of items to each of several goals; every item is one round trip, items can be carried in parallel by any free robot
# [JnP-0.8.2 2026-10-13] 기본 협업 태스크 '다목적 이동' 의 작업 분할 계획. 그룹이 payload(goals=G:x,y:count|…)로 GOALS·ITEMS·GOAL_POS 를 바인딩한다.
# 구조: 병렬 — 물품 하나가 왕복(trip) 원자 task 하나, 서로 독립. 어느 로봇이 어느 물품을 옮기는지는 할당기(MultiGoalAllocator, ETA)가 정한다.

# GENERAL TASK DECOMPOSITION
# Decompose per goal and per item: one round trip per item. Trips are independent, so all run in parallel;
# the allocator assigns free robots by ETA and re-assigns robots to other goals when one goal runs out of items.

# CODE
import threading

GOALS = []      # goal names in payload order (bound at run time)
ITEMS = {}      # goal -> ["G.item1", "G.item2", ...] (bound at run time; an empty list means no item for that goal)
GOAL_POS = {}   # goal -> "x,y" (bound at run time)

def carry_item(item, goal, target):
    # 0: round trip base -> goal -> base carrying one item
    Trip(item, goal, target)

threads = []
for goal in GOALS:
    for item in ITEMS[goal]:
        t = threading.Thread(target=carry_item, args=(item, goal, GOAL_POS[goal]))
        t.start()
        threads.append(t)
for t in threads:
    t.join()

# Task Multi-Goal Move is done
