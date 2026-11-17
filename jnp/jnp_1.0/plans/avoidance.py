# Task Description: Collision Avoidance — every robot crosses a bottleneck to its own target without blocking the passage; robots pass one at a time in ETA order
# Plan Source: example — hand-written template in the LLM-TDM layout for this basic task; NOT produced by the LLM-TDM module
# (예시 계획: 기본 협업 태스크용으로 사람이 LLM-TDM 형식에 맞춰 직접 작성한 분할. LLM-TDM 모듈이 생성한 것이 아님)
# [JnP-0.9.0 2026-10-18] 기본 협업 태스크 '충돌회피' 의 작업 분할 계획. 경로(route) 하나가 역할 하나다 — 로봇을 지정하지 않는다.
# 통과 순서(ETA = 시작점-병목 거리 ÷ 로봇 속도)는 실행 환경 정보라 계획 밖에서 계산한다(jnp_plan 이 payload 의 bt·routes 와 속도 함수로
# FIRST·REST·PREV·TARGETS 를 경로 역할 이름으로 바인딩). 구조: 역할별 병렬 가지; 첫 역할은 바로 이동, 나머지는 앞 역할의 로봇이
# 통과하기를 기다린 뒤(가상 task, 그룹 관찰자가 완료 처리) 이동.

# GENERAL TASK DECOMPOSITION
# One branch per route role, all branches in parallel. The first role (shortest ETA) drives straight to its target.
# Every later role first waits until the robot of the role before it has actually passed the bottleneck (a virtual step the group
# completes from position observation), then drives to its target. Robots wait where they are, so the passage is never blocked.

# CODE
import threading

FIRST = []      # [route] — the route role that crosses first (bound at run time)
REST = []       # route roles that cross after it, in crossing order (bound at run time)
TARGETS = {}    # route -> "tx,ty" (bound at run time)
PREV = {}       # route -> the route role that crosses just before it (bound at run time)

def cross_first(route):
    # 0: drive to the target through the bottleneck
    GoTo(route, TARGETS[route])

def cross_after(route):
    # 0: wait until the robot of the previous route has passed the bottleneck (virtual: completed by the group's observer)
    WaitPass(route, PREV[route])
    # 1: then drive to the target
    GoTo(route, TARGETS[route])

threads = []
for route in FIRST:
    t = threading.Thread(target=cross_first, args=(route,))
    t.start()
    threads.append(t)
for route in REST:
    t = threading.Thread(target=cross_after, args=(route,))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

# Task Collision Avoidance is done
