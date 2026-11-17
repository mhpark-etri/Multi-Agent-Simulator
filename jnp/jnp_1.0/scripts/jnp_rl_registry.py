# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G1 2026-10-31] 정보 제공 기능의 목록과 설명(description) v1.1 — ROS 없이 import 된다.

에이전트는 자기 상태·관측·결정을 "제공 항목" 으로 다른 에이전트에 알려 줄 수 있다. 어떤 항목을 제공하는지는 설명 XML 의
<provides> 에 적어 광고하고, 다른 에이전트는 설명을 읽고 그 채널을 구독한다. 설명에 적히지 않은 채널로 주고받는 것은 금지다.

설명 v1.1 = v1.0(agent·goal·capability·skills·busy) + <provides>. <data version="1.1"> 속성은 <provides> 가 있을 때만 붙는다.
옛 파서는 모르는 요소를 무시하고(그대로 동작), 새 파서는 <provides> 가 없으면 '제공 항목 없음'(None) 으로 읽는다 — <skills> 와 같은 규칙.
"""
import xml.etree.ElementTree as ET

DESCRIPTION_VERSION = '1.1'

# 항목 이름 → ROS 메시지 형식, 기본 주기(Hz; 'event' = 생길 때마다), 뜻
PROVIDES_ITEMS = {
    'pose':       {'type': 'geometry_msgs/PoseStamped', 'rate': 2.0,     'desc': '내 위치(map 좌표)'},
    'local_map':  {'type': 'nav_msgs/OccupancyGrid',    'rate': 0.5,     'desc': '내가 만든 지도'},
    'goal':       {'type': 'geometry_msgs/PoseStamped', 'rate': 'event', 'desc': '내 현재 이동 목표'},
    'done_area':  {'type': 'std_msgs/String',           'rate': 'event', 'desc': '내가 다 훑은 구역(JSON)'},
    'detections': {'type': 'std_msgs/String',           'rate': 'event', 'desc': '내 탐지 결과(JSON)'},
    'assignment': {'type': 'std_msgs/String',           'rate': 'event', 'desc': '리더가 제안하는 배정(JSON)'},
    'custom':     {'type': 'std_msgs/String',           'rate': 'event', 'desc': '제작자 정의 내용(JSON 문자열, 크기만 센다)'},
    'done':       {'type': 'std_msgs/String',           'rate': 'event', 'desc': '내 몫 끝 보고(JSON {robot, t, reason})'},
    'merged_map': {'type': 'nav_msgs/OccupancyGrid',    'rate': 'event', 'desc': 'host 가 합친 지도(결과물 전달 채널)'},
}


def channel(agent_name, item):
    """제공 채널 이름: /<에이전트 노드 이름>/jnp/provides/<항목>."""
    return '/%s/jnp/provides/%s' % (str(agent_name).strip('/'), item)


def normalize_items(value):
    """~jnp_provides 파라미터('' | 'pose,local_map' | ['pose']) → 알려진 항목 이름 목록(모르는 이름은 버리고 알림)."""
    if value is None:
        return []
    names = value if isinstance(value, (list, tuple)) else [x.strip() for x in str(value).split(',')]
    out, unknown = [], []
    for n in names:
        n = str(n).strip()
        if not n:
            continue
        (out if n in PROVIDES_ITEMS else unknown).append(n)
    if unknown:
        print('[JnP] ~jnp_provides 의 %s 는 제공 항목 목록에 없어 광고하지 않음(목록: %s)' % (unknown, sorted(PROVIDES_ITEMS)), flush=True)
    return out


def provides_xml(agent_name, items, rates=None):
    """<provides> 요소 문자열. items=[] 이면 빈 요소(제공 항목 없음을 선언)."""
    rates = rates or {}
    parts = ['<provides version="%s">' % DESCRIPTION_VERSION]
    for it in items:
        spec = PROVIDES_ITEMS[it]
        parts.append('<item name="%s" type="%s" channel="%s" rate="%s"/>' % (it, spec['type'], channel(agent_name, it), rates.get(it, spec['rate'])))
    parts.append('</provides>')
    return ''.join(parts)


def parse_provides(root):
    """설명 XML 루트 → 제공 항목 목록 [{name,type,channel,rate}] | None(<provides> 없음 = 구판 설명)."""
    pv = root.find('provides')
    if pv is None:
        return None
    return [{'name': it.get('name'), 'type': it.get('type'), 'channel': it.get('channel'), 'rate': it.get('rate')}
            for it in pv.findall('item') if it.get('name')]


def description_version(root):
    """<data version="…"> 값, 없으면 '1.0'."""
    return root.get('version') or '1.0'


def parse_description_provides(xml_text):
    """XML 문자열 → (버전, 제공 항목 목록|None). 파싱 실패는 ('1.0', None)."""
    try:
        root = ET.fromstring(xml_text or '')
    except ET.ParseError:
        return '1.0', None
    return description_version(root), parse_provides(root)
