#!/usr/bin/env python3
import math
import rospy
import tf
from geometry_msgs.msg import Point, Point32, PolygonStamped, PointStamped
from std_msgs.msg import Header, ColorRGBA
from visualization_msgs.msg import Marker, MarkerArray
from time import time

#############################################################
recordedPoints = []
n_point_target = 4
map_frame = 'map'
boundary_pub = None
marker_pub = None
tf_listener = None


def transform_clicked_to_map(data):
    """RViz Publish Point may use Fixed Frame; store boundary in map_frame."""
    src = (data.header.frame_id or 'map').strip('/')
    target = map_frame.strip('/')
    if src == target:
        p = Point()
        p.x = data.point.x
        p.y = data.point.y
        p.z = data.point.z
        return p
    if tf_listener is None:
        p = Point()
        p.x = data.point.x
        p.y = data.point.y
        p.z = data.point.z
        return p
    try:
        tf_listener.waitForTransform(
            target, src, rospy.Time(0), rospy.Duration(0.5),
        )
        out = tf_listener.transformPoint(target, data)
        p = Point()
        p.x = out.point.x
        p.y = out.point.y
        p.z = 0.0
        return p
    except (
        tf.LookupException,
        tf.ConnectivityException,
        tf.ExtrapolationException,
    ) as exc:
        rospy.logwarn_throttle(
            5.0,
            'boundary: TF %s -> %s failed (%s); using click coords as-is',
            src, target, exc,
        )
        p = Point()
        p.x = data.point.x
        p.y = data.point.y
        p.z = data.point.z
        return p


def publish_boundary_preview():
    """Publish polygon + markers after each click so RViz shows the box while clicking."""
    if boundary_pub is None or len(recordedPoints) < 1:
        return
    stamp = rospy.Time.now()
    header = Header()
    header.frame_id = map_frame
    header.stamp = stamp

    boundary_list = PolygonStamped()
    boundary_list.header = header
    boundary_list.polygon.points = []
    for p in recordedPoints:
        p32 = Point32()
        p32.x = float(p.x)
        p32.y = float(p.y)
        p32.z = float(p.z)
        boundary_list.polygon.points.append(p32)
    boundary_pub.publish(boundary_list)

    if marker_pub is None:
        return
    ma = MarkerArray()
    corner = Marker()
    corner.header = header
    corner.ns = 'boundary_corners'
    corner.id = 0
    corner.type = Marker.SPHERE_LIST
    corner.action = Marker.ADD
    corner.pose.orientation.w = 1.0
    corner.scale.x = corner.scale.y = corner.scale.z = 0.25
    corner.color = ColorRGBA(1.0, 0.85, 0.1, 1.0)
    for p in recordedPoints:
        corner.points.append(Point(x=p.x, y=p.y, z=0.05))
    ma.markers.append(corner)

    if len(recordedPoints) >= 2:
        line = Marker()
        line.header = header
        line.ns = 'boundary_edges'
        line.id = 0
        line.type = Marker.LINE_STRIP
        line.action = Marker.ADD
        line.pose.orientation.w = 1.0
        line.scale.x = 0.08
        line.color = ColorRGBA(1.0, 0.85, 0.1, 0.95)
        for p in recordedPoints:
            line.points.append(Point(x=p.x, y=p.y, z=0.05))
        if len(recordedPoints) >= n_point_target:
            p0 = recordedPoints[0]
            line.points.append(Point(x=p0.x, y=p0.y, z=0.05))
        ma.markers.append(line)

    marker_pub.publish(ma)


def recordedPointsCallback(data):
    global recordedPoints
    if len(recordedPoints) >= n_point_target:
        rospy.logwarn_throttle(
            3.0,
            'boundary: already have %d points — restart exploration_boundary to re-click',
            n_point_target,
        )
        return
    pt = transform_clicked_to_map(data)
    recordedPoints.append(pt)
    n = len(recordedPoints)
    rospy.loginfo(
        'boundary: click %d/%d at (%.2f, %.2f) frame=%s',
        n, n_point_target, pt.x, pt.y, data.header.frame_id or map_frame,
    )
    publish_boundary_preview()


#############################################################
def node():
    global recordedPoints, n_point_target, map_frame, boundary_pub, marker_pub, tf_listener
    rospy.init_node('exploration_boundary', anonymous=False)

    map_frame = rospy.get_param('~map_frame', 'map')
    n_point_target = rospy.get_param('~n_point', 4)
    topic_input = rospy.get_param('~topicInput', '/clicked_point')
    topic_output = rospy.get_param('~topicOutput', '/exploration_boundary')
    marker_topic = rospy.get_param('~marker_topic', '/exploration_boundary_marker')
    frequency = rospy.get_param('~frequency', 1.0)
    time_interval = rospy.get_param('~timeInterval', 5.0)
    use_param_boundary = rospy.get_param('~use_param_boundary', False)
    boundary_coords = rospy.get_param('~boundary_coords', '')
    xmin = rospy.get_param('~xmin', float('nan'))
    xmax = rospy.get_param('~xmax', float('nan'))
    ymin = rospy.get_param('~ymin', float('nan'))
    ymax = rospy.get_param('~ymax', float('nan'))

    tf_listener = tf.TransformListener()
    boundary_pub = rospy.Publisher(
        topic_output, PolygonStamped, queue_size=1, latch=True,
    )
    marker_pub = rospy.Publisher(
        marker_topic, MarkerArray, queue_size=1, latch=True,
    )
    rospy.Subscriber(topic_input, PointStamped, recordedPointsCallback)

    rate = rospy.Rate(frequency)

    if use_param_boundary:
        loaded = []
        if boundary_coords:
            for pair in boundary_coords.split(';'):
                parts = pair.split(',')
                if len(parts) != 2:
                    continue
                p = Point()
                p.x = float(parts[0].strip())
                p.y = float(parts[1].strip())
                p.z = 0.0
                loaded.append(p)
        elif (not math.isnan(xmin) and not math.isnan(xmax)
              and not math.isnan(ymin) and not math.isnan(ymax)):
            rospy.loginfo(
                'boundary box (map): xmin=%.2f xmax=%.2f ymin=%.2f ymax=%.2f',
                xmin, xmax, ymin, ymax,
            )
            for x, y in [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]:
                p = Point()
                p.x = x
                p.y = y
                p.z = 0.0
                loaded.append(p)

        if len(loaded) >= 3:
            recordedPoints = loaded
            n_point_target = len(recordedPoints)
            rospy.loginfo('boundary polygon: loaded %d points from params', n_point_target)
            publish_boundary_preview()
        else:
            rospy.logwarn(
                'use_param_boundary=True but no valid points found, falling back to clicked points',
            )

    rospy.loginfo(
        'boundary: RViz tool "Publish Point" -> %s (%d clicks, frame=%s). '
        'Preview on %s and %s',
        topic_input, n_point_target, map_frame, topic_output, marker_topic,
    )

    while len(recordedPoints) < n_point_target and not rospy.is_shutdown():
        rospy.loginfo_throttle(
            5.0,
            'boundary: waiting for clicks %d/%d on %s (Fixed Frame should be %s)',
            len(recordedPoints), n_point_target, topic_input, map_frame,
        )
        rate.sleep()

    if rospy.is_shutdown():
        return

    rospy.loginfo(
        'boundary polygon: received all %d points — exploration boundary active',
        n_point_target,
    )
    publish_boundary_preview()

    start_time = rospy.get_rostime().secs
    next_time_report = start_time + time_interval
    rospy.loginfo('--- >>> the exploration starts at time: %.2f ', start_time)
    while not rospy.is_shutdown():
        publish_boundary_preview()
        if next_time_report <= rospy.get_rostime().secs:
            rospy.loginfo(
                '--- >>> current time: %.2f    time elapsed: %.2f',
                rospy.get_rostime().secs,
                rospy.get_rostime().secs - start_time,
            )
            next_time_report = rospy.get_rostime().secs + time_interval
        rate.sleep()


#############################################################
if __name__ == '__main__':
    try:
        node()
    except rospy.ROSInterruptException:
        pass
