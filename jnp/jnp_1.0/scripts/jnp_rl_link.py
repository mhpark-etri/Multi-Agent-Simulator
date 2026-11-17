# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G1 2026-10-31] 정보 제공·구독 연결(ROS 필요). 설명을 읽고 → 광고된 채널을 구독하고 → 받은 바이트를 기록표에 적는다.

- Provider: 제공 채널에 발행한다(보내는 쪽은 세지 않는다 — 받는 쪽이 센다).
- subscribe(): rospy.AnyMsg 로 받아 본문 바이트를 먼저 세고, 그다음 실제 메시지 형식으로 풀어 콜백에 준다.
- query_description(): 설명 서비스 응답 XML 크기를 제어 메시지로 센다.
- describe_and_subscribe(): 설명 조회 → <provides> 확인 → 구독. 위치(pose) 한 항목으로 처음부터 끝까지 잇는 시험이 이 함수다.
"""
import importlib

from jnp_rl_registry import PROVIDES_ITEMS, channel, parse_description_provides


def msg_class_of(type_str):
    """'geometry_msgs/PoseStamped' → 클래스."""
    pkg, name = type_str.split('/')
    return getattr(importlib.import_module(pkg + '.msg'), name)


def make_receive_handler(msg_class, log, item, sender, receiver, callback):
    """AnyMsg → 바이트 기록 → 메시지 풀기 → 콜백. ROS 없이도 호출 가능(시험용)."""
    def handler(anymsg):
        buff = getattr(anymsg, '_buff', b'') or b''
        msg = msg_class()
        msg.deserialize(buff)
        if log is not None:
            log.record('data', item, sender, receiver, len(buff))
        callback(msg)
    return handler


class Provider(object):
    def __init__(self, agent_name, item, queue_size=5, latch=False):
        import rospy
        self.item = item
        self.channel = channel(agent_name, item)
        self.msg_class = msg_class_of(PROVIDES_ITEMS[item]['type'])
        self.pub = rospy.Publisher(self.channel, self.msg_class, queue_size=queue_size, latch=latch)

    def publish(self, msg):
        self.pub.publish(msg)


def subscribe(self_name, provider_agent, item, callback, log=None, type_str=None):
    """광고된 채널을 구독한다. 구독 시작을 제어 메시지(채널 이름 길이)로 한 번 적는다."""
    import rospy
    ch = channel(provider_agent, item)
    msg_class = msg_class_of(type_str or PROVIDES_ITEMS[item]['type'])
    if log is not None:
        log.record('control', 'subscribe:' + item, self_name, provider_agent, len(ch))
    return rospy.Subscriber(ch, rospy.AnyMsg, make_receive_handler(msg_class, log, item, provider_agent, self_name, callback), queue_size=10)


def query_description(self_name, other_agent, log=None, timeout=5.0):
    """다른 에이전트의 설명 서비스를 불러 XML 을 받는다. 응답 크기를 제어 메시지로 적는다."""
    import rospy
    from jnp.srv import DescriptionService
    srv = '/%s/description_service' % str(other_agent).strip('/')
    rospy.wait_for_service(srv, timeout=timeout)
    xml = rospy.ServiceProxy(srv, DescriptionService)('').output_xml
    if log is not None:
        log.record('control', 'description', other_agent, self_name, len(xml.encode('utf-8')))
    return xml


def describe_and_subscribe(self_name, other_agent, item, callback, log=None, timeout=5.0):
    """설명 조회 → 그 에이전트가 item 을 광고하면 구독. 광고하지 않으면 None."""
    xml = query_description(self_name, other_agent, log, timeout)
    _ver, provides = parse_description_provides(xml)
    for p in provides or []:
        if p['name'] == item:
            return subscribe(self_name, other_agent, item, callback, log, p.get('type'))
    return None


def start_pose_provider(agent_name, rate_hz=2.0, stamp_from_tf=False, buf=None):
    """내 위치(map→<로봇>/base_footprint TF)를 주기적으로 제공 채널에 발행하는 타이머를 켠다. 반환: (Provider, Timer).
    [2026-11-04] stamp_from_tf 면 메시지 시각에 변환의 표본 시각을 그대로 적어 받는 쪽이 원본 나이를 볼 수 있게 한다. 형식과 크기는 같다. buf 를 주면 그 TF 버퍼를 함께 쓴다."""
    import rospy
    import tf2_ros
    from geometry_msgs.msg import PoseStamped
    robot = str(agent_name).strip('/').split('/')[-1]
    prov = Provider(agent_name, 'pose')
    lis = None
    if buf is None:
        buf = tf2_ros.Buffer(rospy.Duration(10.0))
        lis = tf2_ros.TransformListener(buf)
    state = {'lis': lis}

    def tick(_evt):
        try:
            tr = buf.lookup_transform('map', '%s/base_footprint' % robot, rospy.Time(0))
        except Exception:
            return
        m = PoseStamped()
        m.header.stamp = tr.header.stamp if stamp_from_tf else rospy.Time.now(); m.header.frame_id = 'map'
        m.pose.position.x = tr.transform.translation.x; m.pose.position.y = tr.transform.translation.y
        m.pose.position.z = tr.transform.translation.z; m.pose.orientation = tr.transform.rotation
        prov.publish(m)
    timer = rospy.Timer(rospy.Duration(1.0 / max(float(rate_hz), 0.01)), tick)
    return prov, timer


def start_providers(agent_name, items, rate_hz=2.0):
    """~jnp_provides 항목 중 지금 구현된 것(pose)만 켠다. 나머지 항목은 G2 이후."""
    import rospy
    started = {}
    if not rospy.core.is_initialized():
        return started
    for it in items:
        if it == 'pose':
            started[it] = start_pose_provider(agent_name, rate_hz)
        else:
            print('[JnP] 제공 항목 %s 는 아직 발행기가 없음(광고만 함)' % it, flush=True)
    return started
