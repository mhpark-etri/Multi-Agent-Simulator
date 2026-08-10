#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --------Include modules---------------
from copy import copy
import rospy
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PointStamped
import tf
from numpy import array, vstack, delete
import numpy as _np_sf
from functions import (
    gridValue,
    informationGain,
    is_corner_frontier,
    frontier_cleared_on_all_robot_costmaps,
    costmap_invalidates_frontier,
    costmap_xy_from_map_point,
    map_topic_summary,
    point_on_map_grid,
)
from sklearn.cluster import MeanShift
from rrt_exploration.msg import PointArray

# Subscribers' callbacks------------------------------
mapData      = OccupancyGrid()
frontiers    = []
globalmaps   = []


def _resolve_robot_topic(robot_ns, topic):
    """Build /robot_ns/... without locobot_0map-style concatenation bugs."""
    robot_ns = robot_ns.strip('/')
    topic = topic.strip()
    if not topic:
        return '/' + robot_ns + '/map'
    if topic.startswith('/'):
        parts = [p for p in topic.split('/') if p]
        if parts and parts[0] == robot_ns:
            return '/' + '/'.join(parts)
        return '/' + robot_ns + topic
    return '/' + robot_ns + '/' + topic


def _normalize_frame(frame):
    return frame.strip('/')


def callBack(data, args):
    global frontiers
    tfLisn, target_frame = args
    target_frame = _normalize_frame(target_frame)
    src_frame = _normalize_frame(data.header.frame_id)
    try:
        if src_frame == target_frame:
            pt = data.point
        else:
            pt = tfLisn.transformPoint(target_frame, data).point
    except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException) as exc:
        rospy.logwarn_throttle(
            5.0,
            'filter: TF %s -> %s failed: %s',
            data.header.frame_id,
            target_frame,
            exc,
        )
        return
    x = array([pt.x, pt.y])
    if len(mapData.data) > 0 and not point_on_map_grid(mapData, x, margin_m=0.0):
        rospy.logwarn_throttle(
            8.0,
            'filter: dropped detected point (%.2f,%.2f) outside merged map grid '
            '(src frame %s) — check map_merge TF',
            x[0], x[1], data.header.frame_id,
        )
        return
    if len(frontiers) > 0:
        frontiers = vstack((frontiers, x))
    else:
        frontiers = array([x])


def mapCallBack(data):
    global mapData
    mapData = data


# def globalMap(data):
#     global global1, globalmaps, litraIndx, namespace_init_count, n_robots
#     global1 = data
#     if n_robots > 1:
#         indx = int(data._connection_header['topic']
#                    [litraIndx])-namespace_init_count
#     elif n_robots == 1:
#         indx = 0
#     globalmaps[indx] = data

def globalCostMapCallBack(data):
    global globalmaps, robot_namelist
    # search the topic based on the robot name arrangement suplied by the user
    topic_breakdownlist = str(data._connection_header['topic']).split('/')
    for ia in range(0, len(robot_namelist)):
        if robot_namelist[ia] in topic_breakdownlist:
            indx = ia
    globalmaps[indx] = data

# Node----------------------------------------------


def node():
    global frontiers, mapData, globalmaps, robot_namelist
    rospy.init_node('filter', anonymous=False)

    # fetching all parameters
    map_topic               = rospy.get_param('~map_topic', '/map')
    threshold               = rospy.get_param('~costmap_clearing_threshold', 70)
    # this can be smaller than the laser scanner range, >> smaller >>less computation time>> too small is not good, info gain won't be accurate
    info_radius             = rospy.get_param('~info_radius', 1.0)
    goals_topic             = rospy.get_param('~goals_topic', '/detected_points')
    robot_namelist          = rospy.get_param('~robot_namelist', 'robot1')
    bandwith_cluster        = rospy.get_param('~bandwith_cluster', 0.3)
    snap_to_free            = rospy.get_param('~snap_to_free', False)  # ★ baseline v2 (2026-07-27)
    rateHz                  = rospy.get_param('~rate', 100)
    global_costmap_topic    = rospy.get_param('~global_costmap_topic', '/move_base_node/global_costmap/costmap')
    robot_frame             = rospy.get_param('~robot_frame', 'base_link')
    map_frame               = rospy.get_param('~map_frame', 'map')
    min_info_gain_keep      = rospy.get_param('~min_info_gain_keep', 0.05)
    use_global_merged_map     = rospy.get_param('~use_global_merged_map', False)
    reject_corner_frontiers = rospy.get_param('~reject_corner_frontiers', True)
    corner_hard_reject_opening_deg = float(
        rospy.get_param('~corner_hard_reject_opening_deg', 155.0))
    corner_two_wall_opening_deg = float(
        rospy.get_param('~corner_two_wall_opening_deg', 168.0))
    corner_min_wall_directions = int(rospy.get_param('~corner_min_wall_directions', 2))
    corner_min_passage_clear_m = float(rospy.get_param('~corner_min_passage_clear_m', 0.55))
    costmap_clearing_mode = rospy.get_param('~costmap_clearing_mode', 'all_robots')

    rate = rospy.Rate(rateHz)
# -------------------------------------------

    robot_namelist = robot_namelist.split(',')

# ---------------------------------------------------------------------------------------------------------------
    map_subs = []
    if use_global_merged_map:
        merged_map = map_topic if map_topic.startswith('/') else '/' + map_topic
        map_subs.append(merged_map)
        rospy.loginfo('filter: subscribe merged map %s', merged_map)
        rospy.Subscriber(merged_map, OccupancyGrid, mapCallBack)
    else:
        for i in range(0, len(robot_namelist)):
            map_sub = _resolve_robot_topic(robot_namelist[i], map_topic)
            map_subs.append(map_sub)
            rospy.loginfo('filter: subscribe map %s', map_sub)
            rospy.Subscriber(map_sub, OccupancyGrid, mapCallBack)
# ---------------------------------------------------------------------------------------------------------------
    for i in range(0, len(robot_namelist)):
        globalmaps.append(OccupancyGrid())

    costmap_subs = []
    for i in range(0, len(robot_namelist)):
        costmap_sub = _resolve_robot_topic(robot_namelist[i], global_costmap_topic)
        costmap_subs.append(costmap_sub)
        rospy.loginfo('filter: subscribe global costmap %s', costmap_sub)
        rospy.Subscriber(costmap_sub, OccupancyGrid, globalCostMapCallBack)
#---------------------------------------------------------------------------------------------------------------
# wait if map is not received yet
    map_wait = map_subs[0] if map_subs else _resolve_robot_topic(robot_namelist[0], map_topic)
    wait_start = rospy.get_time()
    last_log = wait_start
    while len(mapData.data) < 1:
        elapsed = rospy.get_time() - wait_start
        if elapsed - last_log > 10.0:
            rospy.logwarn(
                'filter: waiting for OccupancyGrid on %s (%.0fs). '
                'Check: T1 gmapping running? rostopic hz %s',
                map_wait, elapsed, map_wait,
            )
            last_log = elapsed
        rospy.sleep(0.1)
# wait if any of robots' global costmap map is not received yet
    for i in range(0, len(robot_namelist)):
        while (len(globalmaps[i].data) < 1):
            rospy.loginfo('Waiting for the global costmap')
            rospy.sleep(0.1)
            pass

    merged_frame = _normalize_frame(
        mapData.header.frame_id if len(mapData.data) > 0 else map_frame,
    )
    if merged_frame != _normalize_frame(map_frame):
        rospy.logwarn(
            'filter: /map frame_id=%s but map_frame param=%s — using %s for TF',
            merged_frame, map_frame, merged_frame,
        )
    target_frame = merged_frame
#---------------------------------------------------------------------------------------------------------------  
    try:
        tfLisn = tf.TransformListener()
    except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
        rospy.sleep(0.1)
        pass
    rospy.loginfo('Waiting for TF Transformer')
    for i in range(0, len(robot_namelist)):
        child_frame = robot_namelist[i].strip('/') + '/' + robot_frame.strip('/')
        rospy.loginfo('Transforming %s -> %s', child_frame, target_frame)
        tfLisn.waitForTransform(
            target_frame,
            child_frame,
            rospy.Time(0),
            rospy.Duration(30.0),
        )

#---------------------------------------------------------------------------------------------------------------
    rospy.Subscriber(goals_topic, PointStamped, callback=callBack,
                     callback_args=[tfLisn, target_frame])
    pub = rospy.Publisher('frontiers', Marker, queue_size=10)
    pub2 = rospy.Publisher('centroids', Marker, queue_size=10)
    pub2_raw = rospy.Publisher('centroids_raw', Marker, queue_size=10)
    filterpub = rospy.Publisher(
        '/filtered_points', PointArray, queue_size=10, latch=True,
    )
    filtered_marker_pub = rospy.Publisher(
        'filtered_points_marker', Marker, queue_size=10)

    rospy.loginfo('filter: the map and global costmaps are received')
    rospy.loginfo('filter: %s', map_topic_summary(mapData, 'merged map'))
    rospy.loginfo(
        'filter: all markers/centroids/filtered_points use map_frame=%s',
        map_frame,
    )
    for i, name in enumerate(robot_namelist):
        cm = globalmaps[i]
        rospy.loginfo(
            'filter: %s costmap frame=%s (sample via TF only if != %s)',
            name,
            cm.header.frame_id,
            map_frame,
        )

#---------------------------------------------------------------------------------------------------------------
    # Busy-wait without rospy.sleep() starves /detected_points callbacks.
    wait_frontier_start = rospy.get_time()
    while len(frontiers) < 1 and not rospy.is_shutdown():
        if rospy.get_time() - wait_frontier_start > 10.0:
            rospy.logwarn_throttle(
                10.0,
                'filter: no messages on %s — RRT detectors publish here after '
                '4 boundary clicks on /clicked_point (or 5 extra RViz clicks). '
                'Check: rosnode list | grep rrt; rostopic hz %s',
                goals_topic,
                goals_topic,
            )
            wait_frontier_start = rospy.get_time()
        rospy.sleep(0.05)
    rospy.loginfo(
        'filter: first frontier from %s — starting /filtered_points publish',
        goals_topic,
    )

    points = Marker()
    points_clust = Marker()
# Set the frame ID and timestamp.  See the TF tutorials for information on these.
    points.header.frame_id = map_frame
    points.header.stamp = rospy.Time.now()

    points.ns = "markers2"
    points.id = 0

    points.type = Marker.POINTS
    points.action = Marker.ADD
    points.pose.orientation.w = 1.0
    points.scale.x = 0.5
    points.scale.y = 0.5
    points.color.r = 255.0/255.0
    points.color.g = 255.0/255.0
    points.color.b = 0.0/255.0
    points.color.a = 1
    points.lifetime = rospy.Duration()

    p = Point()

    p.z = 0

    pp = []
    pl = []

    points_clust.header.frame_id = map_frame
    points_clust.header.stamp = rospy.Time.now()

    points_clust.ns = "markers3"
    points_clust.id = 4

    points_clust.type = Marker.POINTS
    points_clust.action = Marker.ADD
    points_clust.pose.orientation.w = 1.0
    points_clust.scale.x = 0.6
    points_clust.scale.y = 0.6
    points_clust.color.r = 0.0/255.0
    points_clust.color.g = 255.0/255.0
    points_clust.color.b = 0.0/255.0
    points_clust.color.a = 1
    points_clust.lifetime = rospy.Duration()

    points_filtered = Marker()
    points_filtered.header.frame_id = map_frame
    points_filtered.ns = 'filtered_points'
    points_filtered.id = 0
    # ★ 2026-07-26 사용자 요청: frontier 사각형을 로봇별 색 + '속 빈 테두리'로.
    #   (전 로봇 공통 자홍 채움 사각형은 누구 것인지 구분 불가 + 배정가능 구슬을
    #   가림) LINE_LIST 외곽선이라 로봇색 구슬/화살표와 겹쳐도 서로 보인다.
    points_filtered.type = Marker.LINE_LIST
    points_filtered.action = Marker.ADD
    points_filtered.pose.orientation.w = 1.0
    points_filtered.scale.x = 0.05
    _fp_pal = {'locobot_0': (1.0, 0.86, 0.0), 'locobot_1': (0.47, 1.0, 0.31),
               'locobot_2': (0.39, 0.71, 1.0), 'stretch_0': (1.0, 0.47, 0.16)}
    _fp_key = rospy.get_namespace().strip('/') or str(map_frame).split('/')[0]
    _fp_rgb = _fp_pal.get(_fp_key, (1.0, 0.2, 1.0))   # 미상(공유 filter)=기존 자홍
    points_filtered.color.r = _fp_rgb[0]
    points_filtered.color.g = _fp_rgb[1]
    points_filtered.color.b = _fp_rgb[2]
    points_filtered.color.a = 1.0
    points_filtered.lifetime = rospy.Duration()

    temppoint = PointStamped()
    temppoint.header.frame_id = map_frame
    temppoint.header.stamp = rospy.Time(0)
    temppoint.point.z = 0.0

    arraypoints = PointArray()
    tempPoint = Point()
    tempPoint.z = 0.0
# -------------------------------------------------------------------------
# ---------------------     Main   Loop     -------------------------------
# -------------------------------------------------------------------------
    while not rospy.is_shutdown():
        # -------------------------------------------------------------------------
        # Clustering frontier points
        centroids = []
        front = copy(frontiers)
        if len(front) > 1:
            ms = MeanShift(bandwidth=bandwith_cluster)
            ms.fit(front)
            centroids = ms.cluster_centers_  # centroids array is the centers of each cluster

        # if there is only one frontier no need for clustering, i.e. centroids=frontiers
        if len(front) == 1:
            centroids = front
        # RViz: raw MeanShift clusters on merged /map (before costmap filter)
        raw_pp = []
        for q in range(0, len(centroids)):
            p.x = float(centroids[q][0])
            p.y = float(centroids[q][1])
            raw_pp.append(copy(p))
        points_clust_raw = copy(points_clust)
        points_clust_raw.ns = 'centroids_raw'
        points_clust_raw.id = 3
        points_clust_raw.color.r = 0.2
        points_clust_raw.color.g = 0.85
        points_clust_raw.color.b = 1.0
        points_clust_raw.header.stamp = rospy.Time.now()
        if raw_pp:
            points_clust_raw.points = raw_pp
            points_clust_raw.action = Marker.ADD
        else:
            points_clust_raw.action = Marker.DELETEALL
            points_clust_raw.points = []
        pub2_raw.publish(points_clust_raw)
# -------------------------------------------------------------------------
# clearing old frontiers

        # ★ baseline v2(2026-07-27 사용자 지시 '지도 밖 frontier 고쳐라'):
        #   후보를 '관측된 free' 셀로 스냅. 검출기 eta 오버슛/벽틈 때문에
        #   미지·벽 밖에 찍힌 후보를 경계 위로 교정하고, 반경 내 free 가
        #   없으면(완전 벽 밖) 폐기한다. ~snap_to_free 파라미터로만 활성.
        if snap_to_free and len(centroids) > 0 and len(mapData.data) > 0:
            _W9 = mapData.info.width; _H9 = mapData.info.height
            _res9 = mapData.info.resolution
            _ox9 = mapData.info.origin.position.x
            _oy9 = mapData.info.origin.position.y
            _arr9 = _np_sf.asarray(mapData.data, dtype=_np_sf.int16).reshape(_H9, _W9)
            _rad9 = max(1, int(1.2 / _res9))
            z9 = 0
            _snapped9 = _dropped9 = 0
            while z9 < len(centroids):
                _cx9 = float(centroids[z9][0]); _cy9 = float(centroids[z9][1])
                _j9 = int((_cx9 - _ox9) / _res9); _i9 = int((_cy9 - _oy9) / _res9)
                _v9 = (_arr9[_i9, _j9]
                       if 0 <= _i9 < _H9 and 0 <= _j9 < _W9 else -1)
                if 0 <= _v9 < 50:
                    z9 += 1
                    continue        # 이미 관측-free — 그대로
                _i0 = max(0, _i9 - _rad9); _i1 = min(_H9, _i9 + _rad9 + 1)
                _j0 = max(0, _j9 - _rad9); _j1 = min(_W9, _j9 + _rad9 + 1)
                _win9 = _arr9[_i0:_i1, _j0:_j1]
                _fy9, _fx9 = _np_sf.nonzero((_win9 >= 0) & (_win9 < 50))
                if len(_fy9) == 0:
                    centroids = delete(centroids, (z9), axis=0)
                    _dropped9 += 1
                    continue        # 반경 내 free 없음(벽 밖) — 폐기
                _dd9 = (_fy9 - (_i9 - _i0)) ** 2 + (_fx9 - (_j9 - _j0)) ** 2
                _k9 = int(_np_sf.argmin(_dd9))
                centroids[z9][0] = _ox9 + (_j0 + int(_fx9[_k9]) + 0.5) * _res9
                centroids[z9][1] = _oy9 + (_i0 + int(_fy9[_k9]) + 0.5) * _res9
                _snapped9 += 1
                z9 += 1
            if _snapped9 or _dropped9:
                rospy.loginfo_throttle(10.0,
                    'filter: 후보 free-스냅 %d개, 벽밖 폐기 %d개 (baseline v2)',
                    _snapped9, _dropped9)
        drop_costmap = drop_corner = drop_info = 0
        z = 0
        while z < len(centroids):
            pt_xy = [centroids[z][0], centroids[z][1]]
            temppoint.point.x = pt_xy[0]
            temppoint.point.y = pt_xy[1]

            if costmap_clearing_mode == 'all_robots':
                cond = frontier_cleared_on_all_robot_costmaps(
                    globalmaps,
                    pt_xy,
                    tfLisn,
                    threshold,
                    target_frame,
                )
            else:
                cond = False
                for i in range(0, len(robot_namelist)):
                    try:
                        x = costmap_xy_from_map_point(
                            target_frame, pt_xy, globalmaps[i], tfLisn,
                        )
                        cond = costmap_invalidates_frontier(
                            globalmaps[i], x, threshold,
                        ) or cond
                    except (
                        tf.LookupException,
                        tf.ConnectivityException,
                        tf.ExtrapolationException,
                    ) as exc:
                        rospy.logwarn_throttle(
                            10.0,
                            'filter: costmap TF %s -> %s failed: %s',
                            map_frame,
                            globalmaps[i].header.frame_id,
                            exc,
                        )
            corner_drop = (
                reject_corner_frontiers
                and is_corner_frontier(
                    mapData,
                    pt_xy,
                    hard_reject_opening_deg=corner_hard_reject_opening_deg,
                    two_wall_opening_deg=corner_two_wall_opening_deg,
                    min_wall_directions=corner_min_wall_directions,
                    min_passage_clear_m=corner_min_passage_clear_m,
                )
            )
            ig = informationGain(mapData, pt_xy, info_radius * 0.5)
            info_drop = ig < min_info_gain_keep
            if cond or corner_drop or info_drop:
                if cond:
                    drop_costmap += 1
                elif corner_drop:
                    drop_corner += 1
                elif info_drop:
                    drop_info += 1
                centroids = delete(centroids, (z), axis=0)
                z = z - 1
            z += 1
        if len(centroids) > 0:
            frontiers = copy(centroids)
# -------------------------------------------------------------------------
# publishing
        arraypoints.points = []
        for i in centroids:
            tempPoint.x = i[0]
            tempPoint.y = i[1]
            arraypoints.points.append(copy(tempPoint))
            # print("------frontier: [%f %f ]" %( i[0],  i[1]))
        filterpub.publish(arraypoints)
        if len(centroids) < 1:
            rospy.logwarn_throttle(
                8.0,
                'filter: 0 frontiers after filter (raw=%d) drops: costmap=%d corner=%d info=%d '
                '(mode=%s thresh=%d min_info=%.3f)',
                len(front),
                drop_costmap,
                drop_corner,
                drop_info,
                costmap_clearing_mode,
                int(threshold),
                float(min_info_gain_keep),
            )
        else:
            rospy.loginfo_throttle(
                5.0,
                'filter: publishing %d frontier(s) on /filtered_points',
                len(centroids),
            )
        fp_pts = []
        _fh = 0.17          # 반변 — 0.34m 속 빈 사각 테두리 (LINE_LIST 4변=8점)
        for i in centroids:
            _cx = float(i[0])
            _cy = float(i[1])
            _c4 = ((_cx - _fh, _cy - _fh), (_cx + _fh, _cy - _fh),
                   (_cx + _fh, _cy + _fh), (_cx - _fh, _cy + _fh))
            for _k in range(4):
                for _xy in (_c4[_k], _c4[(_k + 1) % 4]):
                    pt = Point()
                    pt.x = _xy[0]
                    pt.y = _xy[1]
                    pt.z = 0.02
                    fp_pts.append(pt)
        points_filtered.header.frame_id = map_frame
        points_filtered.header.stamp = rospy.Time.now()
        points_filtered.points = fp_pts
        if fp_pts:
            points_filtered.action = Marker.ADD
            filtered_marker_pub.publish(points_filtered)
        else:
            points_filtered.action = Marker.DELETEALL
            filtered_marker_pub.publish(points_filtered)
            points_filtered.action = Marker.ADD
        pp = []
        for q in range(0, len(frontiers)):
            p.x = frontiers[q][0]
            p.y = frontiers[q][1]
            pp.append(copy(p))
        points.points = pp
        pp = []
        for q in range(0, len(centroids)):
            p.x = centroids[q][0]
            p.y = centroids[q][1]
            pp.append(copy(p))
        now = rospy.Time.now()
        points.header.stamp = now
        points_clust.header.stamp = now
        points_clust.header.frame_id = map_frame
        if pp:
            points_clust.points = pp
            points_clust.action = Marker.ADD
        else:
            points_clust.action = Marker.DELETEALL
            points_clust.points = []
        pub.publish(points)
        pub2.publish(points_clust)
        points_clust.action = Marker.ADD
        
        # rospy.loginfo('publish the cleaned up frontier')
        rate.sleep()
# -------------------------------------------------------------------------


if __name__ == '__main__':
    try:
        node()
    except rospy.ROSInterruptException:
        pass
