#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import subprocess
from rosgraph import Master
import threading
import sys
import copy
from jnp.srv import DescriptionService, DescriptionServiceResponse
import os
import xml.etree.ElementTree as ET

import actionlib
from jnp.msg import AgentActionAction, AgentActionGoal, AgentActionResult, AgentActionFeedback

import time
import random
import json


class JnPAgent:

    def __init__(self, node_name='jnpagent', topic_name='/jnp_agent_join_event', file_name='', rate=1):
        # Node name 초기화
        self.node_name = node_name
        print("=========================> {0}".format(node_name))
        # Publisher 객체 초기화
        self.publisher = rospy.Publisher(topic_name, String, queue_size=10)
        self.subcriber = rospy.Subscriber('/jnp_agent_join_event', String, self.discovery_callback)
        self._goal_items = {}    # /goal_items: goal → (남은수, x, y) — 그룹 간 이적 대상 탐색용
        self.sub_items = rospy.Subscriber('/goal_items', String, self._items_cb)
        self._task_base = None   # base 존 중심 (/task_base latched) — 교통관제용
        from geometry_msgs.msg import PoseStamped as _PS
        self.sub_base = rospy.Subscriber('/task_base', _PS, self._task_base_cb)
        self.agent_list = [ ]
        self.group_list = [ ]
        self.agent_goals = { }   # 0.8.1: 발견한 에이전트의 goal 기억 — task별 리더 선출 후보 판별용
        # 0.8.1: task 처리 직렬화 — 그룹이 advertise 하기 전 창(수 초)에 두 번째 task 가
        # 병렬 콜백으로 들어와 같은 이름의 그룹을 이중 스폰하면 ROS 마스터가
        # 실행 중이던 1차 그룹을 죽인다(동명 노드 대체). 락+busy 로 원천 차단.
        self._task_lock = threading.Lock()
        self._coalition_busy = False
        self._bids = {}      # {라운드ID: {로봇: {goal: eta}}} — 분산 선택 입찰 수집
        self._bid_pos = {}   # {라운드ID: {로봇: "x,y"}} — 입찰에 실린 위치 (홈 좌표)
        self._mg_assign = {}   # {라운드ID: 배분} — 리더 확정 발행(mgassign)
        self.flag_init_node = False
        self.xml_file_path = file_name
   


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
        #task_topic_name=namespace+'jnp_task_alloc_event_topic'
        task_topic_name=node_name+'/jnp_task_alloc_event_topic'
        self.publisher2 = rospy.Publisher(task_topic_name, String, queue_size=10)
        self.subcriber2 = rospy.Subscriber(task_topic_name, String, self.task_callback)
        thread = threading.Thread(target=self.input_thread)
        thread.start()
        self.service = rospy.Service(self.node_name+'/description_service', DescriptionService, self.handle_description_request)
        #self.server = actionlib.SimpleActionServer('AgentActionAction', AgentActionAction, self.execute, False)
        self.server = actionlib.SimpleActionServer('/'+self.node_name+'/AgentActionAction', AgentActionAction, self.execute, False)
        self.server.start()


        self.rate = rospy.Rate(self.rate1)
        advertise_count=0
        try:
            while not rospy.is_shutdown():
            #message = "Hello from Talker class! Time: %s" % rospy.get_time()
                if advertise_count > 2: #send 3 times
                    break
                #namespace = rospy.get_namespace()
                #node_name = rospy.get_name() # namespace is include in node_name
                #print("ns = {0} name={1}".format(namespace, node_name))
            #message = f"{namespace}:{node_name}"
                message = f"new:{node_name}"
                #rospy.loginfo(message)
                print("=====> Send Message[{0}]".format(message))
                self.publisher.publish(message)
                advertise_count = advertise_count + 1
                self.rate.sleep()
        except rospy.exceptions.ROSInterruptException:
            rospy.loginfo("Node shutting down.")

    def task_callback(self, msg):
        rospy.loginfo("Received task message: %s", msg.data)
        message= msg.data
        # baisc collabo task : 1:Relay 2:Mult-Goal 3:BCA 4:Map-Gen 5:Find-Obj
        
        # Respond bidding: Send its skill -->launch file etc. hw specs...


        #Accept the atomic action: Allocated Task 

    def discovery_callback(self, msg):
        rospy.loginfo("Received discovery message: %s", msg.data)
        message= msg.data
        if message.startswith("task:"):
            # 0.8.1: task(goal) 공지 — coalition 형성의 유일한 트리거
            self.handle_task_event(message)
            return
        if message.startswith("mgjoin:"):
            return                          # 그룹 대상 메시지 — 에이전트는 무시
        if message.startswith("mgrelease:"):
            # 그룹 간 이적: 방출 통보 — 탈퇴와 '동시에' 물품 남은 goal 그룹 가입
            try:
                _, node, old_group, exclude = (message.split(':', 3) + [''])[:4]
            except ValueError:
                return
            if node.strip() != self.node_name:
                return
            threading.Thread(
                target=self._transfer_groups,
                args=(old_group.strip(),
                      {g.strip() for g in exclude.split(',') if g.strip()}),
                daemon=True).start()
            return
        if message.startswith("mgassign:"):
            # 리더가 확정한 배분 — 라운드 ID 로 이번 task 것만 수락
            try:
                _, rid, body = message.split(':', 2)
                self._mg_assign.setdefault(rid.strip(), {}).update(
                    {kv.split('=')[0]: kv.split('=')[1]
                     for kv in body.split('|') if '=' in kv})
            except (ValueError, IndexError):
                pass
            return
        if message.startswith("mgbid:"):
            # 분산 선택 입찰: mgbid:<라운드>:<로봇>:<G1>=<eta>|... — 라운드별 수집
            # (라운드 ID 가 있어 수집함을 초기화할 필요가 없고, 도착 순서 레이스가 사라짐)
            try:
                _, rid, who, pos, etas = message.split(':', 4)
                self._bids.setdefault(rid.strip(), {})[who.strip()] = {
                    kv.split('=')[0]: float(kv.split('=')[1])
                    for kv in etas.split('|') if '=' in kv}
                if ',' in pos:
                    self._bid_pos.setdefault(rid.strip(), {})[who.strip()] = pos.strip()
            except (ValueError, IndexError):
                pass
            return
        node_name = msg.data.split(":")[1]
        if message.startswith("kill:"):
            # 탈퇴/해체 통지: agent_list와 group_list 양쪽에서 제거
            # (기존 코드는 agent_list만 정리해 그룹 해체 후에도 group_list가 오염된 채 남았음)
            if node_name in self.agent_list:
                self.agent_list.remove(node_name)
            if node_name in self.group_list:
                self.group_list.remove(node_name)
            return
        if node_name not in self.agent_list:
            if node_name != self.node_name:
                if message.startswith("new:"):
                    print("--->{0}".format(node_name))
                    if (node_name not in self.agent_list) and  (node_name not in self.group_list):
                        description = self.get_description(node_name)
                        if not description:   # 서비스 실패(None) 방어
                            return
                        if "<agent>" in description:
                            self.agent_list.append(node_name)
                            self.agent_goals[node_name] = self._desc_goal(description)
                        if "<group>" in description:
                            self.group_list.append(node_name)
                        # 0.8.1: coalition은 task에 종속 — 발견만으로는 그룹을 만들지 않는다.
                        # (~auto_group:=true 는 '발견-즉시-그룹' 트리거만 되살린다.
                        #  그룹 노드 자체는 0.8.1 동작 — 완전한 0.8 은 /mnt/20260804 참조)
                        if rospy.get_param('~auto_group', False):
                            if len(self.agent_list)>=1 and (node_name not in self.group_list):
                                self.make_group()

    def _desc_goal(self, description):
        """description XML에서 <goal> 텍스트 추출 (실패 시 '')."""
        try:
            root = ET.fromstring(description)
            el = root.find('goal')
            return el.text if (el is not None and el.text) else ''
        except ET.ParseError:
            return ''

    def handle_task_event(self, message):
        """0.8.1: 'task:<goal>[:<payload>]' — goal 부여 = coalition 형성 트리거.
        goal이 맞는 에이전트만 반응하고, 그중 리더가 goal/payload를 그룹 노드에 넘긴다.
        완료되면 그룹이 kill을 발행해 해체(coalition)되고, 에이전트는 다음 task를 기다린다."""
        parts = message.split(':', 2)
        task_goal = parts[1].strip()
        payload = parts[2] if len(parts) > 2 else ''
        if not task_goal:
            rospy.logwarn('빈 goal 의 task 무시: %s', message)
            return
        my_goal = rospy.get_param('~jnp_goal', 'Relay,Mult-Goal,Avoidance,MapExplore,ObjectSearch')
        if not (task_goal in my_goal or my_goal == 'Any'):
            return                      # 내 goal과 무관한 task
        # 0.8.1: payload 에 robots= 명단이 있으면 명단에 든 에이전트만 참여
        # (다목적 이동의 goal별 그룹 — 서로 다른 로봇 부분집합이 동시에 별도 coalition)
        task_robots = None
        for sec in payload.split(';'):
            sec = sec.strip()
            if sec.startswith('robots='):
                task_robots = {r.split(':')[0].strip()
                               for r in sec[len('robots='):].split('|') if r.strip()}
        my_short = self.node_name.strip('/').split('/')[-1]
        if task_robots is not None and my_short not in task_robots:
            return                      # 이 그룹 대상이 아님
        if 'mode=dynamic' in payload and 'Avoidance' in task_goal:
            # v4(2026-08-09): 그룹 선형성 없음 — 전원 병렬 출발, 충돌 '예측' 시
            # 관련 로봇끼리 즉석 충돌방지 coalition 형성/해산
            if getattr(self, '_av_running', False):
                rospy.logwarn('동적 회피 이미 실행 중 — 재발행 무시')
                return
            self._av_running = True
            threading.Thread(target=self._solo_avoidance, args=(payload,),
                             daemon=True).start()
            return
        with self._task_lock:
            if self._coalition_busy:
                rospy.logwarn('task 수신했으나 coalition 진행 중 — 완료 후 재발행 요망')
                return
            if self.group_list:
                # 그룹이 비정상 종료(kill 미발행)했을 수 있다 — 죽은 그룹은 정리하고 진행
                self._purge_dead_groups()
            if self.group_list:
                rospy.logwarn('task 수신했으나 이미 coalition 소속 — 해체 후 재시도 요망')
                return
            self._coalition_busy = True
        try:
            if (task_goal == 'Mult-Goal' and 'goals=' in payload
                    and task_robots is None):
                # 다중 goal 공지: 에이전트가 스스로 goal 을 선택(가장 빨리 도달 기준)
                # 하고 같은 선택끼리 goal별 그룹을 만든다 (분산 선택 프로토콜)
                self._multigoal_select_and_group(payload)
            else:
                # 리더는 그룹 종료까지 여기서 블록 → busy 가 coalition 전체 기간을 커버
                self.make_group(goal=task_goal, payload=payload)
        finally:
            self._coalition_busy = False

    # ── 다목적 이동: 분산 goal 선택 프로토콜 (2026-08-08) ──
    # 각 에이전트가 자기 위치/속도 특성으로 goal별 ETA 를 입찰(mgbid)하고,
    # 모두 같은 입찰 데이터에 같은 결정 알고리즘을 적용해 같은 배분에 합의한다.
    #  - opt=fast (기본): 각자 가장 빨리 갈 수 있는 goal 선택 (+ 빈 goal 최소 보정)
    #  - opt=total: 전체 완료 시간 고려 — goal 정원을 물품 비율로 잡고 ETA 순 배정
    def _robot_speed(self):
        sp = rospy.get_param('~speed', 0.0)
        if sp:
            return float(sp)
        short = self.node_name.strip('/').split('/')[-1]
        if 'locobot' in short:
            return 0.4
        if 'tb3' in short or 'burger' in short:
            return 0.2
        return 0.3

    def _multigoal_select_and_group(self, payload):
        import math
        # goals / opt 파싱
        goals = {}
        opt = 'fast'
        for sec in payload.split(';'):
            sec = sec.strip()
            if sec.startswith('goals='):
                for g in sec[len('goals='):].split('|'):
                    parts = g.strip().split(':')
                    if len(parts) >= 3:
                        x, y = parts[1].split(',')[:2]
                        goals[parts[0].strip()] = (float(x), float(y), int(parts[2]))
            elif sec.startswith('opt='):
                opt = sec[len('opt='):].strip() or 'fast'
        if not goals:
            return
        my_short = self.node_name.strip('/').split('/')[-1]
        # 내 위치(odom) + 속도 특성 → goal별 ETA
        try:
            from nav_msgs.msg import Odometry
            od = rospy.wait_for_message('/%s/odom' % my_short, Odometry, timeout=5.0)
            mx, my_ = od.pose.pose.position.x, od.pose.pose.position.y
        except Exception as e:
            rospy.logwarn('위치 확인 실패 — 선택 불참: %s', e)
            return
        speed = self._robot_speed()
        etas = {g: math.hypot(v[0] - mx, v[1] - my_) / max(speed, 0.05)
                for g, v in goals.items()}
        # 라운드 ID = payload 해시 (모든 에이전트 동일) — 도착 순서 레이스 제거
        import hashlib
        rid = hashlib.md5(payload.encode()).hexdigest()[:8]
        # 입찰 발행(유실·타이밍 대비 3회 재발행) + 3초 수집
        self._bids.setdefault(rid, {})[my_short] = dict(etas)
        self._bid_pos.setdefault(rid, {})[my_short] = f"{mx:.2f},{my_:.2f}"
        self._mg_home = (mx, my_)   # 고정 홈(베이스 슬롯) — 복귀 표류 방지
        bid = (f"mgbid:{rid}:{my_short}:{mx:.2f},{my_:.2f}:" + "|".join(
            f"{g}={e:.2f}" for g, e in etas.items()))
        for _ in range(3):
            self.publisher.publish(bid)
            time.sleep(1.0)
        bids = {a: dict(b) for a, b in self._bids.get(rid, {}).items()
                if set(b.keys()) >= set(goals.keys())}
        if my_short not in bids:
            bids[my_short] = dict(etas)
        agents = sorted(bids.keys())
        print(f"[MG선택] 입찰 {len(agents)}대 opt={opt}", flush=True)
        # ── 결정은 리더 한 명이 내리고 mgassign 으로 확정 발행 (뷰 불일치 방지) ──
        leader = sorted(agents, reverse=True)[0]
        if my_short != leader:
            # 리더의 확정 배분 대기 (최대 6초) — 없으면 지역 계산 폴백
            for _ in range(60):
                if self._mg_assign.get(rid):
                    break
                time.sleep(0.1)
            if self._mg_assign.get(rid):
                assign = dict(self._mg_assign[rid])
                if my_short not in assign:
                    return
                my_g = assign[my_short]
                members = sorted(a for a in assign if assign[a] == my_g)
                self._mg_slot = members.index(my_short) % 4   # 부채꼴 슬롯(순번)
                print(f"[MG선택] 리더 배분 수신 {assign} → 내 goal={my_g}", flush=True)
                gx, gy, gn = goals[my_g]
                _pos = self._bid_pos.get(rid, {})
                sub_payload = (f"goals={my_g}:{gx:.2f},{gy:.2f}:{gn}"
                               f";robots=" + "|".join(
                                   f"{m}:{_pos[m]}" if m in _pos else m for m in members))
                self.make_group(goal='Mult-Goal', payload=sub_payload)
                return
        # (리더이거나 폴백) ── 동일 결정 알고리즘 ──
        assign = {}
        if opt == 'total':
            total_items = sum(v[2] for v in goals.values()) or 1
            caps = {g: max(1, round(len(agents) * v[2] / total_items))
                    for g, v in goals.items()}
            while sum(caps.values()) > len(agents):
                caps[max(caps, key=lambda g: caps[g])] -= 1
            while sum(caps.values()) < len(agents):
                caps[min(caps, key=lambda g: caps[g])] += 1
            entries = sorted((bids[a][g], a, g) for a in agents for g in goals)
            cnt = {g: 0 for g in goals}
            for eta, a, g in entries:
                if a not in assign and cnt[g] < caps[g]:
                    assign[a] = g
                    cnt[g] += 1
        else:
            for a in agents:
                assign[a] = min(goals, key=lambda g: bids[a][g])
            # 빈 goal 보정: 아무도 안 고른 goal 에는 이동 손해가 가장 적은 로봇을 보낸다
            for g in sorted(goals):
                if g not in assign.values():
                    donors = [a for a in agents
                              if list(assign.values()).count(assign[a]) > 1]
                    if not donors:
                        donors = agents[:]
                    mover = min(donors, key=lambda a: bids[a][g] - bids[a][assign[a]])
                    assign[mover] = g
        # 리더: 확정 배분 발행 (2회 — 유실 대비)
        if my_short == leader:
            msg = f"mgassign:{rid}:" + "|".join(f"{a}={g}" for a, g in sorted(assign.items()))
            self.publisher.publish(msg)
            time.sleep(0.3)
            self.publisher.publish(msg)
        my_g = assign[my_short]
        members = sorted(a for a in agents if assign[a] == my_g)
        self._mg_slot = members.index(my_short) % 4           # 부채꼴 슬롯(순번)
        print(f"[MG선택] 배분 {assign} → 내 goal={my_g} 멤버={members}", flush=True)
        # goal별 그룹 형성: 같은 goal 을 고른 멤버들끼리 coalition
        gx, gy, gn = goals[my_g]
        _pos = self._bid_pos.get(rid, {})
        sub_payload = (f"goals={my_g}:{gx:.2f},{gy:.2f}:{gn}"
                       f";robots=" + "|".join(
                           f"{m}:{_pos[m]}" if m in _pos else m for m in members))
        self.make_group(goal='Mult-Goal', payload=sub_payload)

    def _purge_dead_groups(self):
        """0.8.1: 유령 coalition 방지 — group_list의 그룹이 실제 살아있는지
        description 서비스를 **실제 호출**해 확인하고, 죽은 그룹은 제거한다.
        (그룹이 크래시로 kill을 못 보내면 에이전트가 영원히 소속 상태에 갇히는 문제.
        등록 조회(lookupService)는 크래시한 노드의 유령 등록에 속으므로 실호출로 판정)"""
        alive = []
        for g in self.group_list:
            try:
                proxy = rospy.ServiceProxy(g + '/description_service', DescriptionService)
                resp = proxy()          # 죽은 그룹이면 connection 실패로 즉시 예외
                if resp is not None:
                    alive.append(g)
            except Exception:
                rospy.logwarn('dead group purged: %s', g)
        self.group_list = alive
        # (kill: 처리는 함수 상단으로 이동)
        # if new agent --> making group start
        # if wanted group is initiated, no action performed.
        # or no watend group, making the group now!
        #check_group_node()
        #make_group()o

        #if you are leader, you should maintain the member's specs

    def handle_description_request(self, req):
    # 요청에서 XML 데이터 가져오기
        xml_data = req.input_xml
        rospy.loginfo("Received Description Request")
    # XML 데이터 처리 및 응답 설정 (이 예제에서는 단순한 문자열 응답만을 제공합니다)
        response = DescriptionServiceResponse()
        #response.output_response = "XML data processed successfully"

        if os.path.exists(self.xml_file_path):
            try:
                with open(self.xml_file_path, 'r') as file:
                    response.output_xml = file.read()  # 파일 내용을 읽어 응답에 설정
                rospy.loginfo("Successfully read XML file.")
            except Exception as e:
                rospy.logerr(f"Error reading the XML file: {e}")
                response.output_xml = "<error>Error reading XML file</error>"
        else:
            # goal/capability는 파라미터로 설정 가능 (기본값은 그룹(goal='Relay')에 모집되도록 함)
            # 기존 XML은 goal이 'None'이고 <capability>가 없어 멤버 수집이 항상 실패했음
            goal = rospy.get_param('~jnp_goal', 'Relay,Mult-Goal,Avoidance,MapExplore,ObjectSearch')
            capability = rospy.get_param('~jnp_capability', '')
            if not capability:
                # 탑재 컴퓨팅 등급도 광고 (2026-08-11): 지도 병합처럼 무거운
                # 공유 서비스의 호스트를 '이름 순'이 아니라 '성능 순'으로 고르기
                # 위한 근거. LoCoBot=x86 NUC급, TB3(waffle/burger)=라즈베리파이.
                _me9 = self.node_name.strip('/').split('/')[-1]
                capability = ('lidar,camera,compute_x86' if 'locobot' in _me9
                              else 'lidar,camera,compute_arm')
            response.output_xml = ("<data><item>Sample XML content</item><agent>" + self.node_name
                                   + "</agent><goal>" + goal + "</goal>"
                                   + "<capability>" + capability + "</capability></data>")
            # baisc collabo task : 1:Relay 2:Mult-Goal 3:BCA 4:Map-Gen 5:Find-Obj 6:None 7:Any
        return response

    def get_description(self,node_name):
        # ★ 타임아웃 필수: join 토픽 퍼블리셔 중에는 description 서비스가 없는
        #   일회성 노드(GUI 의 rostopic pub 등)도 있다 — 무제한 대기면 여기서 영원히 멈춘다
        try:
            rospy.wait_for_service(node_name+'/description_service', timeout=3.0)
        except rospy.ROSException:
            print("description service timeout: %s" % node_name)
            return None
        try:
            get_xml = rospy.ServiceProxy(node_name+'/description_service', DescriptionService)
            response = get_xml()
            print("Get XML:{0}".format(response))
            return response.output_xml
        except rospy.ServiceException as e:
            print("Service call failed: %s" % e)
            return None

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
                    if self.node_name in publishers:
                        publishers.remove(self.node_name)
                nodes.extend(publishers) #publishsers --> list , type of member of publishers --> string
                #self.agent_list.extend(item for item in publishers if item not in self.agent_list) #if not in pu
                for node in publishers:
                    if node not in self.agent_list: #if not in pu
                        if node != self.node_name:
                            if (self.node_name not in self.agent_list) and (self.node_name not in self.group_list):
                                description=self.get_description(node)
                                try:
                                    root = ET.fromstring(description)  # XML 문자열을 파싱하여 루트 엘리먼트 생성
                                    rospy.loginfo("Successfully parsed XML data.")

                                    # 예를 들어, <item> 태그의 내용을 가져오는 경우
                                    items = root.findall('item')  # 'item' 태그를 찾습니다.
                                    if not items:
                                        rospy.loginfo("No 'item' tags found in the XML data.")
                                    else:
                                        for item in items:
                                            # 각 'item'의 텍스트 출력
                                            rospy.loginfo(f"Item: {item.text if item.text is not None else 'No content'}")

                                    # 특정 정보를 가져오는 예제
                                    agent = root.find('agent')  # 'agent' 태그를 찾습니다.
                                    if agent is not None:
                                        rospy.loginfo(f"Agent: {agent.text}")

                                except ET.ParseError as e:
                                    rospy.logerr(f"Error parsing XML: {e}")


                                if "<agent>" in description:
                                    self.agent_list.append(node)
                                    self.agent_goals[node] = self._desc_goal(description)
                                if "<group>" in description:
                                    # ★ 0.8 버그 수정: 자기 이름(self.node_name)을 넣으면
                                    #   영구히 지울 수 없는 유령 소속이 된다(자기 서비스는
                                    #   항상 응답 → purge 불가, kill 로도 제거 불가).
                                    self.group_list.append(node)
                                # 0.8.1: 발견-즉시-그룹은 ~auto_group 게이트 뒤로 (기본 off)
                                if rospy.get_param('~auto_group', False):
                                    if len(self.agent_list)>=1 and (self.node_name not in self.group_list):
                                        self.make_group()

                set_A = set(self.agent_list)
                set_B = set(publishers)
                self.agent_list = list(set_B.intersection(set_A))
        return nodes

    def read_output(self,output):
        for line in iter(output.readline, b''):
            print("Output:", line.decode().strip())
        output.close()

    def read_output2(self,output):
        for line in iter(output.readline, b''):
            print("Output:", line.decode().strip())
        output.close()

    def make_group(self, goal=None, payload=''):
        print("---------- Make Group -------------")
        #propose a group
        #gather the volunteer node
        #spawn the group node, by negotiation.
        #at this time, determine the alphabetical order of node name
        #if i am the selected node, check the group node exists alredy.
        #if no group exhist, spawn the group node at this machine. and send the participation message to the member node.
        #if the group exhist, ask the group node to particiate.
        # 0.8.1: task 트리거(goal 있음)면 그 goal이 맞는 에이전트만 선출 후보로.
        #   전체 목록으로 뽑으면 goal이 다른 에이전트가 1위가 되어 아무도 스폰 안 하는 구멍이 생긴다.
        if goal:
            cands = [a for a in self.agent_list
                     if goal in self.agent_goals.get(a, '') or self.agent_goals.get(a, '') == 'Any']
            # payload 에 robots= 명단이 있으면 후보도 그 명단으로 제한 (goal별 그룹)
            _robots = None
            for sec in (payload or '').split(';'):
                sec = sec.strip()
                if sec.startswith('robots='):
                    _robots = {r.split(':')[0].strip()
                               for r in sec[len('robots='):].split('|') if r.strip()}
            if _robots is not None:
                cands = [a for a in cands
                         if a.strip('/').split('/')[-1] in _robots]
        else:
            cands = copy.deepcopy(self.agent_list)
        total_agent_list = list(cands)
        total_agent_list.append(self.node_name)
        sorted_list = sorted(total_agent_list, reverse=True)
        print("node name = {0}".format(self.node_name))
        print(sorted_list)
        if sorted_list[0] == self.node_name:
            package = "jnp"
            node = "jnp_group.py"   # (구 testgroup.py — 0.8.1에서 개명)
            # 0.8.1: 그룹 이름 = goal 기반 (예: Relay → group_relay).
            # task 없이 만들어지는 경우(auto_group)만 기존 testgroup 유지
            if goal:
                import re as _re
                name = "group_" + _re.sub(r'[^A-Za-z0-9_]', '_', goal).lower()
                # goal별 그룹: payload 의 첫 goal 라벨(G1 등)을 그룹명에 붙여 구분
                for sec in (payload or '').split(';'):
                    sec = sec.strip()
                    if sec.startswith('goals='):
                        first = sec[len('goals='):].split('|')[0].split(':')[0].strip()
                        if first:
                            name += "_" + _re.sub(r'[^A-Za-z0-9_]', '_', first).lower()
                        break
            else:
                name = "testgroup"
            #command = ["rosrun", package, node,"__name:=" + name]
            command = ["rosrun", package, node,f"__name:={name}"]
            if goal:
                # coalition의 goal/payload 를 그룹 노드 param 으로 전달
                command.append(f"_goal:={goal}")
                if payload:
                    command.append(f"_task_payload:={payload}")

            print(command)
        #subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # stdout을 읽는 스레드 시작
            threading.Thread(target=self.read_output, args=(process.stdout,), daemon=True).start()

            # stderr를 읽는 스레드 시작
            threading.Thread(target=self.read_output, args=(process.stderr,), daemon=True).start()

            # 프로세스가 종료될 때까지 대기
            process.wait()
            # thread2 = threading.Thread(target=self.output_thread,args=(process,))
            # thread2.start()
            #stdout, stderr = process.communicate(timeout=10)
            #stdout, stderr = process.communicate()
            # 실시간으로 출력 확인
            # try:
            #     while True:
            #         output = process.stdout.readline()
            #         if output == b'' and process.poll() is not None:
            #             break
            #         if output:
            #             print(output.decode().strip())

            #     # 오류 출력도 확인
            #     err = process.stderr.read()
            #     if err:
            #         print("Error Output:", err.decode())
            # except KeyboardInterrupt:
            #     print("Process interrupted")
            #     process.terminate()
        # 결과 출력
            #print(stdout.decode())
            #print("Standard Error:", stderr.decode())
            print("--- end of make_group ---")


    def output_thread(self, process):
        try:
            while True:
                output = process.stdout.readline()
                if output == b'' and process.poll() is not None:
                    print("Output Break~~~~~~~~~~~~~~~~~~~~~~~")
                    break
                if output:
                    print(output.decode().strip())

            # 오류 출력도 확인
            err = process.stderr.read()
            if err:
                print("Error Output:", err.decode())
        except KeyboardInterrupt:
            print("Process interrupted")
            process.terminate()
        #stdout, stderr = process.communicate()
        #print(stdout.decode())
        #print("Standard Error:", stderr.decode())

    def input_thread(self):
        while not rospy.is_shutdown():
        # 사용자 입력 대기
            user_input = input("Press 'q' to shut down the node or 'g' for grouping: ")
        # 'q'가 입력되면 노드 종료
            if user_input == 'q':
                node_name = rospy.get_name()
                message = f"kill:{node_name}"
                rospy.loginfo(message)
                self.publisher.publish(message)
                rospy.signal_shutdown("User requested shutdown.")
                sys.exit(0)
            elif user_input == 'g':
                self.make_group()

#    def check_new():

    def _items_cb(self, msg):
        try:
            g, left, xy = msg.data.split(':', 2)
            x, y = [float(v) for v in xy.split(',')[:2]]
            self._goal_items[g.strip()] = (int(left), x, y)
        except (ValueError, IndexError):
            pass

    def _transfer_groups(self, old_group, exclude):
        """그룹 간 이적: 방출된 그룹 탈퇴와 동시에, /goal_items 에서 물품이 남은
        goal 을 ETA(거리÷속도) 기준으로 골라 그 그룹에 가입(mgjoin)한다.
        (원 스펙: 한 goal 소진 시 그 로봇들을 다른 goal 로 이동 — 그룹 경계 확장판)"""
        import math
        _og = old_group.strip('/')
        self.group_list = [g for g in self.group_list if g.strip('/') != _og]
        for _ in range(10):                 # /goal_items latch 수신 대기 (보통 즉시)
            if self._goal_items:
                break
            time.sleep(0.3)
        cands = {g: v for g, v in self._goal_items.items()
                 if v[0] > 0 and g not in exclude}
        if not cands:
            print(f"[이적] {old_group} 탈퇴 — 물품 남은 다른 goal 없음 (대기)", flush=True)
            return
        try:
            from nav_msgs.msg import Odometry
            robot = self.node_name.strip('/').split('/')[-1]
            odom = rospy.wait_for_message('/%s/odom' % robot, Odometry, timeout=5.0)
            mx, my_ = odom.pose.pose.position.x, odom.pose.pose.position.y
        except Exception:
            mx = my_ = 0.0
        speed = self._robot_speed()
        g = min(cands, key=lambda k: math.hypot(cands[k][1] - mx,
                                                cands[k][2] - my_) / max(speed, 0.05))
        print(f"[이적] {old_group} → group_mult_goal_{g.lower()}"
              f" (남은 {cands[g][0]}개, 탈퇴와 동시 가입)", flush=True)
        msg = f"mgjoin:{g}:{self.node_name}:{mx:.2f},{my_:.2f}"
        self.publisher.publish(msg)
        time.sleep(0.5)
        self.publisher.publish(msg)         # 유실 대비 재발행 (그룹이 중복 등록 차단)

    def execute(self, goal):
        # 0.8.1: command = "execute:<task이름>:<goal>" — goal 이 'nav:x,y[,yaw]' 면
        # move_base 실주행, 그 외(데모 goal)는 기존 스텁(2~5초 대기) 유지
        # ★ 어떤 태스크든 시작하면 이 로봇의 '주행 소유권' 세대를 올린다 —
        #   은퇴 대기(자리 비켜주기) 스레드가 남아 새 태스크의 목표를 밀어내는
        #   사고 방지 (탐사 외 태스크도 반드시 포함).
        self._standby_gen = getattr(self, '_standby_gen', 0) + 1
        result = AgentActionResult()
        parts = (goal.command or '').split(':', 2)
        task_goal = parts[2] if len(parts) > 2 else ''
        if task_goal.startswith('nav:'):
            ok = self._drive_nav(task_goal[4:])
            result.result_message = ("completed:" if ok else "failed:") + self.node_name
        elif task_goal.startswith('trip:'):
            # 다목적 이동의 물품 왕복: 현 위치 기억 → goal 이동 → 복귀 (= 물품 1개 소진)
            ok = self._drive_trip(task_goal[5:])
            result.result_message = ("completed:" if ok else "failed:") + self.node_name
        elif task_goal.startswith('cross:'):
            # 충돌회피: 병목 진입점 → 그룹 순서 대기 → 통과 → 목표 영역
            ok = self._drive_cross(task_goal[6:])
            result.result_message = ("completed:" if ok else "failed:") + self.node_name
        elif task_goal.startswith('explore') or task_goal.startswith('search'):
            # 지도제작 v3: 지속 탐사 루프 — 그룹 피더의 목표를 추종, done 방송까지
            ok = self._explore_loop()
            result.result_message = ("completed:" if ok else "failed:") + self.node_name
        else:
            time.sleep(random.uniform(2, 5))
            result.result_message = "completed:" + self.node_name
        feedback = AgentActionFeedback()  # 피드백 객체 생성
        feedback.feedback_message = f"The content of {goal.command} in {self.node_name} is {result.result_message}"
        self.server.publish_feedback(feedback)
        rospy.loginfo(result.result_message)
        print(f"Action::: The content of {goal.command} in {self.node_name} is {result.result_message}")

        self.server.set_succeeded(result)

    def _task_base_cb(self, msg):
        self._task_base = (msg.pose.position.x, msg.pose.position.y)

    # ── 존-토큰 교통관제 클라이언트 (traffic_zones.py) ──
    # 좁은 구역(base 원, goal 주변)의 '이동'을 존마다 1대로 직렬화.
    # 노드/서비스가 없으면 무-관제로 진행 (반환 True — 기존 동작 유지).
    ZONE_BASE_R = 2.2      # traffic_zones ~base_radius 와 일치
    ZONE_GOAL_R = 2.2      # traffic_zones ~goal_radius 와 일치

    def _zone_wait(self, name, max_iter=90):
        """반환값 = '실제로 토큰을 획득했는가'. 미획득(노드 부재/타임아웃/예외)
        이어도 주행은 진행하지만, 획득 못 한 존은 절대 release 하지 않는다 —
        무토큰 로봇이 남의 토큰을 반납하는 연쇄 차단 (리뷰 #1/#6/#12)."""
        try:
            from std_srvs.srv import Trigger
            try:
                rospy.wait_for_service('/zone_%s/acquire' % name, timeout=1.0)
            except rospy.ROSException:
                return False                    # 관제 노드 없음 — 무-관제 진행
            acq = rospy.ServiceProxy('/zone_%s/acquire' % name, Trigger)
            robot = self.node_name.strip('/').split('/')[-1]
            for i in range(max_iter):
                try:
                    if acq().success:
                        if i:
                            print(f"[교통] {robot}: {name} 존 진입", flush=True)
                        return True
                except rospy.ServiceException:
                    return False                # 관제 이상 — 막지 않음(미획득)
                if i == 0:
                    print(f"[교통] {robot}: {name} 존 대기...", flush=True)
                rospy.sleep(0.5)
            rospy.logwarn('%s 존 대기 시간 초과 — 무-관제 진행(미획득)', name)
            return False
        except Exception as e:
            rospy.logwarn('존 획득 실패(무시): %s', e)
            return False

    def _zone_release(self, name):
        try:
            from std_srvs.srv import Trigger
            rospy.ServiceProxy('/zone_%s/release' % name, Trigger)()
        except Exception:
            pass

    def _zones_for_leg(self, x1, y1, x2, y2):
        """다리의 '목적지'가 속한 존만 반환 (정렬 순서 고정 — 자원 순서화).
        양끝 존 전부 획득은 과직렬화로 전 로봇 정지 체감을 만들었다(2026-08-08
        실측) — 혼잡의 본질은 '붐비는 구역으로의 진입'이므로 도착지 존만 잡고,
        출발지 존 이탈은 위치공유+우선권+시차가 담당한다."""
        import math

        def hit(cx, cy, rr):
            # 출발점이 존 안이면 '출발 존' — 면제 (과직렬화 방지, 이탈은
            # 위치공유+우선권 담당). 그 외에는 선분-원 교차로 관통까지 검사.
            if math.hypot(x1 - cx, y1 - cy) < rr - 0.3:
                return False    # 출발 존 면제 — '진짜 존 안'(엄격 반경)일 때만
            L2 = (x2 - x1) ** 2 + (y2 - y1) ** 2 or 1.0
            t = max(0.0, min(1.0, ((cx - x1) * (x2 - x1)
                                   + (cy - y1) * (y2 - y1)) / L2))
            px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
            return math.hypot(cx - px, cy - py) < rr
        zs = set()
        tb = self._task_base
        if tb and hit(tb[0], tb[1], self.ZONE_BASE_R + 0.3):
            zs.add('base')
        for g, (_left, gx0, gy0) in list(self._goal_items.items()):
            if hit(gx0, gy0, self.ZONE_GOAL_R + 0.3):
                zs.add(g)
        return sorted(zs)

    def _acquire_zones(self, names):
        got = []
        for n in names:                     # 정렬 순서 획득 — 전 클라이언트 동일
            if self._zone_wait(n):
                got.append(n)               # 실제 획득분만 — 그것만 반납 대상
        return got

    def _release_zones(self, names):
        for n in names:
            self._zone_release(n)

    def _solo_avoidance(self, payload):
        """동적 충돌회피(v4): 그룹 없이 전원 병렬 출발. 주행 중 충돌이 '예측'
        되면(거리<2.0m & 접근 중) 그 쌍이 즉석 coalition 을 형성 — 충돌점 ETA
        가 짧은 쪽 우선 통과, 낮은 쪽 일시정지. 통과 확인 시 해산·재개.
        ※ 단순화 명시: 즉석 coalition 은 별도 그룹 노드 없이 우선 로봇이
        /jnp/status 로 형성/해산을 발행하는 경량 합의체 (Monitor 에 표시)."""
        import math
        from nav_msgs.msg import Odometry
        me = self.node_name.strip('/').split('/')[-1]
        try:
            routes = {}
            for sec in payload.split(';'):
                sec = sec.strip()
                if sec.startswith('routes='):
                    for rt in sec[len('routes='):].split('|'):
                        nm, _, rest = rt.partition(':')
                        se, _, ta = rest.partition('>')
                        v = [float(x) for x in (se + ',' + ta).split(',')]
                        routes[nm.strip()] = tuple(v[:4])
            if me not in routes:
                return
            tx, ty = routes[me][2], routes[me][3]
            others = [n for n in routes if n != me]
            pos = {}
            hist = {}
            for n in list(routes):
                rospy.Subscriber(
                    '/%s/odom' % n, Odometry,
                    (lambda n_: lambda m: pos.__setitem__(
                        n_, (m.pose.pose.position.x, m.pose.pose.position.y)))(n))
            plans = {}       # 로봇 → [(x,y), ...] (전역 경로 ~0.5m 간격 다운샘플)
            from nav_msgs.msg import Path as _Path
            for n in list(routes):
                for _pt in ('NavfnROS', 'GlobalPlanner'):
                    rospy.Subscriber(
                        '/%s/move_base/%s/plan' % (n, _pt), _Path,
                        (lambda n_: lambda m: plans.__setitem__(
                            n_, [(q.pose.position.x, q.pose.position.y)
                                 for q in m.poses[::10]]))(n))
            stpub = rospy.Publisher('/jnp/status', String, queue_size=6)
            dispub = rospy.Publisher('/conflict_display', String, queue_size=6)
            import actionlib as al
            from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
            import tf.transformations as tft
            client = al.SimpleActionClient('/%s/move_base' % me, MoveBaseAction)
            if not client.wait_for_server(rospy.Duration(30.0)):
                rospy.logwarn('%s: move_base 없음 — 동적 회피 중단', me)
                return

            def send_goal():
                g = MoveBaseGoal()
                g.target_pose.header.frame_id = 'map'
                g.target_pose.header.stamp = rospy.Time.now()
                g.target_pose.pose.position.x = tx
                g.target_pose.pose.position.y = ty
                cx0, cy0 = pos.get(me, (tx - 1.0, ty))
                yaw = math.atan2(ty - cy0, tx - cx0)
                q = tft.quaternion_from_euler(0, 0, yaw)
                g.target_pose.pose.orientation.x = q[0]
                g.target_pose.pose.orientation.y = q[1]
                g.target_pose.pose.orientation.z = q[2]
                g.target_pose.pose.orientation.w = q[3]
                client.send_goal(g)
            rospy.sleep(1.5)
            send_goal()
            print(f"[동적회피] {me}: 병렬 출발 → ({tx:.2f},{ty:.2f})", flush=True)
            prev_d = {}
            paused = {}
            group_open = {}
            cooldown = {}
            speed = self._robot_speed()

            def spd(n):
                if 'locobot' in n:
                    return 0.4
                return 0.2 if ('tb3' in n or 'burger' in n) else 0.3

            def ahead(path, cur):
                """경로에서 현재 위치 최근접점 이후 구간 + 누적거리."""
                if not path:
                    return []
                k0 = min(range(len(path)),
                         key=lambda k: (path[k][0] - cur[0]) ** 2
                         + (path[k][1] - cur[1]) ** 2)
                seg = path[k0:]
                out = []
                acc = 0.0
                for i2, pt in enumerate(seg):
                    if i2:
                        acc += math.hypot(pt[0] - seg[i2 - 1][0],
                                          pt[1] - seg[i2 - 1][1])
                    out.append((pt[0], pt[1], acc))
                return out

            def predict_cross(o, mypos, opos):
                """경로 교차 예측: 두 전역 경로가 0.7m 이내로 겹치는 지점에
                비슷한 시각(차<6s)에 도달하면 (교차점, 내ETA, 상대ETA) 반환."""
                pa = ahead(plans.get(me), mypos)
                pb = ahead(plans.get(o), opos)
                if len(pa) < 2 or len(pb) < 2:
                    return None
                best = None
                for ax, ay, sa in pa:
                    ta = sa / max(speed, 0.05)
                    if ta > 20.0:
                        break
                    for bx, by, sb in pb:
                        tb = sb / max(spd(o), 0.05)
                        if tb > 20.0:
                            break
                        if math.hypot(ax - bx, ay - by) < 0.7                                 and abs(ta - tb) < 6.0:
                            if best is None or max(ta, tb) < best[3]:
                                best = ((ax + bx) / 2.0, (ay + by) / 2.0,
                                        ta, max(ta, tb), tb)
                    if best is not None:
                        break
                if best is None:
                    return None
                return (best[0], best[1]), best[2], best[4]

            # ── 미션 트리 (2026-08-11 지시) ─────────────────────────────
            # 쌍마다 별도 coalition 트리를 그리던 방식 폐기. 태스크의 실체는
            # '로봇별 go_to_goal 병렬 수행'이고, 병목 처리(pass/yield)는 그
            # 수행 '도중' 일어나는 하위 동작이므로 각 로봇 가지에 접붙인다
            # (물건찾기 트리와 동일한 규약). 이름이 가장 앞선 로봇 1대만 발행
            # — 여럿이 같은 group 이름으로 발행하면 부분 정보끼리 덮어쓴다.
            _leader = min(routes)
            _pairs = {}          # '<a>_<b>' → {'high': 우선, 'low': 양보}

            def _conf_cb(m):
                """다른 로봇들이 발행하는 /conflict_display 로 전체 쌍 상태 파악.
                (쌍은 우선 로봇만 발행 — ranks 비면 해소)"""
                try:
                    d = json.loads(m.data)
                except Exception:
                    return
                k, rk = d.get('group'), (d.get('ranks') or {})
                if not k:
                    return
                if not rk:
                    _pairs.pop(k, None)
                    return
                hi = [n for n, v in rk.items() if int(v) == 1]
                lo = [n for n, v in rk.items() if int(v) != 1]
                if hi and lo:
                    _pairs[k] = {'high': hi[0], 'low': lo[0]}

            if me == _leader:
                rospy.Subscriber('/conflict_display', String, _conf_cb,
                                 queue_size=8)

            def _mission_tree():
                """avoidance[P] → 로봇별 move.<n>[P] → go_to_goal.<n>(+pass/yield)"""
                waiting = {v['low'] for v in _pairs.values()}
                kids, alldone = [], True
                for n in sorted(routes):
                    p_ = pos.get(n)
                    txn, tyn = routes[n][2], routes[n][3]
                    dn = bool(p_) and math.hypot(p_[0] - txn, p_[1] - tyn) < 0.5
                    alldone = alldone and dn
                    ch = [{'name': 'go_to_goal.%s' % n,
                           'goal': 'nav:%.2f,%.2f' % (txn, tyn), 'kind': 'atomic',
                           'agent': '/etri/' + n,
                           # 양보 중이면 'wait' — 실제로 목표가 취소된 상태
                           'state': 'done' if dn else
                                    ('wait' if n in waiting else 'running')}]
                    for v in _pairs.values():
                        if v['high'] == n:      # 내가 먼저 통과 — 상대를 지나침
                            ch.append({'name': 'pass.%s' % v['low'],
                                       'goal': 'nav:cross', 'kind': 'atomic',
                                       'agent': '/etri/' + n, 'state': 'running'})
                        elif v['low'] == n:     # 내가 양보 — 상대가 지날 때까지
                            ch.append({'name': 'yield.%s' % v['high'],
                                       'goal': 'virtual:hold', 'kind': 'atomic',
                                       'agent': '/etri/' + n, 'state': 'running'})
                    kids.append({'name': 'move.%s' % n, 'kind': 'par',
                                 'state': 'done' if dn else '', 'children': ch})
                return ({'name': 'avoidance', 'goal': 'Avoidance', 'kind': 'par',
                         'state': 'done' if alldone else '',
                         'children': kids}, alldone)

            def _pub_mission(state='running', note=''):
                tr, alldone = _mission_tree()
                try:
                    stpub.publish(json.dumps(
                        {'group': '/coalition_avoidance', 'state': state,
                         'goal': 'Avoidance',
                         'members': [{'name': '/etri/' + n, 'cap': []}
                                     for n in sorted(routes)],
                         'tree': tr, 'stamp': rospy.get_time(), 'note': note}))
                except Exception as _pe:
                    rospy.logwarn('미션 트리 발행 실패: %s', _pe)
                return alldone

            def form_conflict(o, mid, my_eta, o_eta, how, dinfo):
                i_high = ((round(my_eta * 2) / 2.0, me)
                          < (round(o_eta * 2) / 2.0, o))
                key = '_'.join(sorted([me, o]))
                now2 = rospy.get_time()
                if i_high:
                    # (쌍별 coalition 발행 폐기 — 미션 트리에 가지로 접붙는다)
                    try:
                        dispub.publish(json.dumps(
                            {'group': key, 'ranks': {me: 1, o: 2},
                             'mid': [round(mid[0], 2), round(mid[1], 2)]}))
                    except Exception:
                        pass
                    print(f"[동적회피] {how}({dinfo}): coalition {key}"
                          f" 형성 — 우선 {me}", flush=True)
                    group_open[o] = {'mid': mid, 't': now2}
                else:
                    print(f"[동적회피] {how}({dinfo}): {o} 우선 — {me} 일시정지",
                          flush=True)
                    client.cancel_all_goals()
                    paused[o] = {'mid': mid, 't': now2}

            retry_n = 0
            _arrived, _arr_t, _last_pub = False, 0.0, 0.0
            while not rospy.is_shutdown():
                rospy.sleep(0.7)
              # 반복별 가드 — 한 번의 예외가 회피 루프 전체를 죽이지 않게
                try:
                    mypos = pos.get(me)
                    if mypos is None:
                        continue
                    now = rospy.get_time()
                    # 미션 트리 주기 발행 (리더 1대) — 전원 도착이면 완료 발행
                    if me == _leader and now - _last_pub > 1.5:
                        _last_pub = now
                        if _mission_tree()[1]:
                            _pub_mission('success', '전원 목표 도착')
                            print('[동적회피] 전 로봇 목표 도착 — 미션 완료',
                                  flush=True)
                            return
                        _pub_mission('running',
                                     ('병목 처리 중: ' + ', '.join(sorted(_pairs)))
                                     if _pairs else '전원 이동 중')
                        # 도착 후 무한 대기 방지 (상대가 영영 안 오는 경우)
                        if _arrived and now - _arr_t > 300.0:
                            _pub_mission('success', '리더 대기 시간 초과 — 종료')
                            return
                    # move_base 포기(ABORTED 등) 감지 → 재전송 (벽 걸림 회복)
                    if not paused and not _arrived:
                        stt = client.get_state()
                        if stt in (4, 5, 9) and retry_n < 8:   # ABORTED/REJECTED/LOST
                            retry_n += 1
                            rospy.logwarn('%s: move_base 포기(%d) — 재전송 %d/8',
                                          me, stt, retry_n)
                            rospy.sleep(2.0)
                            send_goal()
                            continue
                    for n, p_ in pos.items():           # 정지 감지용 이력
                        h = hist.setdefault(n, [])
                        h.append((now, p_[0], p_[1]))
                        hist[n] = [e for e in h if now - e[0] <= 5.0]
                    if math.hypot(mypos[0] - tx, mypos[1] - ty) < 0.45 and not paused:
                        if me != _leader:
                            print(f"[동적회피] {me}: 목표 도착", flush=True)
                            return
                        if not _arrived:
                            _arrived, _arr_t = True, now
                            print(f"[동적회피] {me}: 목표 도착 — 미션 트리 발행 유지",
                                  flush=True)
                        continue        # 도착한 리더는 병목 로직 없이 발행만
                    for o in others:
                        op = pos.get(o)
                        if op is None or now < cooldown.get(o, 0) or o in paused \
                                or o in group_open:
                            continue
                        if math.hypot(op[0] - routes[o][2], op[1] - routes[o][3]) < 0.5:
                            continue                    # 상대는 이미 도착 — 무시
                        dme = math.hypot(mypos[0] - op[0], mypos[1] - op[1])
                        closing = prev_d.get(o, 99.0) - dme > 0.02
                        prev_d[o] = dme
                        # ①경로 교차 예측 (전역 경로 기반 — 마주치기 전에 미리)
                        pc = predict_cross(o, mypos, op)
                        if pc is not None:
                            mid, my_eta, o_eta = pc
                            form_conflict(o, mid, my_eta, o_eta,
                                          '경로교차 예측',
                                          f'{my_eta:.0f}s/{o_eta:.0f}s')
                            continue
                        # ②근접 감지 (안전망): 2.0m 이내 + 접근 중
                        if dme >= 2.0 or not closing:
                            continue
                        mid = ((mypos[0] + op[0]) / 2.0, (mypos[1] + op[1]) / 2.0)
                        my_eta = dme / 2.0 / max(speed, 0.05)
                        o_eta = dme / 2.0 / max(spd(o), 0.05)
                        form_conflict(o, mid, my_eta, o_eta, '충돌 예측',
                                      f'{dme:.1f}m')
                    # ── (일시정지 측) 해소 판정: 상대 통과/이탈/도착 ──
                    for o in list(paused):
                        op = pos.get(o)
                        mid = paused[o]['mid']
                        o_mid = math.hypot(op[0] - mid[0], op[1] - mid[1]) if op else 99
                        # ★조기 재개 봉쇄(2026-08-09 충돌 원인): 예측 형성 시점엔
                        # 상대가 아직 교차점에서 멀다 — '병목에 들어왔다(1.0m)
                        # 나감(1.6m)'을 확인해야 통과로 인정
                        if o_mid < 1.0:
                            paused[o]['seen'] = True
                        o_passed = paused[o].get('seen') and o_mid > 1.6
                        o_done = op and math.hypot(op[0] - routes[o][2],
                                                   op[1] - routes[o][3]) < 0.5
                        # 동시양보 안전탈출: 상대도 4초째 정지면 이름 우선으로 재개
                        o_h = hist.get(o, [])
                        o_still = (len(o_h) > 3 and
                                   math.hypot(o_h[-1][1] - o_h[0][1],
                                              o_h[-1][2] - o_h[0][2]) < 0.10)
                        mutual_stall = ((now - paused[o]['t'] > 6.0 and o_still
                                         and me < o)
                                        or (now - paused[o]['t'] > 45.0 and o_still))
                        hard_timeout = now - paused[o]['t'] > 120.0
                        if o_done or o_passed or mutual_stall or hard_timeout:
                            if mutual_stall:
                                print(f"[동적회피] {me}: 동시양보 감지 — 이름 우선 재개",
                                      flush=True)
                            else:
                                print(f"[동적회피] {me}: {o} 통과 확인 — 재개", flush=True)
                            cooldown[o] = now + 12.0
                            del paused[o]
                            prev_d.pop(o, None)
                            try:    # 표시 정리 (해산 발행 유실 대비 — 양쪽 모두 해제)
                                dispub.publish(json.dumps(
                                    {'group': '_'.join(sorted([me, o])), 'ranks': {}}))
                            except Exception:
                                pass
                            if not paused:
                                send_goal()
                    # ── (우선 측) 해산 판정: 내가 충돌점을 지나 멀어짐 ──
                    for o in list(group_open):
                        op = pos.get(o)
                        mid = group_open[o]['mid']
                        my_mid = math.hypot(mypos[0] - mid[0], mypos[1] - mid[1])
                        if my_mid < 1.0:
                            group_open[o]['seen'] = True
                        i_passed = group_open[o].get('seen') and my_mid > 1.6
                        my_done = math.hypot(mypos[0] - tx, mypos[1] - ty) < 0.5
                        if i_passed or my_done or now - group_open[o]['t'] > 120:
                            key = '_'.join(sorted([me, o]))
                            print(f"[동적회피] 병목 해소 {key} — 가지 제거", flush=True)
                            try:
                                dispub.publish(json.dumps({'group': key, 'ranks': {}}))
                            except Exception:
                                pass
                            cooldown[o] = now + 12.0
                            del group_open[o]
                except Exception as _le:
                    rospy.logwarn('동적 회피 반복 오류(%s): %s — 계속', me, _le)
        except Exception as e:
            rospy.logwarn('동적 회피 오류(%s): %s', me, e)
        finally:
            self._av_running = False

    def _drive_cross(self, spec):
        """충돌회피(Avoidance) 태스크: '진입x,y;이탈x,y;목표x,y[@bt]'.
        ① 병목 진입 대기점 → ② 그룹(/bottleneck)이 정한 순서 대기
        — 앞 로봇이 병목을 '지난 후'에만 허가 → ③ 병목 통과(이탈점)
        → ④ 통과 보고 → ⑤ 목표 영역으로 이동."""
        if '@' in spec:
            spec, _tag = spec.split('@', 1)
        try:
            e_s, x_s, t_s = spec.split(';')
            ex, ey = [float(v) for v in e_s.split(',')[:2]]
            xx, xy = [float(v) for v in x_s.split(',')[:2]]
            tx, ty = [float(v) for v in t_s.split(',')[:2]]
        except (ValueError, IndexError) as e:
            rospy.logwarn('cross: 형식 오류: %s', e)
            return False
        robot = self.node_name.strip('/').split('/')[-1]
        # ① 진입 대기점
        if not self._drive_nav(f"{ex:.2f},{ey:.2f}"):
            return False
        # ② 순서 대기 (그룹 서비스 부재 시 무-관제 진행)
        acquired = False
        controlled = True
        try:
            from std_srvs.srv import Trigger
            try:
                rospy.wait_for_service('/bottleneck/acquire', timeout=10.0)
            except rospy.ROSException:
                controlled = False
            if controlled:
                acq = rospy.ServiceProxy('/bottleneck/acquire', Trigger)
                for i in range(600):            # 최대 600 sim초
                    try:
                        r = acq()
                    except rospy.ServiceException:
                        rospy.sleep(1.0)        # 일시 예외 — 무허가 통과 금지, 재시도
                        continue
                    if r.success:
                        acquired = True
                        print(f"[회피] {robot}: 병목 통과 허가", flush=True)
                        break
                    if i % 10 == 0:
                        print(f"[회피] {robot}: 병목 순서 대기 ({r.message})",
                              flush=True)
                    rospy.sleep(1.0)
                if not acquired:
                    rospy.logwarn('%s: 병목 대기 시간 초과 — task 실패 처리', robot)
                    return False
        except Exception as e:
            rospy.logwarn('병목 제어 실패(무-관제 진행): %s', e)
        # ③ 병목 통과 → ④ 보고: 성공=release(통과 확정), 실패=abort(순서 뒤로 반납)
        ok = False
        try:
            ok = self._drive_nav(f"{xx:.2f},{xy:.2f}")
        finally:
            if acquired:
                try:
                    from std_srvs.srv import Trigger
                    svc = '/bottleneck/release' if ok else '/bottleneck/abort'
                    rospy.ServiceProxy(svc, Trigger)()
                except Exception:
                    pass
        if not ok:
            return False
        # ⑤ 목표 영역
        return self._drive_nav(f"{tx:.2f},{ty:.2f}")

    def _drive_trip(self, spec):
        """다목적 이동 왕복: 'x,y[@G이름]' — goal 자체가 목적지.
        절차: ① goal 근처 대기점으로 접근 → ② 그룹의 진입 허가(순서 제어) 획득
        → ③ goal 도달 → ④ 허가 반납 → ⑤ 출발 지점 복귀 (복귀까지 되면 물품 1개)."""
        gname = ''
        if '@' in spec:
            spec, gname = spec.split('@', 1)
        try:
            import math
            from nav_msgs.msg import Odometry
            robot = self.node_name.strip('/').split('/')[-1]
            odom = rospy.wait_for_message('/%s/odom' % robot, Odometry, timeout=5.0)
            hx = odom.pose.pose.position.x
            hy = odom.pose.pose.position.y
            if getattr(self, '_mg_home', None):
                hx, hy = self._mg_home   # 항상 베이스 자리로 복귀 (이적 후에도)
            vals = [float(v) for v in spec.split(',')[:2]]
            gx, gy = vals[0], vals[1]
        except Exception as e:
            rospy.logwarn('trip: 시작 정보 확인 실패: %s', e)
            return False
        # ⓪ 출발 시차: 첫 trip 만 로봇별 0~3.6초 — 베이스 동시 출발 교차 대치 완화
        if not getattr(self, '_trip_started', False):
            self._trip_started = True
            import hashlib as _hl
            stag = (int(_hl.md5(robot.encode()).hexdigest()[:2], 16) % 4) * 1.2
            if stag:
                print(f"trip: 출발 시차 {stag:.1f}s(sim)", flush=True)
                rospy.sleep(stag)
        # ① 대기점: goal 에서 출발 방향으로 1.3m 앞 + 로봇별 횡방향 오프셋(병목 완화)
        dx, dy = gx - hx, gy - hy
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        # 부채꼴 대기(2026-08-08): 일렬 줄이 goal 출입 통로를 막던 것을,
        # goal 중심 반경 1.7m 원호의 로봇별 방위(±25°/±75°, 직선 통로 비움)로 분산
        slot = getattr(self, '_mg_slot', sum(ord(c) for c in robot) % 4)
        ang = math.atan2(-uy, -ux) + math.radians((-25, 25, -75, 75)[slot])
        wx = gx + 1.7 * math.cos(ang)
        wy = gy + 1.7 * math.sin(ang)
        # ①-a 출발 다리(home→부채꼴 대기점): 걸치는 존 전부 고정 순서 획득
        #    (이동 중에만 보유 — 도착=정지 후 즉시 반납. 정지 로봇은 토큰 불요)
        zs = self._zones_for_leg(hx, hy, wx, wy)
        held1 = self._acquire_zones(zs)
        ok1 = self._drive_nav(f"{wx:.2f},{wy:.2f}")
        self._release_zones(held1)
        if not ok1:
            return False
        # ② 진입 허가 — goal 그룹이 관리 (goal 점유는 한 번에 1대)
        acquired = False
        if gname:
            try:
                from std_srvs.srv import Trigger
                acq = rospy.ServiceProxy('/goal_entry_%s/acquire' % gname, Trigger)
                for _ in range(90):             # 최대 ~3분 대기
                    try:
                        if acq().success:
                            acquired = True
                            break
                    except rospy.ServiceException:
                        pass
                    print(f"[JnP-NAV] {robot}: {gname} 진입 대기...", flush=True)
                    rospy.sleep(2.0)
                if not acquired:
                    return False
            except Exception as e:
                rospy.logwarn('진입 허가 실패(무시하고 진행): %s', e)
        # ③ goal 자체 도달 — 진입락(/goal_entry)이 이미 1대 직렬화하므로 존 생략
        ok = self._drive_nav(spec)

        def _entry_release():
            if gname and acquired:
                try:
                    from std_srvs.srv import Trigger
                    rospy.ServiceProxy('/goal_entry_%s/release' % gname,
                                       Trigger)()
                except Exception:
                    pass
        if not ok:
            _entry_release()
            return False
        # ⑤ 복귀 존을 '진입락 보유 중' 확보한 뒤 반납 — goal 점유 중 다음 로봇
        #    진입 방지 (리뷰 #8/#13). 교착 없음: 진입락 대기자는 존 토큰 비보유.
        zs3 = self._zones_for_leg(gx, gy, hx, hy)
        held3 = self._acquire_zones(zs3)
        _entry_release()
        ok3 = self._drive_nav(f"{hx:.2f},{hy:.2f}")
        self._release_zones(held3)
        return ok3

    def _explore_loop(self):
        """지도제작 v3 지속 탐사 + v4 병목 처리 이식 (2026-08-09 사용자 지시).

        목표 추종: 그룹 피더의 /explore_target/<robot>(latched) 를 계속 따라감.
        병목 처리(충돌회피 v4 코어 이식): 전역 경로 교차 예측(0.7m/6s/20s) +
        근접 안전망(2.0m 접근) → 즉석 coalition(ETA 짧은 쪽 우선, 낮은 쪽 정지)
        → '병목 진입(1.0m)→이탈(1.6m)' 확인 후 해소 — Monitor(/jnp/status)와
        RViz/Gazebo(/conflict_display: 순위 숫자+병목 사각형)에 그대로 표시."""
        try:
            from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
            from geometry_msgs.msg import PoseStamped as _PS
            from std_msgs.msg import Bool as _Bool
            from std_msgs.msg import String as _Str
            from nav_msgs.msg import Path as _Path
            import tf.transformations as tft
            import math as _m
            robot = self.node_name.strip('/').split('/')[-1]
            state = {'tgt': None, 'done': False, 'peers': []}
            _s1 = rospy.Subscriber(
                '/explore_target/%s' % robot, _PS,
                lambda m: state.__setitem__(
                    'tgt', (m.pose.position.x, m.pose.position.y)),
                queue_size=2)
            def _all_done_cb(m):
                state['done'] = bool(m.data)
                if m.data:
                    state['all_done'] = True   # 미션 전체 종료 — 대기 모드도 끝
            _s2 = rospy.Subscriber('/explore_done', _Bool, _all_done_cb,
                                   queue_size=2)
            def _mine_done_cb(m):
                state['done'] = bool(m.data)
                if m.data:
                    state['mine_done'] = True      # 은퇴(내 몫 소진) — 대기 모드
            _s2b = rospy.Subscriber('/explore_done/%s' % robot, _Bool,
                                    _mine_done_cb, queue_size=2)

            def _grp_cb(m):
                try:
                    _, names = m.data.split(':', 1)
                    state['peers'] = [x.strip() for x in names.split(',')
                                      if x.strip() and x.strip() != robot]
                except ValueError:
                    pass
            _s3 = rospy.Subscriber('/mutual_obstacles/set_group', _Str,
                                   _grp_cb, queue_size=2)
            import tf2_ros as _tf2
            _buf = _tf2.Buffer(rospy.Duration(10.0))
            _lis = _tf2.TransformListener(_buf)
            client = actionlib.SimpleActionClient('/%s/move_base' % robot,
                                                  MoveBaseAction)
            if not client.wait_for_server(rospy.Duration(20.0)):
                rospy.logwarn('%s: move_base 서버 없음 — 탐사 불가', robot)
                return False

            # ── v4 병목 처리 엔진 상태 ──
            _pos, _plans, _hist = {}, {}, {}
            _prevd, _paused, _gopen, _cool = {}, {}, {}, {}
            _plan_sub = {}
            _stpub = rospy.Publisher('/jnp/status', _Str, queue_size=6)
            _dispub = rospy.Publisher('/conflict_display', _Str, queue_size=6)
            from geometry_msgs.msg import Twist as _Tw
            _cvpub = rospy.Publisher('/%s/cmd_vel' % robot, _Tw, queue_size=2)
            _jam_since, _jam_cool = 0.0, -1e9
            _fail_n = 0
            _esc_rev = True     # 탈출 방향 교대용 (True=후진부터)
            # ★ 양보 즉시 재개 (2026-08-11): 지금까지 정지한 쪽은 '상대가 병목에
            #   들어왔다(1.0m)→나갔다(1.6m)'를 자기 눈으로 확인해야만 재개했다.
            #   예측이 빗나가 상대가 그 근처를 안 지나가면 45~120초 타임아웃까지
            #   죽은 듯 서 있게 된다(waffle 25초+ 정지 실측). 우선 로봇이 이미
            #   /conflict_display 로 해소를 방송하므로, 그걸 받으면 곧바로 푼다.
            # 새 태스크가 시작되면 이전 '대기 모드' 스레드가 로봇을 몰지 않도록
            # 세대 번호로 무효화한다 (좀비 스레드가 goal 을 쏘는 사고 방지)
            _my_gen = getattr(self, '_standby_gen', 0)
            _resume = {'keys': {}}

            def _res_cb(m):
                try:
                    d = json.loads(m.data)
                except (ValueError, TypeError):
                    return
                if d.get('ranks'):
                    return                     # 형성 통지 — 해소만 처리
                if d.get('src') != 'priority':
                    return                     # 표시용/양보측 신호는 무시
                if d.get('by') == robot:
                    return                     # 내가 낸 방송 — 자기 재개 금지
                k = d.get('group') or ''
                # 키 형식 = '_'.join(sorted([a, b])) — 로봇 이름 자체에 '_' 가
                # 있으므로 split('_') 로는 복원 불가 (접두/접미로 판정)
                if k.startswith(robot + '_') or k.endswith('_' + robot):
                    _resume['keys'][k] = rospy.get_time()
            _s4 = rospy.Subscriber('/conflict_display', _Str, _res_cb,
                                   queue_size=8)
            _speed = self._robot_speed()

            def _spd(n):
                if 'locobot' in n:
                    return 0.4
                return 0.2 if ('tb3' in n or 'burger' in n) else 0.3

            def _sub_plans(n):
                if n in _plan_sub:
                    return
                _plan_sub[n] = [rospy.Subscriber(
                    '/%s/move_base/%s' % (n, tp), _Path,
                    (lambda n_: lambda m: _plans.__setitem__(
                        n_, [(q.pose.position.x, q.pose.position.y)
                             for q in m.poses[::10]]))(n))
                    for tp in ('NavfnROS/plan', 'GlobalPlanner/plan',
                               'DWAPlannerROS/global_plan')]

            def _ahead(path, cur_):
                if not path:
                    return []
                k0 = min(range(len(path)),
                         key=lambda k: (path[k][0] - cur_[0]) ** 2
                         + (path[k][1] - cur_[1]) ** 2)
                seg = path[k0:]
                out, acc = [], 0.0
                for i2, pt in enumerate(seg):
                    if i2:
                        acc += _m.hypot(pt[0] - seg[i2 - 1][0],
                                        pt[1] - seg[i2 - 1][1])
                    out.append((pt[0], pt[1], acc))
                return out

            def _predict(o, mypos, opos):
                pa = _ahead(_plans.get(robot), mypos)
                pb = _ahead(_plans.get(o), opos)
                if len(pa) < 2 or len(pb) < 2:
                    return None
                best = None
                for ax, ay, sa in pa:
                    ta = sa / max(_speed, 0.05)
                    if ta > 20.0:
                        break
                    for bx, by, sb in pb:
                        tb = sb / max(_spd(o), 0.05)
                        if tb > 20.0:
                            break
                        if (_m.hypot(ax - bx, ay - by) < 0.7
                                and abs(ta - tb) < 6.0):
                            if best is None or max(ta, tb) < best[3]:
                                best = ((ax + bx) / 2.0, (ay + by) / 2.0,
                                        ta, max(ta, tb), tb)
                    if best is not None:
                        break
                if best is None:
                    return None
                return (best[0], best[1]), best[2], best[4]

            def _ctree(key, high, low, st):
                done = st == 'success'
                return {'name': 'avoid_%s' % key, 'goal': 'AvoidConflict',
                        'kind': 'par', 'state': 'done' if done else '',
                        'children': [
                            {'name': f'pass.{high}', 'goal': 'nav:cross',
                             'kind': 'atomic', 'agent': '/etri/' + high,
                             'state': 'done' if done else 'running'},
                            {'name': f'yield.{low}', 'goal': 'virtual:hold',
                             'kind': 'atomic', 'agent': '/etri/' + low,
                             'state': 'done' if done else 'running'}]}

            def _form(o, mid, my_eta, o_eta, how, dinfo):
                i_high = ((round(my_eta * 2) / 2.0, robot)
                          < (round(o_eta * 2) / 2.0, o))
                key = '_'.join(sorted([robot, o]))
                now2 = rospy.get_time()
                if i_high:
                    try:
                        # 별도 coalition 발행 대신 /conflict_display 만 —
                        # 트리 표시는 미션 그룹이 root 아래 avoid_* 가지로 흡수
                        # (2026-08-10 지시: 병목은 미션과 병렬 가지가 맞다)
                        _dispub.publish(json.dumps(
                            {'group': key, 'ranks': {robot: 1, o: 2},
                             'mid': [round(mid[0], 2), round(mid[1], 2)]}))
                    except Exception:
                        pass
                    print(f"[탐사-병목] {how}({dinfo}): coalition {key}"
                          f" — 우선 {robot}", flush=True)
                    _gopen[o] = {'mid': mid, 't': now2}
                else:
                    print(f"[탐사-병목] {how}({dinfo}): {o} 우선 — {robot} 정지",
                          flush=True)
                    try:
                        client.cancel_all_goals()
                    except Exception:
                        pass
                    _paused[o] = {'mid': mid, 't': now2}

            cur = None
            _last_send = 0.0
            print(f"[JnP-EXPLORE] {robot} 탐사 루프 시작 (병목 처리 v4 이식)",
                  flush=True)
            while not rospy.is_shutdown() and not state['done']:
                try:
                    rospy.sleep(1.0)
                except rospy.ROSInterruptException:
                    break
                now = rospy.get_time()
                # 위치 갱신 (TF) + 경로 구독 보장
                for n in [robot] + state['peers']:
                    _sub_plans(n)
                    try:
                        tr = _buf.lookup_transform(
                            'map', '%s/base_footprint' % n, rospy.Time(0))
                        _pos[n] = (tr.transform.translation.x,
                                   tr.transform.translation.y)
                    except Exception:
                        pass
                mypos = _pos.get(robot)
                if mypos is not None:
                    for n, p_ in _pos.items():
                        h = _hist.setdefault(n, [])
                        h.append((now, p_[0], p_[1]))
                        _hist[n] = [e for e in h if now - e[0] <= 5.0]
                    # ── 충돌 감지 (예측 + 근접 안전망) ──
                    if not _paused:
                        for o in state['peers']:
                            op = _pos.get(o)
                            if (op is None or now < _cool.get(o, 0)
                                    or o in _paused or o in _gopen):
                                continue
                            dme = _m.hypot(mypos[0] - op[0], mypos[1] - op[1])
                            closing = _prevd.get(o, 99.0) - dme > 0.02
                            _prevd[o] = dme
                            pc = _predict(o, mypos, op)
                            if pc is not None:
                                mid, my_eta, o_eta = pc
                                _form(o, mid, my_eta, o_eta, '경로교차 예측',
                                      f'{my_eta:.0f}s/{o_eta:.0f}s')
                                continue
                            if dme >= 2.0 or not closing:
                                continue
                            mid = ((mypos[0] + op[0]) / 2.0,
                                   (mypos[1] + op[1]) / 2.0)
                            _form(o, mid, dme / 2.0 / max(_speed, 0.05),
                                  dme / 2.0 / max(_spd(o), 0.05),
                                  '충돌 예측', f'{dme:.1f}m')
                    # ── (정지 측) 해소: 상대 방송 / 병목 진입→이탈 / 정체 / 시간초과 ──
                    for o in list(_paused):
                        # ★ 상대(우선 로봇)가 해소를 방송했으면 즉시 재개 —
                        #   자기 관측 조건을 기다리다 45~120초 서 있던 문제 해결
                        _k9 = '_'.join(sorted([robot, o]))
                        _rt9 = _resume['keys'].get(_k9)
                        # 이 정지가 시작된 뒤에 온 신호만 유효 (묵은 키로 다음
                        # 양보가 1초 만에 취소되던 문제) + 30초 지나면 폐기
                        if _rt9 is not None and _rt9 < _paused[o]['t']:
                            _resume['keys'].pop(_k9, None)
                            _rt9 = None
                        if _rt9 is not None and now - _rt9 > 30.0:
                            _resume['keys'].pop(_k9, None)
                            _rt9 = None
                        if _rt9 is not None:
                            _resume['keys'].pop(_k9, None)
                            print(f"[탐사-병목] {robot}: {o} 해소 방송 수신 — 즉시 재개",
                                  flush=True)
                            _cool[o] = now + 6.0
                            del _paused[o]
                            _prevd.pop(o, None)
                            if not _paused:
                                cur = None       # 목표 재발행 유도
                            continue
                        op = _pos.get(o)
                        mid = _paused[o]['mid']
                        o_mid = (_m.hypot(op[0] - mid[0], op[1] - mid[1])
                                 if op else 99.0)
                        if o_mid < 1.0:
                            _paused[o]['seen'] = True
                        o_passed = _paused[o].get('seen') and o_mid > 1.6
                        o_h = _hist.get(o, [])
                        o_still = (len(o_h) > 3 and _m.hypot(
                            o_h[-1][1] - o_h[0][1],
                            o_h[-1][2] - o_h[0][2]) < 0.10)
                        mutual_stall = ((now - _paused[o]['t'] > 6.0 and o_still
                                         and robot < o)
                                        or (now - _paused[o]['t'] > 45.0
                                            and o_still))
                        if (o_passed or mutual_stall
                                or now - _paused[o]['t'] > 120.0):
                            print(f"[탐사-병목] {robot}: "
                                  f"{'동시양보 — 이름 우선' if mutual_stall else o + ' 통과'}"
                                  " — 재개", flush=True)
                            _cool[o] = now + 12.0
                            del _paused[o]
                            _prevd.pop(o, None)
                            try:
                                _dispub.publish(json.dumps(
                                    {'group': '_'.join(sorted([robot, o])),
                                     'ranks': {}}))
                            except Exception:
                                pass
                            if not _paused:
                                cur = None        # 목표 재발행 유도
                    # ── (우선 측) 해산: 내가 병목 진입→이탈 / 시간초과 ──
                    for o in list(_gopen):
                        mid = _gopen[o]['mid']
                        my_mid = _m.hypot(mypos[0] - mid[0], mypos[1] - mid[1])
                        if my_mid < 1.0:
                            _gopen[o]['seen'] = True
                        i_passed = _gopen[o].get('seen') and my_mid > 1.6
                        if i_passed or now - _gopen[o]['t'] > 120.0:
                            key = '_'.join(sorted([robot, o]))
                            try:
                                # src=priority: 우선 로봇의 '통과 완료' 신고만
                                # 상대의 즉시 재개 근거가 된다 (양보 측 신호까지
                                # 받으면 동시양보 이름-우선 스태거가 깨진다)
                                _dispub.publish(json.dumps(
                                    {'group': key, 'ranks': {},
                                     'by': robot, 'src': 'priority'}))
                            except Exception:
                                pass
                            print(f"[탐사-병목] coalition {key} 해산", flush=True)
                            _cool[o] = now + 12.0
                            del _gopen[o]
                # ── 잼 탈출: 정지 매듭(전원 멈춤·밀집)은 '접근 중' 조건이 안
                # 걸려 충돌형성이 안 된다 — 목표 보유·20초 정체·동료 1.0m 이내면
                # 매듭 내 최상위(이름 앞)가 아닌 로봇이 잠깐 후진해 해체 (2026-08-09)
                if (mypos is not None and state['tgt'] is not None
                        and not _paused and now - _jam_cool > 30.0):
                    my_h = _hist.get(robot, [])
                    my_still = (len(my_h) > 3 and now - my_h[0][0] > 4.0
                                and _m.hypot(my_h[-1][1] - my_h[0][1],
                                             my_h[-1][2] - my_h[0][2]) < 0.08)
                    _jam_peers = [o for o in state['peers']
                                  if _pos.get(o) is not None
                                  and _m.hypot(_pos[o][0] - mypos[0],
                                               _pos[o][1] - mypos[1]) < 1.0]
                    if my_still and _jam_peers:
                        if not _jam_since:
                            _jam_since = now
                        elif (now - _jam_since > 20.0
                              and sorted([robot] + _jam_peers)[0] != robot):
                            print(f"[탐사-병목] {robot} 잼 탈출 — 후진", flush=True)
                            try:
                                client.cancel_all_goals()
                            except Exception:
                                pass
                            tw = _Tw()
                            tw.linear.x = -0.12
                            for _k9 in range(25):
                                _cvpub.publish(tw)
                                try:
                                    rospy.sleep(0.1)
                                except rospy.ROSInterruptException:
                                    break
                            _cvpub.publish(_Tw())
                            cur = None
                            _jam_cool = now
                            _jam_since = 0.0
                    else:
                        _jam_since = 0.0
                if _paused:
                    continue                      # 양보 정지 중 — 목표 발행 보류
                t = state['tgt']
                if t is None:
                    continue
                # 같은 목표라도 move_base 가 ABORT 상태면 주기 재전송 —
                # 초기 지도에서 plan 실패했다가 지도가 자라며 가능해진 경우 회복
                if (cur is not None and _m.hypot(t[0] - cur[0], t[1] - cur[1]) <= 0.35
                        and rospy.get_time() - _last_send > 20.0
                        and client.get_state() in (2, 4, 5, 8)):
                    # ★ 2(PREEMPTED) 포함 필수: 병목 양보/잼 탈출이 cancel 한 뒤
                    #   재개 경로가 놓치면 목표가 고아로 남아 로봇이 영구 정지
                    #   (locobot_1·waffle 동반 정지 실측, 2026-08-10)
                    cur = None
                    _fail_n += 1
                    # 계획실패 연속 2회 = 벽 inflation 스커트/일시 마킹에 갇힘 —
                    # 짧게 밀어 자력 탈출. ★ 2회(~40s)여야 발동한다: 피더의
                    # 60s waypoint skip 이 목표를 바꾸며 카운터를 리셋하므로
                    # 3회(60s) 기준은 레이스에 져서 영영 발동 못 한다(실측).
                    # ★ 방향은 후진↔전진 교대 — 무조건 후진이면 벽 반대편에서
                    #   갇혔을 때 벽으로 파고든다 (locobot_0 실측, 2026-08-10)
                    if _fail_n >= 2:
                        _dir = -0.12 if _esc_rev else 0.12
                        _esc_rev = not _esc_rev
                        print(f"[JnP-EXPLORE] {robot} 계획실패 {_fail_n}회 — "
                              f"{'후진' if _dir < 0 else '전진'} 탈출", flush=True)
                        try:
                            client.cancel_all_goals()
                        except Exception:
                            pass
                        tw9 = _Tw()
                        tw9.linear.x = _dir
                        for _k8 in range(25):
                            _cvpub.publish(tw9)
                            try:
                                rospy.sleep(0.1)
                            except rospy.ROSInterruptException:
                                break
                        _cvpub.publish(_Tw())
                        _fail_n = 0
                # ★ '도착했는데 새 목표가 근소하게 달라' 굳는 정체 (2026-08-11 실측):
                #   프런티어에 도달하면 move_base 는 SUCCEEDED(3). 그런데 그룹이
                #   주는 다음 목표가 0.35m 이내면 재전송 조건에 안 걸려 로봇이
                #   프런티어 0.2m 앞에서 영구 정지한다 — 그 자리 프런티어도 영영
                #   안 지워진다(waffle 실측). 목표에서 0.3m 넘게 떨어져 있는데
                #   완료 상태면 같은 목표라도 다시 보낸다.
                if (cur is not None and mypos is not None
                        and client.get_state() == 3
                        and _m.hypot(t[0] - mypos[0], t[1] - mypos[1]) > 0.30
                        and now - _last_send > 3.0):
                    print(f"[JnP-EXPLORE] {robot} 도착 상태로 정체 — 목표 재전송"
                          f" (잔여 {_m.hypot(t[0]-mypos[0], t[1]-mypos[1]):.2f}m)",
                          flush=True)
                    cur = None
                if cur is not None and _m.hypot(t[0] - cur[0], t[1] - cur[1]) > 0.35:
                    _fail_n = 0        # 새 목표 — 실패 카운터 초기화
                if cur is None or _m.hypot(t[0] - cur[0], t[1] - cur[1]) > 0.35:
                    yaw = 0.0
                    try:
                        from nav_msgs.msg import Odometry as _Od
                        _o = rospy.wait_for_message('/%s/odom' % robot, _Od,
                                                    timeout=2.0)
                        _cx = _o.pose.pose.position.x
                        _cy = _o.pose.pose.position.y
                        if _m.hypot(t[0] - _cx, t[1] - _cy) > 0.2:
                            yaw = _m.atan2(t[1] - _cy, t[0] - _cx)
                    except Exception:
                        pass
                    g = MoveBaseGoal()
                    g.target_pose.header.frame_id = 'map'
                    g.target_pose.header.stamp = rospy.Time.now()
                    g.target_pose.pose.position.x = t[0]
                    g.target_pose.pose.position.y = t[1]
                    q = tft.quaternion_from_euler(0, 0, yaw)
                    g.target_pose.pose.orientation.x = q[0]
                    g.target_pose.pose.orientation.y = q[1]
                    g.target_pose.pose.orientation.z = q[2]
                    g.target_pose.pose.orientation.w = q[3]
                    client.send_goal(g)
                    cur = t
                    _last_send = rospy.get_time()
                    print(f"[JnP-EXPLORE] {robot} → ({t[0]:.2f},{t[1]:.2f})",
                          flush=True)
            _standby = (state.get('mine_done') and not state.get('all_done'))
            try:
                client.cancel_all_goals()
                _s1.unregister(); _s3.unregister()
                if not _standby:               # 대기 모드는 완료 신호를 계속 본다
                    _s2.unregister(); _s2b.unregister()
                    _s4.unregister()
                for subs in _plan_sub.values():
                    for s9 in subs:
                        s9.unregister()
            except Exception:
                pass
            if _standby:
                # ★ 은퇴 로봇 '자리 비켜주기' (2026-08-11 지시): 몫을 다한 로봇이
                #   통로에 주차되면 현역의 전역 경로를 막고, 병목 엔진은 상대가
                #   곧 지나갈 것을 전제하므로 협상이 성립하지 않는다(충돌 실측).
                #   → task 는 정상 완료(트리 semantics 유지)하되, 배경 스레드가
                #     현역이 다가오면 옆으로 물러난다.
                def _yield_standby():
                    from nav_msgs.msg import OccupancyGrid as _OG9
                    cm9 = {'m': None}
                    rospy.Subscriber(
                        '/%s/move_base/global_costmap/costmap' % robot, _OG9,
                        lambda m: cm9.__setitem__('m', m), queue_size=1)

                    def _cost9(x9, y9):
                        m9 = cm9['m']
                        if m9 is None:
                            return 100
                        i9 = m9.info
                        gx = int((x9 - i9.origin.position.x) / i9.resolution)
                        gy = int((y9 - i9.origin.position.y) / i9.resolution)
                        if not (0 <= gx < i9.width and 0 <= gy < i9.height):
                            return 100
                        v9 = m9.data[gy * i9.width + gx]
                        return 60 if v9 < 0 else v9

                    def _me9():
                        tr9 = _buf.lookup_transform(
                            'map', '%s/base_footprint' % robot, rospy.Time(0))
                        return (tr9.transform.translation.x,
                                tr9.transform.translation.y)
                    print(f"[JnP-EXPLORE] {robot} 대기 모드 — 현역에게 자리 양보",
                          flush=True)
                    _moved_t = 0.0
                    while (not rospy.is_shutdown()
                           and not state.get('all_done')
                           and self._standby_gen == _my_gen):
                        try:
                            rospy.sleep(1.0)
                        except rospy.ROSInterruptException:
                            break
                        try:
                            mp9 = _me9()
                        except Exception:
                            continue
                        now9 = rospy.get_time()
                        if now9 - _moved_t < 15.0:
                            continue          # 방금 비켰으면 잠시 유지
                        # 가장 가까운 '현역' 동료
                        near9, nd9 = None, 99.0
                        for o9 in state['peers']:
                            try:
                                tr9 = _buf.lookup_transform(
                                    'map', '%s/base_footprint' % o9,
                                    rospy.Time(0))
                            except Exception:
                                continue
                            d9 = _m.hypot(tr9.transform.translation.x - mp9[0],
                                          tr9.transform.translation.y - mp9[1])
                            if d9 < nd9:
                                near9, nd9 = (tr9.transform.translation.x,
                                              tr9.transform.translation.y), d9
                        if near9 is None or nd9 > 1.6:
                            continue          # 아무도 안 다가옴 — 그대로 대기
                        # 상대 반대 방향 우선으로 1.2~2.0m 떨어진 free 지점 탐색
                        away9 = _m.atan2(mp9[1] - near9[1], mp9[0] - near9[0])
                        best9 = None
                        for da9 in (0.0, 0.6, -0.6, 1.2, -1.2, 1.9, -1.9):
                            for rr9 in (1.2, 1.8):
                                a9 = away9 + da9
                                x9 = mp9[0] + rr9 * _m.cos(a9)
                                y9 = mp9[1] + rr9 * _m.sin(a9)
                                if _cost9(x9, y9) >= 40:
                                    continue
                                if _cost9(mp9[0] + rr9 * 0.5 * _m.cos(a9),
                                          mp9[1] + rr9 * 0.5 * _m.sin(a9)) >= 60:
                                    continue          # 중간이 막힘
                                if _m.hypot(x9 - near9[0], y9 - near9[1]) < nd9 + 0.4:
                                    continue          # 더 멀어지지 않으면 무의미
                                best9 = (x9, y9)
                                break
                            if best9:
                                break
                        if best9 is None:
                            continue
                        g9 = MoveBaseGoal()
                        g9.target_pose.header.frame_id = 'map'
                        g9.target_pose.header.stamp = rospy.Time.now()
                        g9.target_pose.pose.position.x = best9[0]
                        g9.target_pose.pose.position.y = best9[1]
                        yaw9 = _m.atan2(best9[1] - mp9[1], best9[0] - mp9[0])
                        q9 = tft.quaternion_from_euler(0, 0, yaw9)
                        (g9.target_pose.pose.orientation.x,
                         g9.target_pose.pose.orientation.y,
                         g9.target_pose.pose.orientation.z,
                         g9.target_pose.pose.orientation.w) = q9
                        client.send_goal(g9)
                        _moved_t = now9
                        print(f"[JnP-EXPLORE] {robot} 자리 양보 — "
                              f"({best9[0]:.2f},{best9[1]:.2f}) 로 이동 "
                              f"(현역 {nd9:.2f}m 접근)", flush=True)
                    try:
                        # ★ cancel_all_goals 는 서버 전체 취소라 '새 태스크의
                        #   목표'까지 죽인다. 새 태스크에 밀려 끝나는 경우엔
                        #   절대 취소하지 않는다 (미션 종료로 끝날 때만 정리).
                        if self._standby_gen == _my_gen:
                            client.cancel_all_goals()
                        _s2.unregister(); _s2b.unregister(); _s4.unregister()
                    except Exception:
                        pass
                    print(f"[JnP-EXPLORE] {robot} 대기 모드 종료", flush=True)
                threading.Thread(target=_yield_standby, daemon=True).start()
            print(f"[JnP-EXPLORE] {robot} 탐사 종료", flush=True)
            return True
        except Exception as e:
            rospy.logwarn('explore 루프 실패: %s', e)
            return False

    def _drive_nav(self, spec):
        """'x,y[,yaw]' 를 move_base 로 실주행. 로봇 네임스페이스는 노드 순수 이름
        (/etri/locobot_0 → locobot_0). 성공 시 True — 실패는 스케줄러가 재시도."""
        try:
            from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
            import tf.transformations as tft
            vals = [float(v) for v in spec.split(',')]
            x, y = vals[0], vals[1]
            robot = self.node_name.strip('/').split('/')[-1]
            if len(vals) > 2:
                yaw = vals[2]
            else:
                # yaw 미지정: 진행 방향을 그대로 향함 — 도착 후 정렬 회전 제거
                yaw = 0.0
                try:
                    import math as _m
                    from nav_msgs.msg import Odometry as _Od
                    _o = rospy.wait_for_message('/%s/odom' % robot, _Od, timeout=3.0)
                    _cx = _o.pose.pose.position.x
                    _cy = _o.pose.pose.position.y
                    if _m.hypot(x - _cx, y - _cy) > 0.2:
                        yaw = _m.atan2(y - _cy, x - _cx)
                except Exception:
                    pass
            client = actionlib.SimpleActionClient('/%s/move_base' % robot, MoveBaseAction)
            if not client.wait_for_server(rospy.Duration(15.0)):
                rospy.logwarn('%s: move_base 서버 없음 — 항법 스택 확인', robot)
                return False
            g = MoveBaseGoal()
            g.target_pose.header.frame_id = 'map'
            g.target_pose.header.stamp = rospy.Time.now()
            g.target_pose.pose.position.x = x
            g.target_pose.pose.position.y = y
            q = tft.quaternion_from_euler(0, 0, yaw)
            g.target_pose.pose.orientation.x = q[0]
            g.target_pose.pose.orientation.y = q[1]
            g.target_pose.pose.orientation.z = q[2]
            g.target_pose.pose.orientation.w = q[3]
            print(f"[JnP-NAV] {robot} → ({x:.2f},{y:.2f})", flush=True)
            client.send_goal(g)
            client.wait_for_result()
            ok = client.get_state() == 3        # GoalStatus.SUCCEEDED
            print(f"[JnP-NAV] {robot} {'도달' if ok else '실패'}", flush=True)
            return ok
        except Exception as e:
            rospy.logwarn('nav 실행 실패: %s', e)
            return False


if __name__ == '__main__':
    # 인수 처리
    if len(sys.argv) < 4:  # 최소 4개의 인수 필요
        rospy.logerr("Usage: rosrun jnp jnp_agent.py __ns:=<namespace> __name:=<nodename> <filename>")
        sys.exit(1)

    #node_name = sys.argv[2]  # 두 번째 인수는 노드 이름
    filename = sys.argv[3]    # 세 번째 인수는 파일 이름

    print("==================================================")
    print("filename = {0}".format(filename))


    agent1 = JnPAgent(node_name='agent1',file_name=filename) 
    agent1.start()
    print("============ SEARCH +++++++++++++")
    nodes=agent1.search()
    for node in nodes:
        print("searched node:{0}".format(node))
    print("========")
