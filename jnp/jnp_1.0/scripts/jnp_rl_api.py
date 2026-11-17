# -*- coding: utf-8 -*-
"""[JnP-1.0 RL G2 2026-10-31] 정책 계약 v0.2 — ROS 없이 import 된다. JnP 가 이 형식으로 입력을 만들어 정책을 부르고 출력을 적용한다.

정책이 받는 입력(Observation) = 자기 것(위치·자기 지도·후보·훑은 곳·역할) + 구독해서 실제 받은 것(received) + 지금 제공/구독 상태.
정책이 내는 출력(Action) = 이동(후보 번호 | None = 지금 목표 유지/없으면 유휴) + 제공 켜고 끄기(provide) + 구독 대상(subscribe).
리더 프록시(중앙)도 같은 형식을 쓴다(그때 received 에는 프록시가 구독한 전 로봇 정보가 들어 있다)."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

API_VERSION = '0.2'

_DEFAULT_SPECS = {   # 로봇 종류별 공칭값(트랙 명세·~jnp_robot_specs 로 덮어쓴다). 단위 m, m/s, rad/s
    'locobot': dict(max_lin=0.46, max_ang=1.9, footprint_r=0.25, lidar_range=16.0),
    'tb3': dict(max_lin=0.26, max_ang=1.82, footprint_r=0.22, lidar_range=3.5),
    'stretch': dict(max_lin=0.30, max_ang=0.50, footprint_r=0.25, lidar_range=12.0),
    'aibot': dict(max_lin=0.50, max_ang=1.0, footprint_r=0.30, lidar_range=12.0),
}


GOAL_XY_MAX_M = 1.5        # 접근점과 후보 사이의 최대 거리[m]. 런타임이 후보 대응을 검사할 때 쓴다


@dataclass
class RobotSpec:
    name: str
    rtype: str
    max_lin: float
    max_ang: float
    footprint_r: float
    lidar_range: float

    @classmethod
    def from_name(cls, name, override=None):
        low = str(name).lower()
        rtype = 'locobot' if 'loco' in low else 'tb3' if ('tb3' in low or 'waffle' in low or 'burger' in low) \
            else 'stretch' if 'stretch' in low else 'aibot' if ('ai' in low and 'bot' in low) else 'locobot'
        d = dict(_DEFAULT_SPECS[rtype])
        if override:
            if 'rtype' in override:
                rtype = str(override['rtype'])
            for k in ('max_lin', 'max_ang', 'footprint_r', 'lidar_range'):
                if k in override:
                    d[k] = float(override[k])
        return cls(name=str(name), rtype=rtype, **d)


@dataclass
class Candidate:
    x: float            # 실제 목표(자유 칸으로 옮긴 지점)
    y: float
    src_x: float        # 프론티어 원본 지점
    src_y: float
    dist: float         # 내 위치 → 목표 거리
    size: int = 0       # 프론티어 칸 수(정보량 어림)


@dataclass
class Observation:
    t: float                                          # 탐사 시작 후 sim초
    round_index: int                                  # 결정 호출 번호
    robot: str
    robot_spec: Optional[RobotSpec]
    my_pos: Tuple[float, float]
    candidates: List[Candidate]
    known_cells: int = 0                              # 자기 지도의 known 칸 수
    grid: Any = None                                  # 자기 지도 (MapMetaData, data) 참조
    visited: List[Tuple[float, float]] = field(default_factory=list)
    need_goal: bool = True                            # 지금 이동 목표가 필요한가(없음·도착·정체)
    current_goal: Optional[Tuple[float, float]] = None
    role: str = ''                                    # JnP 편성에서 받은 역할 이름
    teammates: List[str] = field(default_factory=list)   # JnP 편성에서 알려 준 팀원 이름
    received: Dict[str, Any] = field(default_factory=dict)   # '에이전트/항목' → 최근 받은 값 요약
    available: Dict[str, List[str]] = field(default_factory=dict)   # 에이전트 → 광고한 제공 항목
    providing: Set[str] = field(default_factory=set)  # 내가 지금 제공 중인 항목
    subscribed: Set[str] = field(default_factory=set)  # 내가 지금 구독 중인 '에이전트/항목'
    # 리더 프록시(중앙)용 — 프록시가 받은 팀 전체 정보
    robots_pos: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    others_targets: List[Tuple[float, float]] = field(default_factory=list)
    # 과제 종류와 자기 센서 결과
    mode: str = 'explore'                              # 'explore'(지도 제작) | 'search'(사람·물건 찾기)
    detections: List[Any] = field(default_factory=list)   # 자기 탐지기가 지금 보고 있는 것 [{cls, x, y, dist}] (내 센서 = 공짜)
    route: List[Tuple[float, float]] = field(default_factory=list)   # 수색 모드: JnP 가 준 내 구역 경유점 전체(순서대로)
    received_t: Dict[str, float] = field(default_factory=dict)      # [2026-11-01] '에이전트/항목' → 마지막 수신 시각(sim초). 구독 끊으면 사라진다
    received_meta: Dict[str, Any] = field(default_factory=dict)     # [2026-11-01, R5 F7] '에이전트/항목' → {'stamp': 보낸 쪽 발행 시각, 'frame': 좌표계 이름, 'seq': 번호}
    t_limit: Optional[float] = None                                # [2026-11-01, R5 F1] 회차 시간 한도 T[s](회차 명세에서; 없으면 None → 정책의 기본값)
    grid_frame: Optional[str] = None                               # [2026-11-05] 자기 지도의 좌표계 이름. 접근점을 줄 때 같은 값을 적는다
    grid_stamp: Optional[float] = None                             # [2026-11-05] 자기 지도 판의 시각(sim초). 판단 기록에 남긴다


@dataclass
class Action:
    choice: Optional[int]                         # candidates 번호 | None(목표 유지, 없으면 유휴)
    provide: Optional[Dict[str, bool]] = None     # {'pose': True, 'local_map': False, …} — 적은 것만 바꾼다
    subscribe: Optional[Set[str]] = None          # 원하는 구독 집합 '에이전트/항목' — None 이면 그대로
    note: str = ''
    done: bool = False                            # True = 내 탐사 몫 끝. 탐사 루프가 끝나고 JnP 가 task 완료로 처리한다(되돌릴 수 없음)
    custom_payload: Optional[str] = None          # 'custom' 항목으로 보낼 내용(JSON 문자열). 제공이 켜져 있어야 나간다
    merged_map: Any = None                        # host 가 합친 지도 ((res, ox, oy, w, h), data) — 'merged_map' 제공이 켜져 있으면 발행
    report: Any = None                            # 발견 보고 — 'detections' 제공이 켜져 있으면 JSON 으로 발행(수색 과제의 중앙 보고)
    goal_xy: Optional[Tuple[float, float]] = None   # [2026-11-05] choice 후보로 가려고 실제로 보낼 접근점. 자기 지도의 자유 칸이어야 한다. None 이면 후보의 x, y(기존 동작)
    goal_frame: Optional[str] = None              # [2026-11-05] goal_xy 의 좌표계 이름. Observation.grid_frame 과 같아야 한다
    cancel_goal: bool = False                     # [2026-11-05] 지금 목표를 버린다. choice=None 은 유지이므로 취소가 아니다. choice 와 함께 줄 수 없다
    cancel_why: str = ''                          # [2026-11-05] 취소 사유. 기록에만 쓴다


class Policy(object):
    api_version = API_VERSION

    def reset(self, track_info=None):
        """회차 시작 때 한 번(선택)."""

    def decide(self, obs):
        raise NotImplementedError
