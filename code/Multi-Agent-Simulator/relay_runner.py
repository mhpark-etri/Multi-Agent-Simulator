#!/usr/bin/env python3
"""연쇄 릴레이 실행 전용 프로세스 (GUI 와 분리).

GUI 프로세스 안에서 rospy 를 쓰면 마스터 재시작(Stop→Start) 후 재초기화가
불가능해 두 번째 협업 실행이 먹통이 된다 (2026-08-08 실측).
매 실행마다 이 스크립트를 새 프로세스로 돌려 rospy 를 깨끗하게 초기화한다.

사용: python3 relay_runner.py '<robots json>'
  robots json = [{"name": "locobot_0", "startX": 1.0, "startY": 4.0,
                  "moveToX": 1.0, "moveToY": -6.0}, ...]
"""
import json
import sys
from taskRelay import TaskRelay


class _Robot:
    """taskRelay 가 기대하는 필드만 담는 간이 로봇 객체."""
    pass


def main():
    if len(sys.argv) < 2:
        print("사용: relay_runner.py '<robots json>'")
        sys.exit(1)
    robots = []
    for d in json.loads(sys.argv[1]):
        r = _Robot()
        r.name = d['name']
        r.startX = d['startX']
        r.startY = d['startY']
        r.startZ = d.get('startZ', 0.0)
        r.moveToX = d['moveToX']
        r.moveToY = d['moveToY']
        r.moveToZ = d.get('moveToZ', 0.0)
        robots.append(r)
    TaskRelay().StartTask(robots)


if __name__ == '__main__':
    main()
