# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G2] 정책 파일 읽기. 지정 형식: '/path/file.py:ClassName' | '/path/file.py'(Policy 하위 클래스 1개) | 'pkg.module:ClassName'.
운영 측 기준 정책은 이름('nearest', 'route')으로도 지정한다. 그 파일(jnp_rl_baseline.py)은 운영 측에만 있다."""
import importlib
import importlib.util
import inspect
import os

from jnp_rl_api import Policy, API_VERSION


FORBIDDEN = ('rospy', 'roslib', 'rosgraph', 'rostopic', 'rosnode', 'rosparam', 'actionlib', 'tf2_ros', 'socket', 'subprocess', 'xmlrpc')


def check_policy_source(text):
    """정책 파일이 ROS 나 네트워크에 직접 붙는지 정적으로 본다(import 줄만). 걸리면 모듈 이름 목록을 돌려준다."""
    import re
    bad = []
    for line in text.splitlines():
        m = re.match(r'\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', line)
        if not m:
            continue
        mod = (m.group(1) or m.group(2)).split('.')[0]
        if mod in FORBIDDEN:
            bad.append(mod)
    return bad


def _load_module_from_path(path):
    if os.environ.get('JNP_POLICY_UNSAFE', '') != '1':
        bad = check_policy_source(open(path, encoding='utf-8', errors='replace').read())
        if bad:
            raise ImportError('정책 파일이 금지된 모듈을 씀 %s — 정책은 JnP 가 넘긴 입력만 써야 한다(JNP_POLICY_UNSAFE=1 로 개발 중에만 해제)' % sorted(set(bad)))
    name = 'jnp_policy_' + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError('정책 파일을 읽을 수 없음: %s' % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_policy(spec_str, track_info=None):
    spec_str = str(spec_str).strip()
    if not spec_str:
        raise ValueError('빈 정책 지정')
    if spec_str in ('nearest', 'route'):
        raise ImportError("기준 정책 %r 은 이 묶음에 없다. 정책 파일을 '/path/file.py:ClassName' 으로 지정한다" % spec_str)
    else:
        path, _, cls_name = spec_str.partition(':')
        mod = _load_module_from_path(os.path.expanduser(path)) if (path.endswith('.py') or os.path.sep in path) else importlib.import_module(path)
        if cls_name:
            cls = getattr(mod, cls_name)
        else:
            cands = [c for _, c in inspect.getmembers(mod, inspect.isclass) if issubclass(c, Policy) and c is not Policy and c.__module__ == mod.__name__]
            if len(cands) != 1:
                raise ValueError('Policy 하위 클래스가 정확히 1개여야 함(발견 %d개): %s' % (len(cands), spec_str))
            cls = cands[0]
        pol = cls()
    if not callable(getattr(pol, 'decide', None)):
        raise TypeError('정책에 decide(obs) 가 없음')
    ver = str(getattr(pol, 'api_version', ''))
    if ver.split('.')[0] != API_VERSION.split('.')[0]:
        raise ValueError('정책 api_version %r 가 JnP %r 와 맞지 않음' % (ver, API_VERSION))
    try:
        pol.reset(track_info)
    except Exception as e:
        if getattr(pol, 'strict_reset', False):
            # [2026-11-01, Gazebo 9차에서 발견] 가중치·설정 검사가 reset 에서 실패한 정책은 쓰면 안 된다 — 경고로 넘기면 거부된 체크포인트로 돈다
            raise RuntimeError('정책 reset 실패(치명): %s' % e)
        print('[JnP] 정책 reset 경고: %s' % e, flush=True)
    return pol
