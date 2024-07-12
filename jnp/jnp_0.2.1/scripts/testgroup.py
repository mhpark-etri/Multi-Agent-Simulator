#!/usr/bin/env python
import rospy
from std_msgs.msg import String
import subprocess
from rosgraph import Master
import threading
import sys
from jnp.srv import DescriptionService, DescriptionServiceResponse

class JnPTestGroup:

    def __init__(self, node_name='jnpgroup', topic_name='/jnp_agent_join_event', rate=1):
        # Node name 초기화
        self.node_name = node_name
        print("=========================> {0}".format(node_name))
        # Publisher 객체 초기화
        self.publisher = rospy.Publisher(topic_name, String, queue_size=10)
        self.subcriber = rospy.Subscriber('/jnp_agent_join_event', String, self.discovery_callback)
        self.agent_list = [ ]
        self.flag_init_node = False

        # 전송 주기 설정
        #self.rate = rospy.Rate(rate)
        self.rate1=rate

    def start(self):
        #rospy.init_node(self.node_name, anonymous=True)
        # no
        rospy.init_node(self.node_name)
        self.flag_init_node = True
        namespace = rospy.get_namespace()
        node_name = rospy.get_name() # namespace is include in node_name
        pure_node_name = node_name.replace(namespace, "", 1)
        #print("ns = {0} node_name = {1} pure name = {2}".format(namespace, node_name,pure_node_name))
        self.node_name = node_name
        #self.node_name = rospy.get_name()
        thread = threading.Thread(target=self.input_thread)
        thread.start()
        self.service = rospy.Service(self.node_name+'/description_service', DescriptionService, self.handle_description_request)
        self.rate = rospy.Rate(self.rate1)
        advertise_count=0
        try:
            while not rospy.is_shutdown():
            #message = "Hello from Talker class! Time: %s" % rospy.get_time()
                if advertise_count > 2: #send 3 times
                    break
                message = f"new:{node_name}"
                #rospy.loginfo(message)
                print("=====> Send Message[{0}]".format(message))
                self.publisher.publish(message)
                advertise_count = advertise_count + 1
                self.rate.sleep()
        except rospy.exceptions.ROSInterruptException:
            rospy.loginfo("Node shutting down.")

    def discovery_callback(self, msg):
        rospy.loginfo("Received message: %s", msg.data)
        message= msg.data
        node_name = msg.data.split(":")[1]
        if node_name not in self.agent_list:
            if node_name != self.node_name:
                if message.startswith("new:"):
                    print("--->{0}".format(node_name))
                    self.get_description(node_name)
                    self.agent_list.append(node_name)
        else:
            if message.startswith("kill:"):
                self.agent_list.remove(node_name)

    def handle_description_request(self, req):
    # 요청에서 XML 데이터 가져오기
        xml_data = req.input_xml
        rospy.loginfo("Received Description Request")
    # XML 데이터 처리 및 응답 설정 (이 예제에서는 단순한 문자열 응답만을 제공합니다)
        response = DescriptionServiceResponse()
        #response.output_response = "XML data processed successfully"
        response.output_xml = "<data><item>Sample XML content</item><group>"+self.node_name+"</group></data>"
        return response

    def get_description(self,node_name):
        rospy.wait_for_service(node_name+'/description_service')
        try:
            get_xml = rospy.ServiceProxy(node_name+'/description_service', DescriptionService)
            response = get_xml()
            print("Get XML:{0}".format(response))
        #return response.output_xml
        except rospy.ServiceException as e:
            print("Service call failed: %s" % e)

    def search(self):
        topic_name='/jnp_agent_join_event'
        master = Master('/rospy')
        # System state format: [publishers, subscribers, services]
        pub_list = master.getSystemState()[0]
        nodes = []
        for topic, publishers in pub_list:
            if topic == topic_name: 
                #because before init_node(which in start()), my node is not in publishers list.
                if self.flag_init_node:
                    if self.node_name in publihsers:
                        publishers.remove(self.node_name)
                nodes.extend(publishers) #publishsers --> list , type of member of publishers --> string
                for item in publishers:
                    if item not in self.agent_list: #if not in pu
                        self.get_description(item)
                        self.agent_list.append(item)
                set_A = set(self.agent_list)
                set_B = set(publishers)
                self.agent_list = list(set_B.intersection(set_A))
        return nodes

    def input_thread(self):
        while not rospy.is_shutdown():
        # 사용자 입력 대기
            user_input = input("Press 'q' to shut down the node1: ")
        # 'q'가 입력되면 노드 종료
            if user_input == 'q':
                node_name = rospy.get_name()
                message = f"kill:{node_name}"
                rospy.loginfo(message)
                self.publisher.publish(message)
                rospy.signal_shutdown("User requested shutdown.")
                sys.exit(0)

#    def check_new():


if __name__ == '__main__':
    group1 = JnPTestGroup(node_name='group1') 
    #nodes=group1.search()
    #for node in nodes:
    #    print("searched node:{0}".format(node))
    #print("========")
    group1.start()
