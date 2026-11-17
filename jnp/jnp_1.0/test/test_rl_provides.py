#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [JnP-1.0 RL G1 2026-10-31] 정보 제공 기능·설명 v1.1·통신 기록표 검사. 실행: source <ws>/devel/setup.bash && python3 test/test_rl_provides.py
# ROS 마스터 없이 돈다(메시지 직렬화만 ROS 패키지 사용).
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import jnp_rl_registry as R                          # noqa: E402
import jnp_rl_meter as M                             # noqa: E402
import jnp_rl_link as L                              # noqa: E402
import jnp_agent as A                                # noqa: E402
import jnp_group as G                                # noqa: E402

FAIL = [0]


def ok(what, cond, detail=''):
    print(('PASS ' if cond else 'FAIL ') + what + ((' — ' + str(detail)) if (detail and not cond) else ''), flush=True)
    if not cond:
        FAIL[0] += 1


# A. provides 없으면 설명 v1.0 과 바이트까지 같다(동작 불변)
old_xml = ('<data><item>Sample XML content</item><agent>/etri/tb3_0</agent><goal>Relay</goal><capability>lidar,camera</capability>'
           '<skills source="registry">GoTo,Trip</skills><busy>0</busy></data>')
ok('A provides=None → v1.0 XML 동일', A.description_xml('/etri/tb3_0', 'Relay', 'lidar,camera', ['GoTo', 'Trip'], 'registry', False) == old_xml)
d0 = G.parse_description(old_xml)
ok('A v1.0 XML → provides None, desc_version 1.0', d0['provides'] is None and d0['desc_version'] == '1.0' and d0['skills'] == ['GoTo', 'Trip'])

# B. provides 있으면 v1.1 — 왕복
xml = A.description_xml('/etri/tb3_0', 'Relay', 'lidar,camera', ['GoTo'], 'registry', True, provides=['pose', 'local_map'], provides_rates={'pose': 5})
d = G.parse_description(xml)
ok('B v1.1 XML 에 version 속성·<provides>', xml.startswith('<data version="1.1">') and '<provides version="1.1">' in xml)
ok('B 왕복: 항목 2개·채널·형식·주기', d['desc_version'] == '1.1' and [p['name'] for p in d['provides']] == ['pose', 'local_map']
   and d['provides'][0]['channel'] == '/etri/tb3_0/jnp/provides/pose' and d['provides'][0]['type'] == 'geometry_msgs/PoseStamped'
   and d['provides'][0]['rate'] == '5' and d['provides'][1]['rate'] == '0.5', d)
ok('B 다른 필드는 그대로(skills·busy)', d['skills'] == ['GoTo'] and d['busy'] is True)
ok('B 빈 목록 = 없음 선언', G.parse_description(A.description_xml('/a', 'Relay', 'lidar', None, 'registry', False, provides=[]))['provides'] == [])

# C. 옛 파서 흉내(0.9.0 처럼 알려진 요소만 find) — v1.1 XML 을 읽어도 깨지지 않는다
import xml.etree.ElementTree as ET
root = ET.fromstring(xml)
ok('C 구판 파서 호환: agent·skills·busy 그대로 읽힘', root.find('agent').text == '/etri/tb3_0' and root.find('skills').text == 'GoTo' and root.find('busy').text == '1')

# D. 파라미터 정규화
ok('D normalize_items', R.normalize_items('pose, local_map,nope') == ['pose', 'local_map'] and R.normalize_items('') == [] and R.normalize_items(['goal']) == ['goal'])

# E. 통신 기록표 — 받는 쪽이 적고, 수신자가 둘이면 두 번
tmp = tempfile.mkdtemp()
la = M.CommLog('/etri/a', os.path.join(tmp, 'a.jsonl')); lb = M.CommLog('/etri/b', os.path.join(tmp, 'b.jsonl'))
la.record('data', 'pose', '/etri/c', '/etri/a', 100, t=1.0); lb.record('data', 'pose', '/etri/c', '/etri/b', 100, t=1.0)
la.record('control', 'description', '/etri/c', '/etri/a', 40, t=0.5)
agg = M.aggregate([la.path, lb.path])
ok('E 합계 240 = 100+100+40, 쌍별·종류별', agg['bytes_total'] == 240 and agg['by_pair']['etri/c->etri/a'] == 140 and agg['by_pair']['etri/c->etri/b'] == 100
   and agg['by_kind'] == {'data': 200, 'control': 40}, agg)
# [R11 F1·F4] 런타임이 남기는 식별 줄(policy_manifest·episode_sync: meta, 덧붙임 칸 포함)은 결함 줄도 바이트도 아니다
la.record('meta', 'policy_manifest', '/etri/a', '/etri/a', 0, t=0.1, extra={'policy': {'spec': 'x.py:SomePolicy', 'class': 'm.SomePolicy', 'manifest': {'wrapper_hash': 'abc'}}})
la.record('meta', 'episode_sync', '/etri/a', '/etri/a', 0, t=0.2, extra={'t0': 120.0, 'T': 600.0, 'episode_run_id': 'r1'})
agg2 = M.aggregate([la.path, lb.path])
ok('E 식별 meta 줄은 합계·결함에 안 들어감', agg2['bytes_total'] == 240 and agg2['rows_malformed'] == 0 and agg2['rows'] == agg['rows']
   and M.read_log(la.path)[-1]['t0'] == 120.0 and M.read_log(la.path)[-2]['policy']['class'] == 'm.SomePolicy', agg2)

# F. 수신 처리: AnyMsg 본문 → 바이트 기록 → PoseStamped 로 풀기 → 콜백
from geometry_msgs.msg import PoseStamped
m = PoseStamped(); m.header.frame_id = 'map'; m.pose.position.x = 1.5; m.pose.position.y = -2.0; m.pose.orientation.w = 1.0
buf = io.BytesIO(); m.serialize(buf); raw = buf.getvalue()


class FakeAny(object):
    def __init__(self, b): self._buff = b


got = []
h = L.make_receive_handler(PoseStamped, la, 'pose', '/etri/c', '/etri/a', got.append)
h(FakeAny(raw))
ok('F 받은 메시지가 풀리고 바이트가 기록됨', len(got) == 1 and abs(got[0].pose.position.x - 1.5) < 1e-9 and got[0].header.frame_id == 'map'
   and la.rows[-1]['bytes'] == len(raw) and la.rows[-1]['item'] == 'pose' and la.rows[-1]['sender'] == 'etri/c')
ok('F 채널 이름 규칙', R.channel('/etri/tb3_0', 'pose') == '/etri/tb3_0/jnp/provides/pose')
ok('F 메시지 클래스 찾기', L.msg_class_of('nav_msgs/OccupancyGrid').__name__ == 'OccupancyGrid')

print('TOTAL test_rl_provides: %d FAIL' % FAIL[0])
sys.exit(1 if FAIL[0] else 0)
