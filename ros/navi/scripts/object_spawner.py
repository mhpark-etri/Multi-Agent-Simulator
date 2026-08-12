#!/usr/bin/env python3
"""분산탐색-물건찾기: desk 위 탐색 대상 물체 스폰 (2026-08-10).

월드 파일(ros/navi/worlds/...desk_v3.world)은 수정하지 않고, Start 때 이 노드가
desk(3.59,-3.41, 상판 z=0.80) 위에 물병·사과 SDF 를 스폰한다. 물체 위치는
탐색 로봇에게 알려주지 않는다 (YOLO 로 찾는 것이 태스크).
"""
import rospy
from gazebo_msgs.srv import SpawnModel, GetModelState
from geometry_msgs.msg import Pose

# desk_bottom_right: pose (3.590834, -3.41), 상판 1.2x0.6 z=0.775+0.025
# 간단·확실 노선 (2026-08-10 지시): YOLO 가 가장 안정적으로 잡는 큰 공 2개
OBJECTS = [
    ('search_ball_orange', '/root/tesla/ros/navi/models/yolo_ball_orange/model.sdf', 3.40, -3.32, 0.80),
    ('search_ball_blue',   '/root/tesla/ros/navi/models/yolo_ball_blue/model.sdf',   3.85, -3.48, 0.80),
]


def main():
    rospy.init_node('object_spawner')
    rospy.wait_for_service('/gazebo/spawn_sdf_model', timeout=120)
    spawn = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
    gms = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
    for name, sdf_path, x, y, z in OBJECTS:
        try:
            if gms(name, '').success:
                rospy.loginfo('object_spawner: %s 이미 존재 — 생략', name)
                continue
            p = Pose()
            p.position.x, p.position.y, p.position.z = x, y, z
            p.orientation.w = 1.0
            with open(sdf_path) as f:
                spawn(name, f.read(), '', p, 'world')
            rospy.loginfo('object_spawner: %s 스폰 (%.2f,%.2f,%.2f)', name, x, y, z)
        except Exception as e:
            rospy.logwarn('object_spawner: %s 실패 — %s', name, e)


if __name__ == '__main__':
    main()
