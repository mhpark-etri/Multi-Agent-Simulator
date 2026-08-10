#!/usr/bin/env python3
"""filtered frontier(PointArray, rrt_exploration 커스텀 msg)를 표준
geometry_msgs/PoseArray 로 릴레이 — JnP 그룹 노드(탐사 워크스페이스 미소싱)가
프런티어를 표준 메시지로 구독할 수 있게 한다 (2026-08-09, 완전 JnP화)."""
import rospy
from rrt_exploration.msg import PointArray
from geometry_msgs.msg import PoseArray, Pose

pub = None

def cb(msg):
    pa = PoseArray()
    pa.header.frame_id = 'map'
    pa.header.stamp = rospy.Time.now()
    for p in msg.points:
        q = Pose()
        q.position.x = p.x
        q.position.y = p.y
        q.orientation.w = 1.0
        pa.poses.append(q)
    pub.publish(pa)

if __name__ == '__main__':
    rospy.init_node('frontier_relay')
    pub = rospy.Publisher('/frontiers_pose', PoseArray, queue_size=2)
    rospy.Subscriber(rospy.get_param('~frontiers_topic', '/filtered_points'),
                     PointArray, cb, queue_size=2)
    rospy.spin()
