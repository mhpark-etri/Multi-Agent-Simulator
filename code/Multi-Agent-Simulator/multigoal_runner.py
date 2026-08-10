#!/usr/bin/env python3
"""다목적 이동(물품 소진) — 기존 launch 방식 실행기 (JnP 미사용 비교 구현).

goal 마다 물품 카운터를 두고, 로봇들을 특성(시작위치-goal 거리)으로 할당해
왕복(= 물품 1개 소진)시키며, 한 goal 이 소진되면 남은 goal 로 재할당한다.
JnP 경로에서는 이 할당/재할당을 스케줄러+MultiGoalAllocator 가 담당하지만,
legacy 경로에서는 여기서 직접 구현한다 (두 방식 비교용 — 2026-08-08 지시).

사용: python3 multigoal_runner.py '<json>'
  {"goals": {"G1": [x, y, count], "G2": [x, y, count]},
   "robots": {"locobot_0": [x, y], ...}}
"""
import json
import sys
import threading
import rospy
import actionlib
import tf
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal

_lock = threading.Lock()
_entry = {}                # goal 별 진입 락 — goal 점유는 한 번에 1대
_base_xy = None            # base 존 중심 (spec['base'])
ZONE_R = 2.2               # traffic_zones 반경과 일치


def _zone_wait(name, robot, max_iter=90):
    """존 토큰 획득 시도 — 반환값 = 실제 획득 여부. 미획득이어도 주행은
    진행하되 그 존은 release 하지 않는다 (남의 토큰 반납 차단, 리뷰 #1)."""
    try:
        from std_srvs.srv import Trigger
        try:
            rospy.wait_for_service('/zone_%s/acquire' % name, timeout=1.0)
        except rospy.ROSException:
            return False
        acq = rospy.ServiceProxy('/zone_%s/acquire' % name, Trigger)
        for i in range(max_iter):
            try:
                if acq().success:
                    if i:
                        print(f"[교통] {robot}: {name} 존 진입", flush=True)
                    return True
            except rospy.ServiceException:
                return False
            if i == 0:
                print(f"[교통] {robot}: {name} 존 대기...", flush=True)
            rospy.sleep(0.5)
        print(f"[교통] {robot}: {name} 존 대기 초과 — 무-관제 진행", flush=True)
        return False
    except Exception:
        return False


def _zone_release(name):
    try:
        from std_srvs.srv import Trigger
        rospy.ServiceProxy('/zone_%s/release' % name, Trigger)()
    except Exception:
        pass


def _zones_for_leg(x1, y1, x2, y2):
    """다리가 도착하거나 '관통'하는 존들 (출발점 존은 면제 — 과직렬화 방지).
    고정 정렬 순서 획득으로 교착 불가 (리뷰 #4/#9 반영)."""
    import math

    def hit(cx, cy, rr):
        if math.hypot(x1 - cx, y1 - cy) < rr - 0.3:
            return False        # 출발 존 면제 — '진짜 존 안'(엄격 반경)일 때만
        L2 = (x2 - x1) ** 2 + (y2 - y1) ** 2 or 1.0
        t = max(0.0, min(1.0, ((cx - x1) * (x2 - x1)
                               + (cy - y1) * (y2 - y1)) / L2))
        px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        return math.hypot(cx - px, cy - py) < rr
    zs = set()
    if _base_xy and hit(_base_xy[0], _base_xy[1], ZONE_R + 0.3):
        zs.add('base')
    for g, (gx0, gy0) in _goal_pos.items():
        if hit(gx0, gy0, ZONE_R + 0.3):
            zs.add(g)
    return sorted(zs)
_completed = {}            # goal 별 왕복(복귀) 완료 수 — 표시용
_items_pub = None
_goal_pos = {}

# 로봇 속도 특성 (m/s) — '가장 빨리 갈 수 있는 goal' 판단용
def robot_speed(name):
    if 'locobot' in name:
        return 0.4
    if 'tb3' in name or 'burger' in name:
        return 0.2
    return 0.3




def drive(robot, x, y, yaw=None):
    if yaw is None:
        # yaw 미지정: 진행 방향을 향함 — 도착 후 정렬 회전 제거
        yaw = 0.0
        try:
            import math
            from nav_msgs.msg import Odometry
            o = rospy.wait_for_message('/%s/odom' % robot, Odometry, timeout=3.0)
            cx, cy = o.pose.pose.position.x, o.pose.pose.position.y
            if math.hypot(x - cx, y - cy) > 0.2:
                yaw = math.atan2(y - cy, x - cx)
        except Exception:
            pass
    client = actionlib.SimpleActionClient('/%s/move_base' % robot, MoveBaseAction)
    if not client.wait_for_server(rospy.Duration(15.0)):
        print(f"[MG] {robot}: move_base 서버 없음", flush=True)
        return False
    g = MoveBaseGoal()
    g.target_pose.header.frame_id = 'map'
    g.target_pose.header.stamp = rospy.Time.now()
    g.target_pose.pose.position.x = x
    g.target_pose.pose.position.y = y
    q = tf.transformations.quaternion_from_euler(0, 0, yaw)
    g.target_pose.pose.orientation.x = q[0]
    g.target_pose.pose.orientation.y = q[1]
    g.target_pose.pose.orientation.z = q[2]
    g.target_pose.pose.orientation.w = q[3]
    client.send_goal(g)
    client.wait_for_result()
    return client.get_state() == 3          # SUCCEEDED


def worker(robot, home, goals, remaining, my_goal, slot_idx):
    """로봇 1대의 소비 루프: 자기 그룹 goal 을 동시 왕복으로 소진.
    자기 goal 소진 후에는 남은 goal 로 재할당해 돕는다."""
    import math
    hx, hy = home
    rospy.sleep(slot_idx * 1.2)           # 출발 시차 — 베이스 동시 출발 대치 완화
    while not rospy.is_shutdown():
        with _lock:
            if all(remaining[g] <= 0 for g in goals):
                break                       # 전 goal 소진 — 종료
            gname = None
            if remaining.get(my_goal, 0) > 0:
                gname = my_goal             # 내 그룹 goal 우선
            else:
                # 재할당: 남은 물품이 있는 goal 중 ETA 가 가장 짧은 곳
                sp = robot_speed(robot)
                cands = [(g, p) for g, p in goals.items() if remaining[g] > 0]
                if cands:
                    gname, _p = min(cands, key=lambda it: (
                        ((it[1][0] - hx) ** 2 + (it[1][1] - hy) ** 2) ** 0.5 / sp))
            if gname is None:
                break
            gx, gy = goals[gname]
            remaining[gname] -= 1           # 이 왕복이 소진할 물품 예약
        shown = int(_goal_total[gname]) - _completed.get(gname, 0)
        print(f"[MG] {robot} → {gname} 왕복 시작 (남은 물품 {shown})", flush=True)
        # ① 대기점 접근 (goal 1.3m 앞 + 횡오프셋)
        dx, dy = gx - hx, gy - hy
        dd = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dd, dy / dd
        # 부채꼴 대기: goal 반경 1.7m, 로봇별 방위 ±25°/±75° (출입 직선 통로 비움)
        ang = math.atan2(-uy, -ux) + math.radians((-25, 25, -75, 75)[slot_idx % 4])
        wx, wy = gx + 1.7 * math.cos(ang), gy + 1.7 * math.sin(ang)
        zs = _zones_for_leg(hx, hy, wx, wy)
        held1 = [z for z in zs if _zone_wait(z, robot)]
        ok = drive(robot, wx, wy)
        for z in held1:
            _zone_release(z)
        if ok:
            # ② 진입 순서: goal 점유는 한 번에 1대 (다른 로봇은 대기점에서 대기)
            while not _entry[gname].acquire(blocking=False):
                print(f"[MG] {robot}: {gname} 진입 대기...", flush=True)
                rospy.sleep(2.0)
                if rospy.is_shutdown():
                    ok = False
                    break
            if ok:
                held3 = []
                try:
                    ok = drive(robot, gx, gy)      # ③ goal 도달 — 진입락이 직렬화
                    if ok:
                        # ⑤ 복귀 존을 '진입락 보유 중' 확보 — goal 점유 중
                        #    다음 로봇 진입 방지 (리뷰 #8; 대기자는 존 비보유라 교착 없음)
                        zs3 = _zones_for_leg(gx, gy, hx, hy)
                        held3 = [z for z in zs3 if _zone_wait(z, robot)]
                finally:
                    _entry[gname].release()        # ④ 다음 로봇 진입 허용
                if ok:
                    ok = drive(robot, hx, hy)      # ⑤ 복귀
                for z in held3:
                    _zone_release(z)
        if ok:
            with _lock:
                _completed[gname] = _completed.get(gname, 0) + 1
                left = int(_goal_total[gname]) - _completed[gname]
            if _items_pub:
                _items_pub.publish(f"{gname}:{left}:{_goal_pos[gname][0]:.2f},{_goal_pos[gname][1]:.2f}")
            print(f"[MG] {robot}: {gname} 왕복 완료 — 남은 물품 {left}", flush=True)
        else:
            with _lock:
                remaining[gname] += 1       # 실패 — 물품 반납 후 재시도
            print(f"[MG] {robot}: 왕복 실패 — {gname} 물품 반납", flush=True)
            rospy.sleep(3.0)
    print(f"[MG] {robot} 작업 종료", flush=True)


def main():
    if len(sys.argv) < 2:
        print("사용: multigoal_runner.py '<json>'")
        sys.exit(1)
    spec = json.loads(sys.argv[1])
    goals = {g: (float(v[0]), float(v[1])) for g, v in spec['goals'].items()}
    remaining = {g: int(v[2]) for g, v in spec['goals'].items()}
    rospy.init_node('multigoal_runner')
    global _items_pub, _goal_total
    from std_msgs.msg import String
    _items_pub = rospy.Publisher('/goal_items', String, queue_size=4, latch=True)
    _goal_total = {g: int(v[2]) for g, v in spec['goals'].items()}
    for g, v in spec['goals'].items():
        _entry[g] = threading.Lock()
        _completed[g] = 0
        _goal_pos[g] = (float(v[0]), float(v[1]))
        _items_pub.publish(f"{g}:{int(v[2])}:{float(v[0]):.2f},{float(v[1]):.2f}")

    def _republish_items(_ev):
        # latch 는 '마지막 1건'만 유지 — goal 여러 개는 주기 재발행으로 보완
        with _lock:
            for _g in _goal_pos:
                left = int(_goal_total[_g]) - _completed.get(_g, 0)
                _items_pub.publish(f"{_g}:{left}:{_goal_pos[_g][0]:.2f},{_goal_pos[_g][1]:.2f}")
    rospy.Timer(rospy.Duration(5.0), _republish_items)
    # 베이스(공동 출발지) 표시 — 로봇 시작위치 무게중심을 latch 발행
    try:
        from geometry_msgs.msg import PoseStamped
        if 'base' in spec:
            bx, by = float(spec['base'][0]), float(spec['base'][1])   # 슬롯 상수 중심
            global _base_xy
            _base_xy = (bx, by)
        else:
            bx = sum(float(v[0]) for v in spec['robots'].values()) / len(spec['robots'])
            by = sum(float(v[1]) for v in spec['robots'].values()) / len(spec['robots'])
        base_pub = rospy.Publisher('/task_base', PoseStamped, queue_size=1, latch=True)
        ps = PoseStamped()
        ps.header.frame_id = 'map'
        ps.pose.position.x = bx
        ps.pose.position.y = by
        ps.pose.orientation.w = 1.0
        rospy.sleep(0.3)
        base_pub.publish(ps)
    except Exception as e:
        print(f"[MG] base 표시 발행 실패: {e}", flush=True)
    print(f"[MG] 시작 — goals={ {g: remaining[g] for g in goals} } robots={list(spec['robots'])}",
          flush=True)
    # ── goal 배분 (JnP 분산 선택과 동일 기준의 중앙 구현) ──
    # opt=fast: 각자 가장 빨리 갈 수 있는 goal (+ 빈 goal 최소 보정)
    # opt=total: 물품 비율 정원으로 전체 시간 고려 배분
    import math
    opt = spec.get('opt', 'fast')
    homes = {r: (float(v[0]), float(v[1])) for r, v in spec['robots'].items()}
    eta = {r: {g: math.hypot(p[0] - homes[r][0], p[1] - homes[r][1]) / robot_speed(r)
               for g, p in goals.items()} for r in homes}
    agents = sorted(homes)
    assign = {}
    if opt == 'total':
        total_items = sum(remaining.values()) or 1
        caps = {g: max(1, round(len(agents) * remaining[g] / total_items)) for g in goals}
        while sum(caps.values()) > len(agents):
            caps[max(caps, key=lambda g: caps[g])] -= 1
        while sum(caps.values()) < len(agents):
            caps[min(caps, key=lambda g: caps[g])] += 1
        cnt = {g: 0 for g in goals}
        for e, a, g in sorted((eta[a][g], a, g) for a in agents for g in goals):
            if a not in assign and cnt[g] < caps[g]:
                assign[a] = g
                cnt[g] += 1
    else:
        for a in agents:
            assign[a] = min(goals, key=lambda g: eta[a][g])
        for g in sorted(goals):
            if g not in assign.values():
                donors = [a for a in agents
                          if list(assign.values()).count(assign[a]) > 1] or agents[:]
                mover = min(donors, key=lambda a: eta[a][g] - eta[a][assign[a]])
                assign[mover] = g
    print(f"[MG] 배분(opt={opt}): {assign}", flush=True)
    threads = []
    for idx, robot in enumerate(agents):
        t = threading.Thread(target=worker,
                             args=(robot, homes[robot], goals, remaining,
                                   assign[robot], idx),
                             daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print("[MG] 전체 물품 소진 — 다목적 이동 완료", flush=True)


if __name__ == '__main__':
    main()
