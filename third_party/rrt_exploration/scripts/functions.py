import math
import rospy
import tf
from numpy import array, dot
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib_msgs.msg import GoalStatusArray
from nav_msgs.srv import GetPlan
from nav_msgs.msg import Odometry, OccupancyGrid
from geometry_msgs.msg import PoseStamped, PointStamped
from numpy import floor
from numpy.linalg import norm
from numpy import inf
import numpy as np
# ________________________________________________________________________________

_DEFAULT_PLAN_SERVICE = '/move_base_node/NavfnROS/make_plan'
_PLAN_SERVICE_FALLBACKS = (
    _DEFAULT_PLAN_SERVICE,
    '/move_base_node/GlobalPlanner/make_plan',
    '/move_base_node/make_plan',
)


def _plan_service_full_name(robot_name, service_suffix):
    suffix = service_suffix if service_suffix.startswith('/') else '/' + service_suffix
    return robot_name.strip('/') + suffix


def resolve_plan_service_suffix(robot_name, timeout_sec=15.0):
    """Pick make_plan service (Navfn on LoCoBot, GlobalPlanner on Stretch)."""
    by_robot = rospy.get_param('~plan_service_by_robot', {})
    if robot_name in by_robot:
        candidates = [by_robot[robot_name]]
    else:
        default = rospy.get_param('~plan_service', _DEFAULT_PLAN_SERVICE)
        candidates = [default]
        for suffix in _PLAN_SERVICE_FALLBACKS:
            if suffix not in candidates:
                candidates.append(suffix)
    for suffix in candidates:
        full = _plan_service_full_name(robot_name, suffix)
        try:
            rospy.wait_for_service(full, timeout=timeout_sec)
            rospy.loginfo('%s: make_plan service %s', robot_name, full)
            return suffix
        except rospy.ROSException:
            rospy.logwarn(
                '%s: make_plan not available at %s (timeout %.0fs)',
                robot_name, full, timeout_sec,
            )
    raise rospy.ROSException(
        'No make_plan service for %s (tried %s)' % (robot_name, candidates),
    )


def index_of_point(mapData, Xp):
    resolution = mapData.info.resolution
    Xstartx = mapData.info.origin.position.x
    Xstarty = mapData.info.origin.position.y
    width = mapData.info.width
    Data = mapData.data
    index = int(	(floor((Xp[1]-Xstarty)/resolution) *
                  width)+(floor((Xp[0]-Xstartx)/resolution)))
    return index


def point_of_index(mapData, i):
    y = mapData.info.origin.position.y + \
        (i/mapData.info.width)*mapData.info.resolution
    x = mapData.info.origin.position.x + \
        (float(i-(int(i/mapData.info.width)*(mapData.info.width)))*mapData.info.resolution)
    return array([x, y])
# ________________________________________________________________________________


def informationGain(mapData, point, r):
    infoGain = 0.0
    index = index_of_point(mapData, point)
    r_region = int(r/mapData.info.resolution)
    init_index = index-r_region*(mapData.info.width+1)
    for n in range(0, 2*r_region+1):
        start = n*mapData.info.width+init_index
        end = start+2*r_region
        limit = ((start/mapData.info.width)+2)*mapData.info.width
        for i in range(start, end+1):
            if (i >= 0 and i < limit and i < len(mapData.data)):
                if map_cell_is_unknown(mapData.data[i]) and norm(
                    array(point) - point_of_index(mapData, i)
                ) <= r:
                    infoGain += 1.0
    return infoGain*(mapData.info.resolution**2)


def costmap_invalidates_frontier(costmap, xy, threshold=70):
    """True if a known lethal/inflated cell blocks this frontier on the costmap.

    Unknown (255) and out-of-grid are allowed — exploration targets live there.
    """
    if len(costmap.data) < 1:
        return False
    v = int(gridValue(costmap, xy, out_of_bounds=-1))
    if v < 0:
        return False
    if v == 255:
        return False
    if v >= 254:
        return True
    return v > int(threshold)


def costmap_xy_from_map_point(map_frame, map_xy, costmap, tf_listener):
    """Sample costmap at map-frame (x,y); TF only if costmap frame differs."""
    target = map_frame.strip('/')
    cframe = costmap.header.frame_id.strip('/')
    if cframe == target:
        return array([float(map_xy[0]), float(map_xy[1])])
    temppoint = PointStamped()
    temppoint.header.frame_id = target
    temppoint.header.stamp = rospy.Time(0)
    temppoint.point.x = float(map_xy[0])
    temppoint.point.y = float(map_xy[1])
    temppoint.point.z = 0.0
    tp = tf_listener.transformPoint(costmap.header.frame_id, temppoint)
    return array([tp.point.x, tp.point.y])


def map_topic_summary(map_msg, label='map'):
    if len(map_msg.data) < 1:
        return '%s: empty' % label
    res = map_msg.info.resolution
    ox = map_msg.info.origin.position.x
    oy = map_msg.info.origin.position.y
    w = map_msg.info.width * res
    h = map_msg.info.height * res
    return (
        '%s frame=%s origin=(%.2f,%.2f) size=%.1fx%.1fm'
        % (label, map_msg.header.frame_id, ox, oy, w, h)
    )


def frontier_cleared_on_all_robot_costmaps(
    global_costmaps,
    map_frame_point,
    tf_listener,
    threshold,
    target_frame,
):
    """Drop only when every robot costmap sees known cost above threshold."""
    if len(global_costmaps) < 1:
        return False
    saw_known = 0
    for cm in global_costmaps:
        if len(cm.data) < 1:
            continue
        try:
            xy = costmap_xy_from_map_point(
                target_frame, map_frame_point, cm, tf_listener,
            )
        except (
            tf.LookupException,
            tf.ConnectivityException,
            tf.ExtrapolationException,
        ):
            return False
        v = int(gridValue(cm, xy, out_of_bounds=-1))
        if v < 0 or v == 255:
            return False
        saw_known += 1
        if v <= int(threshold):
            return False
    return saw_known > 0
# ________________________________________________________________________________


def discount(mapData, assigned_pt, centroids, infoGain, r):
    index = index_of_point(mapData, assigned_pt)
    r_region = int(r/mapData.info.resolution)
    init_index = index-r_region*(mapData.info.width+1)
    for n in range(0, 2*r_region+1):
        start = n*mapData.info.width+init_index
        end = start+2*r_region
        limit = ((start/mapData.info.width)+2)*mapData.info.width
        for i in range(start, end+1):
            if (i >= 0 and i < limit and i < len(mapData.data)):
                for j in range(0, len(centroids)):
                    current_pt = centroids[j]
                    if(mapData.data[i] == -1 and norm(point_of_index(mapData, i)-current_pt) <= r and norm(point_of_index(mapData, i)-assigned_pt) <= r):
                        # this should be modified, subtract the area of a cell, not 1
                        infoGain[j] -= 1.0
    return infoGain
# ________________________________________________________________________________


def pathCost(path):
    """Approximate path length from Navfn poses (Python 3: index must be int)."""
    if len(path) < 2:
        return inf
    mid = len(path) // 2
    p1 = array([path[mid - 1].pose.position.x, path[mid - 1].pose.position.y])
    p2 = array([path[mid].pose.position.x, path[mid].pose.position.y])
    return norm(p1 - p2) * (len(path) - 1)
# ________________________________________________________________________________


def unvalid(mapData, pt):
    index = index_of_point(mapData, pt)
    r_region = 5
    init_index = index-r_region*(mapData.info.width+1)
    for n in range(0, 2*r_region+1):
        start = n*mapData.info.width+init_index
        end = start+2*r_region
        limit = ((start/mapData.info.width)+2)*mapData.info.width
        for i in range(start, end+1):
            if (i >= 0 and i < limit and i < len(mapData.data)):
                if(mapData.data[i] == 1):
                    return True
    return False
# ________________________________________________________________________________


def Nearest(V, x):
    n = inf
    i = 0
    for i in range(0, V.shape[0]):
        n1 = norm(V[i, :]-x)
        if (n1 < n):
            n = n1
            result = i
    return result

# ________________________________________________________________________________


def Nearest2(V, x):
    n = inf
    result = 0
    for i in range(0, len(V)):
        n1 = norm(V[i]-x)

        if (n1 < n):
            n = n1
    return i
# ________________________________________________________________________________


def gridValue(mapData, Xp, out_of_bounds=100):
    """Cell cost at world (x,y). OOB returns out_of_bounds (100=occupied, 255=unknown for costmaps)."""
    if len(mapData.data) < 1 or mapData.info.resolution <= 0 or mapData.info.width < 1:
        return out_of_bounds
    resolution = mapData.info.resolution
    Xstartx = mapData.info.origin.position.x
    Xstarty = mapData.info.origin.position.y
    width = mapData.info.width
    Data = mapData.data
    px = float(Xp[0])
    py = float(Xp[1])
    col = int(floor((px - Xstartx) / resolution))
    row = int(floor((py - Xstarty) / resolution))
    if col < 0 or row < 0 or col >= width:
        return out_of_bounds
    height = len(Data) // width if width else 0
    if row >= height:
        return out_of_bounds
    index = row * width + col
    if 0 <= index < len(Data):
        return Data[index]
    return out_of_bounds



def map_cell_is_occupied(v, lethal_threshold=65):
    return int(v) >= lethal_threshold


def map_cell_is_free(v, free_threshold=50):
    """OccupancyGrid: 0=free, 100=occupied; gmapping may use low values (8, 26)."""
    v = int(v)
    return 0 <= v < free_threshold


def map_cell_is_unknown(v):
    """REP-118: -1 unknown; 255 on some costmap/SLAM exports."""
    v = int(v)
    return v < 0 or v == 255


def map_known_cell_fraction(mapData):
    """Fraction of cells that are not unknown (-1 / 255). For merged-map readiness."""
    if len(mapData.data) < 1:
        return 0.0
    known = 0
    for v in mapData.data:
        vi = int(v)
        if vi >= 0 and vi != 255:
            known += 1
    return known / float(len(mapData.data))


def _neighbor_cells(mapData, point, neighbor_cells):
    res = mapData.info.resolution
    px, py = float(point[0]), float(point[1])
    for dx in range(-neighbor_cells, neighbor_cells + 1):
        for dy in range(-neighbor_cells, neighbor_cells + 1):
            if dx == 0 and dy == 0:
                continue
            yield int(gridValue(mapData, [px + dx * res, py + dy * res]))


def has_adjacent_free(mapData, point, neighbor_cells=2, free_threshold=50):
    return any(map_cell_is_free(n, free_threshold) for n in _neighbor_cells(mapData, point, neighbor_cells))


def is_map_frontier(mapData, point, neighbor_cells=2, free_threshold=50):
    """True on free|unknown border (Cartographer-friendly occupancy values)."""
    v = int(gridValue(mapData, point))
    if map_cell_is_occupied(v):
        return False
    if map_cell_is_unknown(v):
        return has_adjacent_free(mapData, point, neighbor_cells, free_threshold)
    if map_cell_is_free(v, free_threshold):
        return any(map_cell_is_unknown(n) for n in _neighbor_cells(mapData, point, neighbor_cells))
    return False


def costmap_world_bounds(costmap):
    if len(costmap.data) < 1 or costmap.info.resolution <= 0:
        return None
    res = costmap.info.resolution
    ox = costmap.info.origin.position.x
    oy = costmap.info.origin.position.y
    w = costmap.info.width * res
    h = costmap.info.height * res
    return ox, oy, ox + w, oy + h


def point_in_costmap_world(costmap, xy):
    bounds = costmap_world_bounds(costmap)
    if bounds is None:
        return False
    ox, oy, ex, ey = bounds
    px, py = float(xy[0]), float(xy[1])
    return ox <= px < ex and oy <= py < ey


def get_robot_static_map_topic(robot_name):
    """LoCoBot uses static_layer; Stretch hello_robot yaml uses static_map plugin name."""
    base = '/' + robot_name.strip('/') + '/move_base_node/global_costmap/'
    for suffix in ('static_layer/map_topic', 'static_map/map_topic'):
        key = base + suffix
        try:
            val = str(rospy.get_param(key, '')).strip()
            if val:
                return val
        except Exception:
            pass
    return ''


def _snap_xy_to_plannable_costmap(
    costmap, xy, max_cost=50, search_radius_m=1.2, prefer_unknown=False,
):
    """Move a pose off inflated cells (~99); optional bias toward unknown (frontiers)."""
    xy = array(xy, dtype=float)
    if len(costmap.data) < 1 or costmap.info.resolution <= 0:
        return xy
    v = int(gridValue(costmap, xy, out_of_bounds=255))
    if v <= max_cost:
        return xy
    res = costmap.info.resolution
    max_cells = max(1, int(float(search_radius_m) / res))
    ox = costmap.info.origin.position.x
    oy = costmap.info.origin.position.y
    sx = int(floor((xy[0] - ox) / res))
    sy = int(floor((xy[1] - oy) / res))
    best = None
    best_score = inf
    for r in range(1, max_cells + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                col, row = sx + dx, sy + dy
                candidate = array([ox + (col + 0.5) * res, oy + (row + 0.5) * res])
                c = int(gridValue(costmap, candidate, out_of_bounds=255))
                if c > max_cost:
                    continue
                d = norm(xy - candidate)
                score = d - (0.15 if prefer_unknown and c == 255 else 0.0)
                if score < best_score:
                    best_score = score
                    best = candidate
        if best is not None:
            return best
    return xy


def snap_start_to_plannable_costmap(
    costmap, start_xy, max_start_cost=50, search_radius_m=1.2,
):
    """Navfn/GlobalPlanner fail when the robot sits on inflated cells (~99)."""
    return _snap_xy_to_plannable_costmap(
        costmap, start_xy, max_cost=max_start_cost,
        search_radius_m=search_radius_m, prefer_unknown=False,
    )


def snap_goal_to_plannable_costmap(
    costmap, goal_xy, max_goal_cost=50, search_radius_m=0.75,
):
    """Frontiers on map edges often land on inflated cells (goal cost 99)."""
    return _snap_xy_to_plannable_costmap(
        costmap, goal_xy, max_cost=max_goal_cost,
        search_radius_m=search_radius_m, prefer_unknown=True,
    )


def navfn_no_plan_reason(robot_name, start_xy, end_xy, costmap=None):
    """Human-readable hint when Navfn returns an empty plan."""
    parts = []
    static_topic = get_robot_static_map_topic(robot_name)
    if static_topic and static_topic.strip('/') not in ('map', ''):
        parts.append('static_map=%s (expected /map)' % static_topic)
    cm_topic = '/' + robot_name.strip('/') + '/move_base_node/global_costmap/costmap'
    cm = costmap
    if cm is None or len(cm.data) < 1:
        try:
            cm = rospy.wait_for_message(cm_topic, OccupancyGrid, timeout=3.0)
        except rospy.ROSException:
            parts.append('no costmap on %s (is move_base running?)' % cm_topic)
            return '; '.join(parts) if parts else 'empty plan'
    bounds = costmap_world_bounds(cm)
    if bounds is not None:
        parts.append(
            'costmap [%.1f,%.1f]-[%.1f,%.1f] frame=%s'
            % (bounds[0], bounds[1], bounds[2], bounds[3], cm.header.frame_id)
        )
    start_xy = array(start_xy, dtype=float)
    end_xy = array(end_xy, dtype=float)
    if not point_in_costmap_world(cm, start_xy):
        parts.append('start (%.2f,%.2f) outside rolling costmap' % (start_xy[0], start_xy[1]))
    if not point_in_costmap_world(cm, end_xy):
        parts.append('goal (%.2f,%.2f) outside rolling costmap' % (end_xy[0], end_xy[1]))
    vs = int(gridValue(cm, start_xy, out_of_bounds=-1))
    vg = int(gridValue(cm, end_xy, out_of_bounds=-1))
    parts.append('cell_cost start=%s goal=%s' % (vs, vg))
    parts.append('dist=%.2fm' % norm(start_xy - end_xy))
    return '; '.join(parts) if parts else 'empty plan'


def costmap_rejects_exploration_goal(costmap, point, max_cost, radius_m=0.15):
    """Reject lethal/inscribed/high known cost; allow 255 (unknown) for frontiers."""
    res = costmap.info.resolution
    steps = max(1, int(radius_m / res)) if radius_m > 0 else 0
    px, py = float(point[0]), float(point[1])
    coords = [[px, py]]
    for dx in range(-steps, steps + 1):
        for dy in range(-steps, steps + 1):
            coords.append([px + dx * res, py + dy * res])
    for xy in coords:
        v = int(gridValue(costmap, xy, out_of_bounds=255))
        if v >= 254:
            return True
        if v == 255:
            continue
        if v > max_cost:
            return True
    return False


def pullback_goal_along_path(costmap, path_xy, max_cost, radius_m,
                             max_pullback_m=4.0):
    """★ pull-back(2026-07-26 사용자 승인): 경로 도달점이 벽회피 창(정사각 ±radius)에
    걸릴 때, 후보를 버리지 않고 navfn 경로를 따라 로봇 쪽으로 당기며 벽회피를
    통과하는 첫 지점을 반환한다(없으면 None). 벽에 붙은 frontier 를 '근처까지
    가는 goal'로 살리는 구제 절차 — 벽회피 원칙(코너 보호)은 그대로 유지된다."""
    if len(path_xy) < 1:
        return None
    acc = 0.0
    since_test = 1e9        # 첫 점(도달점)은 즉시 검사
    prev = array(path_xy[-1], dtype=float)
    for p in reversed(path_xy):
        cur = array(p, dtype=float)
        step = norm(cur - prev)
        acc += step
        since_test += step
        prev = cur
        if acc > max_pullback_m:
            return None
        # 성능: 경로점(2.5cm 간격)마다 창 검사(±radius, 수백 셀)를 돌리면 후보당
        # 수만 회 조회 — 0.25m 보폭으로만 검사한다(창 반경 대비 충분히 조밀).
        if since_test < 0.25:
            continue
        since_test = 0.0
        if not costmap_rejects_exploration_goal(costmap, cur, max_cost, radius_m):
            return [float(cur[0]), float(cur[1])]
    return None


def point_on_map_grid(mapData, point, margin_m=0.0):
    """False if point is outside the occupancy grid (e.g. SLAM drift)."""
    if len(mapData.data) < 1 or mapData.info.resolution <= 0:
        return True
    res = mapData.info.resolution
    ox = mapData.info.origin.position.x
    oy = mapData.info.origin.position.y
    w = mapData.info.width * res
    h = mapData.info.height * res
    px, py = float(point[0]), float(point[1])
    m = float(margin_m)
    return (ox + m) <= px <= (ox + w - m) and (oy + m) <= py <= (oy + h - m)


def exploration_goal_rejected(
    mapData,
    robot_xy,
    goal_xy,
    max_distance_m=12.0,
    map_margin_m=0.0,
):
    """Reject goals far from robot or clearly off the SLAM grid.

    Frontier centroids sit on the known/unknown border; a large inset margin
    (e.g. 0.25 m) rejects every assignable frontier while Navfn still plans.
    """
    if norm(array(robot_xy, dtype=float) - array(goal_xy, dtype=float)) > float(
        max_distance_m
    ):
        return 'too_far'
    if point_on_map_grid(mapData, goal_xy, margin_m=map_margin_m):
        return None
    if point_on_map_grid(mapData, goal_xy, margin_m=0.0):
        return None
    if is_map_frontier(mapData, goal_xy):
        return None
    v = int(gridValue(mapData, goal_xy, out_of_bounds=-1))
    if map_cell_is_unknown(v):
        return None
    return 'off_map'


def exploration_goal_rejected_bool(*args, **kwargs):
    """Backward-compatible bool API."""
    return exploration_goal_rejected(*args, **kwargs) is not None


def frontier_goal_key(point, resolution=0.25):
    """Stable dict key for frontier / goal positions."""
    return (int(round(float(point[0]) / resolution)), int(round(float(point[1]) / resolution)))


def local_plan_signature(path_poses, sample_count=5):
    """Compact signature of a local plan for churn detection."""
    if not path_poses:
        return None
    n = len(path_poses)
    if n == 1:
        idxs = [0]
    else:
        idxs = [int(i * (n - 1) / float(sample_count - 1)) for i in range(sample_count)]
    sig = []
    for i in idxs:
        p = path_poses[i].pose.position
        sig.append((round(p.x, 2), round(p.y, 2)))
    return tuple(sig)


def line_crosses_lethal(mapData, start, end, lethal_threshold=65):
    """True if straight segment hits occupied cells."""
    start = array(start, dtype=float)
    end = array(end, dtype=float)
    dist = norm(end - start)
    if dist < 1e-6 or mapData.info.resolution <= 0:
        return False
    steps = int(dist / mapData.info.resolution) + 1
    for t in np.linspace(0.0, 1.0, steps):
        p = start + t * (end - start)
        if map_cell_is_occupied(gridValue(mapData, p), lethal_threshold):
            return True
    return False


def line_cost_violates(v, max_cost=50, lethal_threshold=65):
    """True if costmap cell blocks a straight-line frontier check."""
    v = int(v)
    if v == 255:
        return False
    return v >= 254 or map_cell_is_occupied(v, lethal_threshold) or v > max_cost


def sample_line_costmap(costmap, start, end, max_cost=50, lethal_threshold=65):
    """Sample (x, y, cost, violates) along a segment on global costmap."""
    if len(costmap.data) < 1 or costmap.info.resolution <= 0:
        return []
    start = array(start, dtype=float)
    end = array(end, dtype=float)
    dist = norm(end - start)
    if dist < 1e-6:
        return []
    steps = int(dist / costmap.info.resolution) + 1
    out = []
    for t in np.linspace(0.0, 1.0, steps):
        p = start + t * (end - start)
        v = int(gridValue(costmap, p, out_of_bounds=255))
        out.append((float(p[0]), float(p[1]), v, line_cost_violates(v, max_cost, lethal_threshold)))
    return out


def line_crosses_high_cost(costmap, start, end, max_cost=50, lethal_threshold=65):
    """True if segment hits lethal or cost above max_cost (unknown 255 allowed)."""
    return any(
        s[3] for s in sample_line_costmap(costmap, start, end, max_cost, lethal_threshold)
    )


def plan_poses_to_path_xy(plan_poses):
    """Navfn/make_plan poses -> list of [x, y] in map frame."""
    out = []
    for p in plan_poses:
        out.append(array([p.pose.position.x, p.pose.position.y], dtype=float))
    return out


def sample_path_costmap(costmap, path_xy, max_cost=50, lethal_threshold=65):
    """Sample costmap along a polyline (consecutive plan poses)."""
    if len(path_xy) < 2:
        return []
    samples = []
    for i in range(len(path_xy) - 1):
        samples.extend(
            sample_line_costmap(
                costmap, path_xy[i], path_xy[i + 1], max_cost, lethal_threshold,
            )
        )
    return samples


def path_crosses_high_cost(costmap, path_xy, max_cost=50, lethal_threshold=65,
                           skip_start_m=1.2):
    """True if any segment of the planner path hits high cost on the costmap.
    ★ 출발 구간 면제(2026-07-26): 로봇이 이미 점유한/즉시 벗어날 첫 skip_start_m
    구간은 비용 검사에서 제외 — 출발지 주변 비용 때문에 모든 후보가 일괄
    거부되는 결함 방지(inflation 광폭화 후 실측)."""
    if len(path_xy) < 1:
        return False
    _sx, _sy = float(path_xy[0][0]), float(path_xy[0][1])
    for smp in sample_path_costmap(costmap, path_xy, max_cost, lethal_threshold):
        if ((smp[0] - _sx) ** 2 + (smp[1] - _sy) ** 2) ** 0.5 < skip_start_m:
            continue
        if smp[3]:
            return True
    return False


def path_crosses_unknown_outside_goal(
    costmap, path_xy, goal_xy, allow_near_goal_m=0.0,
):
    """True if Navfn path crosses unknown (255/OOB) farther than allow_near_goal_m from goal."""
    if len(costmap.data) < 1 or len(path_xy) < 1:
        return False
    goal = array(goal_xy, dtype=float)
    allow_m = max(0.0, float(allow_near_goal_m))
    if len(path_xy) == 1:
        pt = array(path_xy[0], dtype=float)
        v = int(gridValue(costmap, pt, out_of_bounds=255))
        return v == 255 and norm(pt - goal) > allow_m
    for i in range(len(path_xy) - 1):
        for x, y, v, _ in sample_line_costmap(
            costmap,
            path_xy[i],
            path_xy[i + 1],
            max_cost=999,
            lethal_threshold=999,
        ):
            if v == 255 and norm(array([x, y]) - goal) > allow_m:
                return True
    return False


def path_crosses_lethal_on_map(mapData, path_xy, lethal_threshold=65):
    """True if Navfn path crosses known occupied cells on merged /map."""
    if len(mapData.data) < 1 or len(path_xy) < 1:
        return False
    if len(path_xy) == 1:
        return map_cell_is_occupied(
            gridValue(mapData, path_xy[0]), lethal_threshold,
        )
    for i in range(len(path_xy) - 1):
        if line_crosses_lethal(
            mapData, path_xy[i], path_xy[i + 1], lethal_threshold,
        ):
            return True
    return False


def navfn_plan_passes_assigner_checks(
    costmap,
    path_xy,
    goal_xy,
    use_plan_costmap_check=True,
    use_plan_unknown_check=False,
    plan_unknown_allow_near_goal_m=1.5,
    costmap_goal_max_cost=50,
    mapData=None,
    use_plan_lethal_check=False,
    map_lethal_threshold=65,
):
    """Return (ok, reject_reason) for assigner Navfn path validation."""
    if use_plan_lethal_check and mapData is not None and len(mapData.data) > 0:
        if path_crosses_lethal_on_map(mapData, path_xy, map_lethal_threshold):
            return False, 'path_lethal_on_map'
    if use_plan_costmap_check and len(costmap.data) > 0:
        # ★ 스케일 정합(2026-07-26 실측): costmap 토픽은 0~100 스케일인데 별도
        #   치명절(65 고정)이 max_cost 상향을 무력화했다(문턱 180에도 path_high
        #   폭풍). 치명절을 max_cost 에 연동: max(65, min(99, max_cost)) —
        #   locobot(max 50)은 기존 65 유지, stretch(max 95)는 95(=inscribed 99
        #   미만 통과)로 넓은 inflation 경사와 정합.
        _lethal_eff = max(65, min(99, int(costmap_goal_max_cost)))
        if path_crosses_high_cost(costmap, path_xy, costmap_goal_max_cost,
                                  lethal_threshold=_lethal_eff):
            return False, 'path_high_cost'
    if use_plan_unknown_check and len(costmap.data) > 0:
        if path_crosses_unknown_outside_goal(
            costmap, path_xy, goal_xy, plan_unknown_allow_near_goal_m,
        ):
            return False, 'path_unknown'
    return True, None


def first_path_costmap_violation(costmap, path_xy, max_cost=50, lethal_threshold=65):
    """First (x, y, cost) on the path that violates the costmap threshold."""
    for s in sample_path_costmap(costmap, path_xy, max_cost, lethal_threshold):
        if s[3]:
            return (s[0], s[1], s[2])
    return None



def segment_local_cost_stats(costmap, start_xy, end_xy, high_cost_threshold=50):
    """Return (max_cost, mean_cost, fraction_of_samples_above_threshold) along a segment."""
    if len(costmap.data) < 1 or costmap.info.resolution <= 0:
        return 0, 0.0, 0.0
    start = array(start_xy, dtype=float)
    end = array(end_xy, dtype=float)
    dist = norm(end - start)
    if dist < 1e-6:
        v = int(gridValue(costmap, start, 255))
        if v == 255:
            return 0, 0.0, 0.0
        return v, float(v), 1.0 if v >= high_cost_threshold else 0.0
    steps = max(2, int(dist / costmap.info.resolution) + 1)
    vals = []
    for t in np.linspace(0.0, 1.0, steps):
        p = start + t * (end - start)
        v = int(gridValue(costmap, p, 255))
        if v < 255:
            vals.append(v)
    if not vals:
        return 255, 255.0, 1.0
    max_v = max(vals)
    mean_v = sum(vals) / float(len(vals))
    frac = sum(1 for v in vals if v >= high_cost_threshold) / float(len(vals))
    return max_v, mean_v, frac



def local_costmap_blocks_goal(
    tf_listener,
    map_frame,
    local_costmap,
    robot_xy,
    goal_xy,
    max_cost=65,
):
    """True if straight segment is blocked on the local costmap (TEB sees no passage)."""
    if len(local_costmap.data) < 1:
        return False
    target = local_costmap.header.frame_id
    if not target:
        return False
    try:
        rp = point_map_to_frame(tf_listener, map_frame, target, robot_xy)
        gp = point_map_to_frame(tf_listener, map_frame, target, goal_xy)
    except (
        tf.LookupException,
        tf.ConnectivityException,
        tf.ExtrapolationException,
    ):
        return False
    return line_crosses_high_cost(local_costmap, rp, gp, max_cost)


def costmap_revenue_multiplier(
    max_cost,
    mean_cost,
    frac_high,
    soft_cost=35,
    high_cost=65,
    lethal_cost=253,
    weight_max=0.55,
    weight_mean=0.25,
    weight_frac=0.20,
):
    """Scale revenue down when local/global costmap along path to goal is high."""
    if max_cost >= lethal_cost:
        return 0.02
    penalty = 0.0
    if max_cost > soft_cost:
        penalty += weight_max * min(
            1.0, (float(max_cost) - soft_cost) / max(high_cost - soft_cost, 1)
        )
    penalty += weight_mean * min(1.0, float(mean_cost) / max(float(high_cost), 1))
    penalty += weight_frac * float(frac_high)
    return max(0.02, 1.0 - min(1.0, penalty))


def point_map_to_frame(tf_listener, map_frame, target_frame, xy):
    """Transform [x,y] in map_frame into target_frame (e.g. tb3_0/odom for local costmap)."""
    ps = PointStamped()
    ps.header.frame_id = map_frame
    ps.header.stamp = rospy.Time(0)
    ps.point.x = float(xy[0])
    ps.point.y = float(xy[1])
    ps.point.z = 0.0
    out = tf_listener.transformPoint(target_frame, ps)
    return array([out.point.x, out.point.y])


def frontier_local_cost_multiplier(
    tf_listener,
    map_frame,
    costmap,
    robot_xy,
    frontier_xy,
    soft_cost=35,
    high_cost=65,
    high_cost_threshold=50,
    weight_max=0.55,
    weight_mean=0.25,
    weight_frac=0.20,
):
    """Revenue multiplier from robot->frontier segment on costmap (usually local costmap)."""
    if costmap is None or len(costmap.data) < 1:
        return 1.0
    target = costmap.header.frame_id
    if not target:
        return 1.0
    try:
        rp = point_map_to_frame(tf_listener, map_frame, target, robot_xy)
        gp = point_map_to_frame(tf_listener, map_frame, target, frontier_xy)
    except (
        tf.LookupException,
        tf.ConnectivityException,
        tf.ExtrapolationException,
    ):
        return 1.0
    max_v, mean_v, frac = segment_local_cost_stats(
        costmap, rp, gp, high_cost_threshold=high_cost_threshold
    )
    return costmap_revenue_multiplier(
        max_v,
        mean_v,
        frac,
        soft_cost=soft_cost,
        high_cost=high_cost,
        weight_max=weight_max,
        weight_mean=weight_mean,
        weight_frac=weight_frac,
    )


def _map_cell_blocks_ray(mapData, value, ignore_unknown=True):
    """Ray stop: occupied/OOB; optionally pass through unknown (-1) cells."""
    if value >= 50:
        return True
    if not ignore_unknown and value < 0:
        return True
    return False


def ray_clearance_m(mapData, origin_xy, angle_rad, max_range_m, ignore_unknown=True):
    """Distance along a ray until occupied (not unknown) or max_range."""
    if len(mapData.data) < 1 or mapData.info.resolution <= 0:
        return 0.0
    res = mapData.info.resolution
    step = res
    ox = float(origin_xy[0])
    oy = float(origin_xy[1])
    dist = step
    while dist <= max_range_m:
        x = ox + dist * math.cos(angle_rad)
        y = oy + dist * math.sin(angle_rad)
        v = gridValue(mapData, [x, y], out_of_bounds=100)
        if _map_cell_blocks_ray(mapData, v, ignore_unknown=ignore_unknown):
            return max(0.0, dist - step)
        dist += step
    return max_range_m


def wall_direction_count(mapData, point_xy, max_dist_m=0.42, num_dirs=8):
    """How many compass directions have a mapped wall within max_dist_m (corner >= 2)."""
    if len(mapData.data) < 1:
        return 0
    count = 0
    for k in range(num_dirs):
        theta = 2.0 * math.pi * float(k) / float(num_dirs)
        d = ray_clearance_m(
            mapData, point_xy, theta, max_dist_m, ignore_unknown=True
        )
        if d < max_dist_m - 0.02:
            count += 1
    return count


def max_contiguous_free_arc(num_rays, free_mask):
    """Largest contiguous block of free rays on the circle (radians)."""
    if not free_mask:
        return 0.0, 0, 0
    doubled = list(free_mask) + list(free_mask)
    best_len = 0
    best_start = 0
    run = 0
    run_start = 0
    for i, free in enumerate(doubled):
        if free:
            if run == 0:
                run_start = i
            run += 1
            if run > best_len:
                best_len = run
                best_start = run_start
        else:
            run = 0
    step = 2.0 * math.pi / float(num_rays)
    return best_len * step, best_start % num_rays, best_len


def corner_opening_angle_rad(
    mapData,
    point_xy,
    max_range_m=1.0,
    num_rays=32,
    min_clear_m=0.18,
    ignore_unknown=True,
):
    """Largest contiguous arc of directions with min_clear_m before a mapped wall."""
    free_mask = []
    for k in range(num_rays):
        theta = 2.0 * math.pi * float(k) / float(num_rays)
        dist = ray_clearance_m(
            mapData, point_xy, theta, max_range_m, ignore_unknown=ignore_unknown
        )
        free_mask.append(dist >= min_clear_m)
    arc, _, _ = max_contiguous_free_arc(num_rays, free_mask)
    return arc


def max_ray_clearance_m(mapData, point_xy, max_range_m=1.0, num_rays=32):
    """Longest mapped free ray (corridors score high; dead-end alcoves score low)."""
    best = 0.0
    for k in range(num_rays):
        theta = 2.0 * math.pi * float(k) / float(num_rays)
        best = max(
            best,
            ray_clearance_m(mapData, point_xy, theta, max_range_m, ignore_unknown=True),
        )
    return best


def is_corner_frontier(
    mapData,
    point_xy,
    hard_reject_opening_deg=140.0,
    two_wall_opening_deg=155.0,
    min_wall_directions=2,
    wall_check_dist_m=0.42,
    max_range_m=1.0,
    num_rays=32,
    min_passage_clear_m=0.55,
):
    """
    Corner = walled on 5+ of the 8 compass directions (primary), or a narrow opening.

    NOTE (2026-06-09): max_clear is still COMPUTED but DELIBERATELY NOT USED in the decision
    (kept, not deleted). Its old "corridor" guard — `if max_clear >= min_passage_clear_m:
    return False` — nullified corner detection, because every frontier has at least one open
    ray >= 0.55 m, so it always returned False. Disabled below; corner is now decided primarily
    by wall_direction_count >= 5.
    """
    if len(mapData.data) < 1:
        return False
    opening_deg = math.degrees(
        corner_opening_angle_rad(
            mapData,
            point_xy,
            max_range_m=max_range_m,
            num_rays=num_rays,
            ignore_unknown=True,
        )
    )
    walls = wall_direction_count(
        mapData, point_xy, max_dist_m=wall_check_dist_m
    )
    # max_clear: KEPT (computed) but UNUSED — the old corridor guard is disabled:
    #     if max_clear >= min_passage_clear_m:
    #         return False
    max_clear = max_ray_clearance_m(
        mapData, point_xy, max_range_m=max_range_m, num_rays=num_rays
    )
    # Primary corner test: walled on 5+ of the 8 compass directions within wall_check_dist_m.
    if walls >= 5:
        return True
    if opening_deg < hard_reject_opening_deg:
        return True
    if walls >= min_wall_directions and opening_deg < two_wall_opening_deg:
        return True
    return False


def corner_revenue_multiplier(
    mapData,
    frontier_xy,
    robot_xy=None,
    min_opening_deg=140.0,
    soft_opening_deg=200.0,
    min_mult=0.01,
    approach_into_corner_scale=0.15,
    max_range_m=1.0,
    num_rays=32,
    min_clear_m=0.18,
    hard_reject=True,
    hard_reject_opening_deg=140.0,
    two_wall_opening_deg=155.0,
    min_wall_directions=2,
    min_passage_clear_m=0.55,
):
    """Strong corner penalty; optional hard reject (returns ~0)."""
    if hard_reject and is_corner_frontier(
        mapData,
        frontier_xy,
        hard_reject_opening_deg=hard_reject_opening_deg,
        two_wall_opening_deg=two_wall_opening_deg,
        min_wall_directions=min_wall_directions,
        max_range_m=max_range_m,
        num_rays=num_rays,
        min_passage_clear_m=min_passage_clear_m,
    ):
        return 0.001

    opening_rad = corner_opening_angle_rad(
        mapData,
        frontier_xy,
        max_range_m=max_range_m,
        num_rays=num_rays,
        min_clear_m=min_clear_m,
        ignore_unknown=True,
    )
    opening_deg = math.degrees(opening_rad)
    walls = wall_direction_count(mapData, frontier_xy)

    # Exponential: narrow opening -> near-zero multiplier
    norm_open = min(1.0, opening_deg / 180.0)
    mult = max(min_mult, norm_open ** 2.5)
    if walls >= min_wall_directions:
        mult *= max(0.01, 1.0 - 0.35 * float(walls))

    if robot_xy is not None and opening_deg < soft_opening_deg:
        free_mask = []
        for k in range(num_rays):
            theta = 2.0 * math.pi * float(k) / float(num_rays)
            dist = ray_clearance_m(
                mapData, frontier_xy, theta, max_range_m, ignore_unknown=True
            )
            free_mask.append(dist >= min_clear_m)
        _, start_idx, length = max_contiguous_free_arc(num_rays, free_mask)
        if length > 0:
            center_idx = (start_idx + length / 2.0) % num_rays
            exit_angle = 2.0 * math.pi * center_idx / float(num_rays)
            ex = math.cos(exit_angle)
            ey = math.sin(exit_angle)
            fx = float(frontier_xy[0]) - float(robot_xy[0])
            fy = float(frontier_xy[1]) - float(robot_xy[1])
            dist = math.hypot(fx, fy)
            if dist > 0.15:
                dot = (fx / dist) * ex + (fy / dist) * ey
                if dot < -0.2:
                    mult *= max(0.01, approach_into_corner_scale)

    return max(0.001, min(1.0, mult))


def costmap_clearance_score(costmap, point, radius_m, max_cost=50):
    """Count of low-cost cells in a disk (higher = more open space)."""
    if len(costmap.data) < 1 or costmap.info.resolution <= 0:
        return 0
    res = costmap.info.resolution
    steps = max(1, int(float(radius_m) / res))
    px, py = float(point[0]), float(point[1])
    score = 0
    for dx in range(-steps, steps + 1):
        for dy in range(-steps, steps + 1):
            if dx * dx + dy * dy > steps * steps:
                continue
            v = int(gridValue(costmap, [px + dx * res, py + dy * res], out_of_bounds=255))
            if v == 255:
                continue
            if v <= max_cost:
                score += 1
    return score


def escape_goal_plan_ok(
    robot_obj,
    costmap,
    start_xy,
    goal_xy,
    use_plan_check,
    costmap_goal_max_cost,
):
    """Navfn plan exists and (optionally) path stays on low-cost cells."""
    try:
        plan = robot_obj.makePlan(start_xy, goal_xy, costmap=costmap)
        if len(plan) < 2:
            return False, inf
        path_xy = plan_poses_to_path_xy(plan)
        if use_plan_check and len(costmap.data) > 0:
            if path_crosses_high_cost(costmap, path_xy, costmap_goal_max_cost):
                return False, inf
        return True, pathCost(plan)
    except Exception:
        return False, inf


def find_escape_goal(
    robot_obj,
    mapData,
    costmap,
    max_distance_m=10.0,
    min_distance_m=1.0,
    sample_step_m=0.45,
    clearance_radius_m=0.7,
    costmap_goal_max_cost=50,
    goal_check_radius=0.15,
    use_costmap_check=True,
    use_plan_check=True,
    use_map_line_check=False,
    max_plan_tries=45,
    corner_cfg=None,
):
    """
    Pick a known-free map cell in open costmap space with a valid Navfn plan.
    Used when all exploration frontiers are rejected.
    Returns [x, y] or None.
    corner_cfg (optional): reject candidate cells that are dead-end corners so the
    escape goal never sends a robot to nose into a corner.
    """
    if len(mapData.data) < 1 or mapData.info.resolution <= 0:
        return None
    robot_pos = array(robot_obj.getPosition(), dtype=float)
    res = mapData.info.resolution
    width = mapData.info.width
    height = len(mapData.data) // width if width else 0
    if height < 1:
        return None
    ox = mapData.info.origin.position.x
    oy = mapData.info.origin.position.y
    step_cells = max(1, int(float(sample_step_m) / res))
    candidates = []
    for row in range(0, height, step_cells):
        for col in range(0, width, step_cells):
            idx = row * width + col
            if idx < 0 or idx >= len(mapData.data):
                continue
            if not map_cell_is_free(mapData.data[idx]):
                continue
            xy = array(
                [ox + (col + 0.5) * res, oy + (row + 0.5) * res],
                dtype=float,
            )
            if not point_on_map_grid(mapData, xy, margin_m=0.35):
                continue
            dist = norm(robot_pos - xy)
            if dist < float(min_distance_m) or dist > float(max_distance_m):
                continue
            if use_costmap_check and len(costmap.data) > 0:
                if costmap_rejects_exploration_goal(
                    costmap, xy, costmap_goal_max_cost, goal_check_radius,
                ):
                    continue
                clearance = costmap_clearance_score(
                    costmap, xy, clearance_radius_m, costmap_goal_max_cost,
                )
            else:
                clearance = 1
            if use_map_line_check and line_crosses_lethal(mapData, robot_pos, xy):
                continue
            candidates.append((clearance, dist, xy))
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c[0], -c[1]))
    corner_reject = bool(corner_cfg and corner_cfg.get('enabled', True)
                         and corner_cfg.get('hard_reject', True))
    tries = 0
    for clearance, dist, xy in candidates:
        if tries >= max_plan_tries:
            break
        tries += 1
        if corner_reject and is_corner_frontier(
            mapData, xy,
            hard_reject_opening_deg=corner_cfg.get('hard_reject_opening_deg', 140.0),
            two_wall_opening_deg=corner_cfg.get('two_wall_opening_deg', 155.0),
            min_wall_directions=int(corner_cfg.get('min_wall_directions', 2)),
            max_range_m=corner_cfg.get('max_range_m', 1.0),
            num_rays=int(corner_cfg.get('num_rays', 32)),
            min_passage_clear_m=corner_cfg.get('min_passage_clear_m', 0.55),
        ):
            continue
        if not use_plan_check:
            return [float(xy[0]), float(xy[1])]
        ok, plan_cost = escape_goal_plan_ok(
            robot_obj,
            costmap,
            robot_pos,
            xy,
            True,
            costmap_goal_max_cost,
        )
        if ok and plan_cost != inf:
            rospy.loginfo(
                'escape goal candidate ok at [%.2f, %.2f] clearance=%d dist=%.2fm plan=%.2fm',
                xy[0], xy[1], clearance, dist, plan_cost,
            )
            return [float(xy[0]), float(xy[1])]
    return None


def find_yield_goal(
    robot_obj,
    mapData,
    costmap,
    retreat_from_xy,
    max_distance_m=6.0,
    min_distance_m=0.8,
    sample_step_m=0.4,
    clearance_radius_m=0.7,
    costmap_goal_max_cost=50,
    goal_check_radius=0.15,
    use_costmap_check=True,
    use_plan_check=True,
    max_plan_tries=35,
):
    """
    Free-space goal behind the robot (away from retreat_from_xy) for corridor yield.
    Returns [x, y] or None.
    """
    if len(mapData.data) < 1 or mapData.info.resolution <= 0:
        return None
    robot_pos = array(robot_obj.getPosition(), dtype=float)
    away = robot_pos - array(retreat_from_xy, dtype=float)
    if norm(away) < 0.08:
        away = array([1.0, 0.0])
    else:
        away = away / norm(away)
    res = mapData.info.resolution
    width = mapData.info.width
    height = len(mapData.data) // width if width else 0
    if height < 1:
        return None
    ox = mapData.info.origin.position.x
    oy = mapData.info.origin.position.y
    step_cells = max(1, int(float(sample_step_m) / res))
    candidates = []
    for row in range(0, height, step_cells):
        for col in range(0, width, step_cells):
            idx = row * width + col
            if idx < 0 or idx >= len(mapData.data):
                continue
            if not map_cell_is_free(mapData.data[idx]):
                continue
            xy = array(
                [ox + (col + 0.5) * res, oy + (row + 0.5) * res],
                dtype=float,
            )
            if not point_on_map_grid(mapData, xy, margin_m=0.3):
                continue
            dist = norm(robot_pos - xy)
            if dist < float(min_distance_m) or dist > float(max_distance_m):
                continue
            step = xy - robot_pos
            if norm(step) < 0.05:
                continue
            retreat = float(dot(step / norm(step), away))
            if retreat < 0.25:
                continue
            if use_costmap_check and len(costmap.data) > 0:
                if costmap_rejects_exploration_goal(
                    costmap, xy, costmap_goal_max_cost, goal_check_radius,
                ):
                    continue
                clearance = costmap_clearance_score(
                    costmap, xy, clearance_radius_m, costmap_goal_max_cost,
                )
            else:
                clearance = 1
            candidates.append((retreat, clearance, dist, xy))
    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c[0], -c[1], c[2]))
    tries = 0
    for retreat, clearance, dist, xy in candidates:
        if tries >= max_plan_tries:
            break
        tries += 1
        if not use_plan_check:
            return [float(xy[0]), float(xy[1])]
        ok, plan_cost = escape_goal_plan_ok(
            robot_obj,
            costmap,
            robot_pos,
            xy,
            True,
            costmap_goal_max_cost,
        )
        if ok and plan_cost != inf:
            rospy.loginfo(
                'yield goal ok at [%.2f, %.2f] retreat=%.2f clearance=%d dist=%.2fm',
                xy[0], xy[1], retreat, clearance, dist,
            )
            return [float(xy[0]), float(xy[1])]
    return None
