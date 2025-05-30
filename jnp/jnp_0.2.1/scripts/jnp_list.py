#!/usr/bin/env python
import rospy
import subprocess

def get_node_type(node_name):

    try:
        # rosnode info 명령을 사용하여 노드 정보 가져오기
        output = subprocess.check_output(['rosnode', 'info', node_name])
        lines = output.split('\n')
        for line in lines:
            if line.startswith('Type:'):
                _, type_name = line.split(' ')
                return type_name
    except:
        return None


def get_nodes_of_type(target_type):

    nodes = rospy.get_published_topics()
    for node in nodes:
       type_name=get_node_type(node)
       print(type_name)
    #matched_nodes = [node for node in nodes if get_node_type(node) == target_type]
    #return matched_nodes

if __name__ == '__main__':
    rospy.init_node('get_node_type_example', anonymous=True)
    target_type = 'desired_node_type'  # 원하는 노드 타입을 여기에 입력
    get_nodes_of_type(target_type)
    #nodes = get_nodes_of_type(target_type)
    #print("Nodes of type '{}':".format(target_type))
    #for node in nodes:
    #    print(node)


