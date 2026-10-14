######################################################
## JnP Monitor 다이얼로그 (JnP 0.8.2)                ##
## 설명 : JnP 동작(discovery/coalition/scheduling)을 ##
##        전용 창에서 그래픽으로 표시                 ##
##  - /jnp/status        : 그룹이 발행하는 JSON 상태  ##
##  - /jnp_agent_join_event : new/kill/task 이벤트    ##
##  - /jnp/plan          : 작업 분할 기록(JSON, latched) ##
##     미션(자연어) → 분할된 subtask → 스킬 매칭 표시  ##
######################################################
import sys
import re
import json
import time
import subprocess
import datetime
from PySide6 import QtWidgets, QtCore, QtGui
from dlgJnpMonitor_ui import Ui_DlgJnpMonitor

from constant import *

# 상태별 색 (task tree 노드)
COLOR_WAIT = QtGui.QColor("#9e9e9e")        # 대기
COLOR_RUN = QtGui.QColor("#ffc107")         # 실행 중
COLOR_DONE = QtGui.QColor("#4caf50")        # 완료
COLOR_COMPOSITE = QtGui.QColor("#546e7a")   # 복합(Seq/Par)
COLOR_EDGE = QtGui.QColor("#90a4ae")

NODE_W, NODE_H, GAP_X, GAP_Y = 220, 76, 26, 52   # 노드 3줄(이름/스킬·요구/배정)
NODE_FONT_PT = 12               # 트리 글씨 크기 (굵게) — 시인성


def _esc(x):
    return (str(x).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _short(agent):
    return (agent or '').strip('/').split('/')[-1]


def _as_dict(obj):
    return obj if isinstance(obj, dict) else None


def _tree_has(node, name):
    if not isinstance(node, dict):
        return 0
    n = 1 if node.get('name') == name else 0
    for c in node.get('children') or []:
        n += _tree_has(c, name)
    return n


def plan_row_for(plans, statuses, groups, node_name):
    """트리 노드 라벨용 조회 — node 의 **실제 소유 그룹**을 상태 트리에서 먼저 정한다:
    groups 중 상태 트리에 그 node 이름을 가진 그룹이 둘 이상이면 모호 → None(미확인); 정확히 하나면 그 그룹만 본다;
    하나도 없으면(트리 없음) 계획 행이 정확히 한 그룹에만 있을 때만 쓴다. 고른 그룹의 계획이 없거나 상태와 run_id 가 다르면 None.
    (계획 hits 수만 세면 한 그룹의 계획이 아직 없을 때 다른 그룹의 행이 붙는다 — 2차 검수 R2-M1c.)"""
    groups = list(groups or [])
    owners = [g for g in groups if _tree_has((_as_dict(statuses.get(g)) or {}).get('tree'), node_name) > 0]
    if len(owners) > 1:
        return None
    if len(owners) == 1:
        cands = owners
    else:
        cands = [g for g in groups
                 if any(r.get('node') == node_name for r in (_as_dict(plans.get(g)) or {}).get('subtasks') or [] if isinstance(r, dict))]
        if len(cands) != 1:
            return None
    g = cands[0]
    rec = _as_dict(plans.get(g))
    st = _as_dict(statuses.get(g))
    if not rec or not st or not rec.get('run_id') or rec.get('run_id') != st.get('run_id'):
        return None
    hits = [r for r in rec.get('subtasks') or [] if isinstance(r, dict) and r.get('node') == node_name]
    return hits[0] if len(hits) == 1 else None


def _tag_tree(node, grp):
    """트리 노드마다 소유 그룹을 적어 둔 사본(합쳐 그릴 때 각 node 가 자기 그룹의 계획만 보게)."""
    if not isinstance(node, dict):
        return node
    out = dict(node)
    out['_grp'] = grp
    out['children'] = [_tag_tree(c, grp) for c in node.get('children') or []]
    return out


def build_plan_html(plans, statuses, ko=True, cap_history=None):
    """[JnP-0.8.2 2026-10-14] '미션 → 분할된 subtask → 스킬 매칭' HTML (Qt 비의존).
    plans: 그룹명 -> /jnp/plan 기록, statuses: 그룹명 -> /jnp/status, cap_history: (그룹, run_id) -> {agent: cap} 같은 회차에서 마지막 관측.
    결합 규칙: 계획과 상태는 **같은 run_id** 일 때만 결합한다(이전 회차의 완료 상태가 새 계획에 붙지 않게). 상태가 없거나 회차가
    다르면 행 상태를 '상태 미확인'으로 둔다. 그룹이 해체(dissolved)·완료(success/failed)면 이력으로 표시하고 후보는 계산하지 않는다.
    매칭 = 요구 능력 ⊆ 보유 능력(능력 적합성). 유휴 여부·affinity·ETA 에 따른 실제 배정과는 다를 수 있다 — 표 밑에 명시."""
    T = (lambda k, e: k) if ko else (lambda k, e: e)
    if not plans:
        return ("<p style='color:#777;font-size:14px'>%s</p>" % T(
            '협업 태스크를 발행하면 미션의 분할 결과와 스킬 매칭이 여기에 표시됩니다',
            'Publish a collaboration task to see the decomposition and skill matching'))
    out = ["<style>body{font-size:13px} table{border-collapse:collapse;width:100%} td,th{border:1px solid #cfd8dc;padding:3px 7px;font-size:13px} "
           "th{background:#eceff1} .ok{color:#2e7d32;font-weight:bold} .no{color:#c62828;font-weight:bold} .unk{color:#6d4c41;font-weight:bold} "
           ".running{color:#ef6c00;font-weight:bold} .done{color:#2e7d32;font-weight:bold} .wait{color:#757575} .hist{color:#9e9e9e} "
           ".mission{font-size:16px;font-weight:bold;color:#1a237e;background:#e8eaf6;border-left:5px solid #3f51b5;padding:5px 8px;margin:4px 0} "
           ".badge{border-radius:3px;padding:0 5px;font-weight:bold} .head{font-size:14px;margin:4px 0}</style>"]
    STATE_COLOR = {'forming': '#ffc107', 'running': '#03a9f4', 'success': '#4caf50', 'failed': '#f44336', 'dissolved': '#9e9e9e'}
    for grp in sorted(plans):
        rec = _as_dict(plans[grp]) or {}
        st = _as_dict(statuses.get(grp)) or {}
        rid, srid = rec.get('run_id') or '', st.get('run_id') or ''
        linked = bool(rid) and rid == srid
        gstate = st.get('state', '') if linked else ''
        hist = gstate in ('dissolved', 'success', 'failed')
        caps_now = {m.get('name'): (m.get('cap') if isinstance(m.get('cap'), list) else None)
                    for m in (st.get('members') or []) if isinstance(m, dict)} if linked else {}
        caps_last = (cap_history or {}).get((grp, rid)) or {}
        node_state = {}

        def walk(n):
            if isinstance(n, dict):
                node_state[n.get('name')] = n
                for c in n.get('children') or []:
                    walk(c)
        if linked:
            walk(st.get('tree'))
        src = rec.get('source', '?')
        psrc = (rec.get('plan_source') or '').lower()
        if src != 'plan':
            badge = ''
        elif psrc == 'example':
            badge = ("<span class='badge' style='background:#fff3e0;color:#e65100;border:1px solid #ffb74d'>EXAMPLE</span> "
                     "<span style='color:#8d6e63'>%s</span>" % T('(사람이 쓴 분할 템플릿 — LLM-TDM 모듈 출력 아님)', '(hand-written template, not LLM-TDM output)'))
        elif psrc == 'llm-tdm':
            badge = "<span class='badge' style='background:#e3f2fd;color:#0d47a1;border:1px solid #64b5f6'>LLM-TDM</span>"
        else:
            badge = "<span class='badge' style='background:#eeeeee;color:#424242;border:1px solid #bdbdbd'>%s</span>" % _esc((psrc or 'unknown').upper())
        # 그룹 상태 배지 (회차 결합 여부 포함)
        if linked:
            gs = "<span class='badge' style='background:%s;color:#fff'>%s</span>" % (STATE_COLOR.get(gstate, '#607d8b'), _esc(gstate or '?'))
            if hist:
                gs += " <span class='hist'>%s</span>" % T('— 종료됨: 마지막 관측 이력', '— finished: last observed history')
        elif srid and rid and srid != rid:
            gs = "<span class='unk'>%s</span>" % T('상태 회차 불일치 — 이 계획의 상태 기록이 아직 없음', 'status is from another run — no status for this plan yet')
        else:
            gs = "<span class='unk'>%s</span>" % T('상태 미확인(아직 /jnp/status 없음)', 'state unknown (no /jnp/status yet)')
        if src == 'plan':
            head = "<b>%s</b> &nbsp; goal=<b>%s</b> &nbsp; %s <code>%s</code> %s &nbsp; %s" % (
                _esc(grp), _esc(rec.get('goal', '')), T('분할 계획', 'plan'), _esc(rec.get('plan_name') or ''), badge, gs)
        else:
            head = "<b>%s</b> &nbsp; goal=<b>%s</b> &nbsp; <span class='no'>%s</span> (%s) &nbsp; %s" % (
                _esc(grp), _esc(rec.get('goal', '')), T('고정 빌더로 대체', 'fixed builder (fallback)'), _esc(rec.get('reason', '')), gs)
        out.append("<p class='head'>%s</p>" % head)
        desc = rec.get('task_description') or ''
        if desc:
            out.append("<div class='mission'>%s %s</div>" % (
                T('미션(자연어, example):', 'Mission (example):') if psrc == 'example' else T('미션(자연어):', 'Mission:'), _esc(desc)))
        b = rec.get('bindings') or {}
        if isinstance(b, dict) and b:
            bs = '; '.join('%s=%s' % (k, json.dumps(v, ensure_ascii=False)) for k, v in b.items())
            out.append("<p style='margin:2px 0;color:#455a64'><b>%s</b> %s</p>" % (T('바인딩(payload→상수):', 'bindings:'), _esc(bs)[:600]))
        out.append("<table><tr><th>#</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>" % (
            T('분할된 subtask (스킬·인수)', 'subtask (skill·args)'), T('요구 능력', 'needs'), T('실행 node', 'exec node'),
            T('배정 에이전트 [보유 능력]', 'agent [capabilities]'), T('매칭(능력 적합성)', 'match (capability)'), T('상태', 'state')))
        for i, r in enumerate(rec.get('subtasks') or [], 1):
            if not isinstance(r, dict):
                continue
            skill = r.get('skill')
            args = r.get('args') if isinstance(r.get('args'), dict) else {}
            sub = ("%s(%s)" % (skill, ', '.join('%s=%s' % (k, v) for k, v in args.items()))) if skill else (r.get('exec_goal') or '')
            extra = [x for x in (r.get('required_skills') or []) if x != skill]
            if extra:
                sub += " +" + ','.join(str(x) for x in extra)
            req = [str(x) for x in (r.get('requirement') or [])]
            ns = node_state.get(r.get('node')) or {}
            agent = ns.get('agent') or (r.get('preassigned_agent') or '')
            # ── 매칭 셀: 3상태(충족 / 명시적 불일치 / 정보 없음) + 가상·상시 서비스 ──
            if r.get('preassigned'):
                match = "<span class='ok'>%s</span>" % T('상시 서비스(초기 역할)', 'standing service (initial role)')
                agent_txt = _esc(_short(agent))
            elif 'virtual' in req:
                match = "<span class='wait'>%s</span>" % T('그룹이 완료 처리', 'completed by group')
                agent_txt = '—'
            elif agent:
                src_cap = None
                if agent in caps_now and caps_now[agent] is not None:
                    have, src_cap = caps_now[agent], 'now'
                elif agent in caps_last and caps_last[agent] is not None:
                    have, src_cap = caps_last[agent], 'last'
                else:
                    have = None
                if have is None:
                    match = "<span class='unk'>%s</span>" % T('능력 정보 없음 — 검증 불가', 'no capability info — cannot verify')
                    agent_txt = "%s [%s]" % (_esc(_short(agent)), T('정보 없음', 'unknown'))
                else:
                    ok = set(req) <= set(str(x) for x in have)
                    note = '' if src_cap == 'now' else (" <span class='hist'>(%s)</span>" % T('같은 회차 마지막 관측', 'last observed in this run'))
                    match = "<span class='%s'>%s %s⊆{%s}</span>%s" % ('ok' if ok else 'no', '✓' if ok else '✗', _esc(','.join(req)), _esc(','.join(str(x) for x in have)), note)
                    agent_txt = "%s [%s]" % (_esc(_short(agent)), _esc(','.join(str(x) for x in have)))
            else:
                if hist or not linked:
                    match = "<span class='hist'>—</span>"
                else:
                    cands = [_short(n) for n, c in caps_now.items() if c is not None and set(req) <= set(str(x) for x in c)]
                    match = "<span class='wait'>%s: %s</span>" % (T('능력 충족 후보', 'capability-compatible candidates'), _esc(', '.join(cands)) or '0')
                agent_txt = T('(미배정)', '(unassigned)')
            if not linked:
                state, st_cls = T('상태 미확인', 'unknown'), 'unk'
            else:
                raw = ns.get('state') or ('service' if r.get('preassigned') else 'wait')
                st_cls = raw if raw in ('running', 'done', 'wait') else 'wait'
                state = {'running': T('실행 중', 'running'), 'done': T('완료', 'done'), 'wait': T('대기', 'wait'),
                         'service': T('상시', 'service')}.get(raw, raw)
                if hist:
                    st_cls = 'hist'
                    state += T('(이력)', '(history)')
            out.append("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%s</td></tr>" % (
                i, _esc(sub), _esc(','.join(req)) + (' (optional)' if r.get('optional') else ''), _esc(r.get('node', '')),
                agent_txt, match, st_cls, _esc(state)))
        out.append("</table>")
        out.append("<p style='color:#607d8b;margin:2px 0;font-size:12px'>%s</p>" % T(
            '매칭 = 요구 능력 ⊆ 보유 능력(능력 적합성). 실제 배정은 유휴 여부·affinity·ETA 에 따라 달라질 수 있음. 상시 서비스는 초기 역할 표시이며 실행 성공의 증빙이 아님.',
            'match = required ⊆ advertised capabilities (compatibility). Actual assignment also depends on idleness, affinity and ETA. "standing service" describes the initial role, not execution success.'))
        if rec.get('warnings'):
            out.append("<p style='color:#8d6e63;margin:2px 0'>%s %s</p>" % (T('변환 경고:', 'warnings:'), _esc('; '.join(str(w) for w in rec['warnings']))))
    return ''.join(out)


class DialogJnpMonitor(QtWidgets.QDialog):
    # Init
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_DlgJnpMonitor()
        self.ui.setupUi(self)
        # 모달 아님 — 시뮬레이터와 나란히 두고 관찰하는 옵션 창.
        # ★ Dialog 타입(=Window|0x2) 창엔 WM(MobaXterm 포함)이 최대화 버튼을
        #   안 그린다 — Window '비트'만 켜는 setWindowFlag(Qt.Window)는 no-op.
        #   타입 자체를 일반 창으로 교체해야 제목줄에 최소/최대화 버튼이 생긴다.
        self.setWindowFlags(QtCore.Qt.Window
                            | QtCore.Qt.WindowTitleHint
                            | QtCore.Qt.WindowSystemMenuHint
                            | QtCore.Qt.WindowMinMaxButtonsHint
                            | QtCore.Qt.WindowCloseButtonHint)
        self.setSizeGripEnabled(True)

        self.m_scene = QtWidgets.QGraphicsScene(self)
        self.ui.gvJnpTree.setScene(self.m_scene)

        # 에이전트 목록/제목 폰트 확대 (시인성)
        f = self.ui.lstJnpAgents.font()
        f.setPointSize(12)
        self.ui.lstJnpAgents.setFont(f)
        for lb in (self.ui.lbAgentsTitle, self.ui.lbTreeTitle):
            tf = lb.font()
            tf.setPointSize(11)
            tf.setBold(True)
            lb.setFont(tf)

        self.m_agents = {}          # name -> 'alive' | 'killed'
        self.m_status = None        # (호환) 마지막 수신 상태
        self.m_statuses = {}        # 그룹명 -> 최신 상태 (goal별 다중 coalition 지원)
        self.m_dissolved = set()    # 해체 확정 그룹 (잔여 상태 역전 방어)
        self.m_plans = {}           # 그룹명 -> /jnp/plan 기록 (미션·분할·스킬 매칭)
        self.m_caps = {}            # (그룹명, run_id) -> {agent: cap} 같은 회차에서 마지막 관측한 보유 능력 (멤버 방출 뒤 표시용)
        # 회차별 상태 보관(2차 검수 R2-M1a): (그룹명, run_id) -> {'status','dissolved','order'}. m_statuses[그룹] 은 여기서 고른
        # '표시 상태'(계획이 있으면 계획과 같은 run_id 의 상태, 없으면 가장 최근에 수용한 상태 — 구버전/계획 없는 그룹 정책).
        self.m_runs = {}
        self.m_run_seq = 0
        self.MAX_RUNS_PER_GROUP = 20   # 그룹당 보관 회차 상한(오래된 회차부터 정리 — m_caps 도 함께)
        self._cluster_groups = {}   # 트리 표시 키 -> 원래 그룹 목록 (노드 라벨의 그룹별 계획 조회)
        self.m_procs = []

        # 메시지 언어 (메인 창의 한/영 콤보 설정을 공유)
        lang = QtCore.QSettings(SETTING_COMPANY, SETTING_APP).value('ui_lang')
        self.m_ko = (lang is None or int(lang) == 0)
        self.ui.btnDissolveGroup.setText('Group 해제' if self.m_ko else 'Dissolve Group')
        self.ui.btnDissolveGroup.setToolTip(
            '완료 후 유지 중인 그룹을 해제합니다' if self.m_ko
            else 'Dissolve the group kept after completion')
        self.ui.lbJnpCoalition.setText(
            'Coalition: (없음) — JnP 에이전트를 시작하고 협업 태스크를 발행하면 여기에 표시됩니다'
            if self.m_ko else
            'Coalition: (none) — start JnP agents and publish a collaboration task')

        # 'Group 해제' 버튼 — 완료 후 유지(team) 중인 그룹에 해제 명령 발행.
        # task 실행 중(forming/running)에는 비활성 — 완료(success/failed) 시에만 활성
        self.ui.btnDissolveGroup.setEnabled(False)
        self.ui.btnDissolveGroup.clicked.connect(self._dissolve_group)

        # coalition 라벨의 최소폭을 명시적으로 고정 — 라벨 최소폭이 '전체 문구 폭'이라
        # 그룹이 늘 때마다 창 최소폭이 무한정 커지고(2그룹 실측 1090px) 떠 있는 창이
        # 저절로 넓어진다. 명시 최소폭이 sizeHint 를 대체하므로 라벨이 압축되고,
        # 전체 문구는 툴팁으로 보여준다(_redraw 에서 설정).
        self.ui.lbJnpCoalition.setMinimumWidth(200)

        # ── 미션 → 분할된 subtask → 스킬 매칭 패널 (에이전트|트리 아래, 로그 위) ──
        self.m_lbPlanTitle = QtWidgets.QLabel(
            'Mission → Decomposition → Skill matching  (/jnp/plan)' if not self.m_ko
            else '미션 → 작업 분할(subtask) → 스킬 매칭  (/jnp/plan)')
        pf = self.m_lbPlanTitle.font(); pf.setPointSize(11); pf.setBold(True); self.m_lbPlanTitle.setFont(pf)
        self.m_tbPlan = QtWidgets.QTextBrowser(self)
        self.m_tbPlan.setMinimumHeight(170)
        self.m_tbPlan.setMaximumHeight(380)
        self.m_tbPlan.setOpenExternalLinks(False)
        self.m_tbPlan.setHtml(build_plan_html({}, {}, self.m_ko))
        planBox = QtWidgets.QWidget(self)
        pl = QtWidgets.QVBoxLayout(planBox); pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(2)
        pl.addWidget(self.m_lbPlanTitle); pl.addWidget(self.m_tbPlan)
        self.ui.verticalLayout.insertWidget(2, planBox)

        # 토픽 구독은 소형 rospy tap 서브프로세스로 (GUI 프로세스를 ROS 노드로 만들지 않음
        # — master 재시작에도 창만 다시 열면 복구되는 단순한 구조).
        # ★ rostopic echo 는 긴 문자열을 이스케이프+줄바꿈 랩핑해 줄 단위 파싱이 깨진다(실측)
        #   → 원문 그대로 '한 줄 = 한 메시지'를 보장하는 tap 을 쓴다.
        self._spawn_watch('/jnp/status', self._on_status_line)
        self._spawn_watch(CMD_ROS_JNP082_TASK_TOPIC, self._on_event_line)
        self._spawn_watch('/jnp/plan', self._on_plan_line)        # latched — 늦게 열어도 마지막 계획을 받는다

        # RTF/Sim/Real 표시 — /clock 을 2초 간격으로 샘플하는 tap (성능 부담 없음)
        self.m_clock_prev = None
        self.m_sim_t = None
        self.m_rtf = None
        self.m_dissolved_group = None
        self._spawn_clock_watch()
        self.m_statTimer = QtCore.QTimer(self)
        self.m_statTimer.timeout.connect(self._update_stats)
        self.m_statTimer.start(1000)

        # 트리 뷰 줌: 마우스 휠 (위=확대, 아래=축소)
        self.ui.gvJnpTree.viewport().installEventFilter(self)

    # 마우스 휠로 트리 확대/축소

    def showEvent(self, ev):
        # 부모 종속(transient) 힌트 제거 — transient 창엔 최대화를 막는 WM 대비
        try:
            wh = self.windowHandle()
            if wh is not None and wh.transientParent() is not None:
                wh.setTransientParent(None)
        except Exception:
            pass
        super().showEvent(ev)

    # 전체화면 토글 (F11)
    def _toggle_fullscreen(self):
        if self.isFullScreen():
            # showNormal()은 최대화 상태까지 지운다 — FullScreen 비트만 내려서
            # '최대화 → F11 → F11' 후에도 최대화가 유지되게 한다
            self.setWindowState(self.windowState() & ~QtCore.Qt.WindowFullScreen)
        else:
            self.showFullScreen()

    def keyPressEvent(self, ev):
        # F11 = 전체화면 토글 (2026-08-10)
        if ev.key() == QtCore.Qt.Key_F11:
            self._toggle_fullscreen()
            return
        # 전체화면 중 Esc = 창 닫기가 아니라 전체화면 해제 (통상 UX)
        if ev.key() == QtCore.Qt.Key_Escape and self.isFullScreen():
            self._toggle_fullscreen()
            return
        super().keyPressEvent(ev)

    def eventFilter(self, obj, ev):
        if obj is self.ui.gvJnpTree.viewport() and ev.type() == QtCore.QEvent.Wheel:
            factor = 1.15 if ev.angleDelta().y() > 0 else 1 / 1.15
            self.ui.gvJnpTree.scale(factor, factor)
            return True
        return super().eventFilter(obj, ev)

    # /clock 2초 샘플 tap (throttle 은 tap 안에서 — 콜백 폭주 방지)
    CLOCK_CODE = ("import rospy, time; from rosgraph_msgs.msg import Clock; "
                  "rospy.init_node('jnp_mon_clock', anonymous=True); last=[0.0]; "
                  "cb=lambda m: (last.__setitem__(0, time.time()), "
                  "print(m.clock.secs + m.clock.nsecs*1e-9, flush=True)) "
                  "if time.time()-last[0]>=2.0 else None; "
                  "rospy.Subscriber('/clock', Clock, cb); rospy.spin()")

    def _spawn_clock_watch(self):
        proc = QtCore.QProcess(self)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        proc.setProcessEnvironment(env)
        proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        cmd = ("source /opt/ros/noetic/setup.bash; " + PATH_SOURCE_JNP082_SETUP
               + "; python3 -c \"" + self.CLOCK_CODE + "\"")
        proc.start("bash", ["-c", cmd])
        proc.readyReadStandardOutput.connect(
            lambda p=proc: self._drain(p, self._on_clock_line))
        self.m_procs.append(proc)

    def _on_clock_line(self, line):
        try:
            sim_t = float(line)
        except ValueError:
            return
        now = time.time()
        if self.m_clock_prev is not None:
            dw = now - self.m_clock_prev[0]
            ds = sim_t - self.m_clock_prev[1]
            if dw > 0.5:
                self.m_rtf = max(0.0, ds / dw)
        # 시뮬 재시작 감지(클록 후퇴) — Real 기준점 재고정
        if self.m_sim_t is not None and sim_t < self.m_sim_t - 5:
            self.m_real0 = None
        if getattr(self, 'm_real0', None) is None:
            # Real = Gazebo 와 같은 기준(gzserver 시작 시각)의 벽시계 경과 시간
            try:
                out = subprocess.check_output(
                    ['bash', '-c',
                     "ps -o etimes= -p $(pgrep -f 'gz[s]erver' | head -1)"],
                    timeout=3).decode().strip()
                self.m_real0 = now - float(out)
            except Exception:
                self.m_real0 = now          # gzserver 미발견 — 지금부터 경과
        self.m_clock_prev = (now, sim_t)
        self.m_sim_t = sim_t

    def _update_stats(self):
        def hms(t):
            t = int(t)
            return "%02d:%02d:%02d" % (t // 3600, (t % 3600) // 60, t % 60)
        rtf_s = ("%.2f" % self.m_rtf) if self.m_rtf is not None else '--'
        sim_s = hms(self.m_sim_t) if self.m_sim_t is not None else '--'
        # Real = 시뮬(gzserver) 시작부터의 벽시계 경과 — Gazebo 하단 Real Time 과 동일 기준
        # (이전엔 '현재 시각'을 표시해 Gazebo 와 전혀 안 맞았음 — 2026-08-08 수정)
        real_s = (hms(time.time() - self.m_real0)
                  if getattr(self, 'm_real0', None) is not None else '--')
        self.ui.lbSimStats.setText(f"RTF {rtf_s} | Sim {sim_s} | Real {real_s}")

    # 메시지 data 를 한 줄씩 그대로 찍는 rospy tap (flush 필수 — 파이프 블록버퍼 함정)
    # rospy 구독 콜백은 여러 스레드에서 동시에 돈다. print() 는 본문과 개행을 따로
    # 내보내므로 두 메시지가 겹치면 'new:AAAnew:BBB' 처럼 한 줄로 붙어 버린다(실측).
    # → 락으로 직렬화하고 본문+개행을 한 번의 write 로 내보낸다.
    TAP_CODE = ("import rospy, sys, threading; from std_msgs.msg import String; "
                "rospy.init_node('jnp_mon_tap', anonymous=True); "
                "_lk = threading.Lock(); "
                "_w = lambda s: (_lk.acquire(), sys.stdout.write(s + chr(10)), "
                "sys.stdout.flush(), _lk.release()); "
                "rospy.Subscriber('{t}', String, lambda m: _w(m.data)); "
                "rospy.spin()")

    def _spawn_watch(self, topic, handler):
        proc = QtCore.QProcess(self)
        env = QtCore.QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        proc.setProcessEnvironment(env)
        proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        cmd = ("source /opt/ros/noetic/setup.bash; " + PATH_SOURCE_JNP082_SETUP
               + "; python3 -c \"" + self.TAP_CODE.format(t=topic) + "\"")
        proc.start("bash", ["-c", cmd])
        proc.readyReadStandardOutput.connect(
            lambda p=proc, h=handler: self._drain(p, h))
        self.m_procs.append(proc)

    def _drain(self, proc, handler):
        while proc.canReadLine():
            line = bytes(proc.readLine()).decode('utf-8', 'replace').strip()
            if not line:
                continue
            handler(line)

    # /jnp/plan : 작업 분할 기록 JSON (그룹이 트리를 만들 때 1회, latched)
    def _on_plan_line(self, line):
        try:
            rec = json.loads(line)
        except ValueError:
            return
        if not isinstance(rec, dict) or not isinstance(rec.get('subtasks', []), list):
            self._log('[진단] /jnp/plan 형식 오류(객체가 아님) — 무시' if self.m_ko else '[diag] malformed /jnp/plan record ignored')
            return
        grp = rec.get('group') or '?'
        self.m_plans[grp] = rec
        # 새 계획의 표시 상태 = 같은 run_id 로 먼저 도착해 둔 상태(있으면) — 다른 회차 상태는 끊되 버리지 않고 회차 보관함에 둔다
        self._select_display_status(grp)
        n = len(rec.get('subtasks') or [])
        if rec.get('source') == 'plan':
            tag = (' [example — 사람이 쓴 템플릿]' if self.m_ko else ' [example — hand-written template]') \
                if (rec.get('plan_source') or '').lower() == 'example' else ''
            self._log((f"작업 분할: {grp} goal={rec.get('goal')} ← {rec.get('plan_name')}{tag} → subtask {n}개"
                       if self.m_ko else f"decomposition: {grp} goal={rec.get('goal')} ← {rec.get('plan_name')}{tag} → {n} subtasks"))
            if rec.get('task_description'):
                self._log(("미션: " if self.m_ko else "mission: ") + rec['task_description'])
        else:
            self._log((f"작업 분할 대체: {grp} 고정 빌더 — {rec.get('reason')}" if self.m_ko
                       else f"decomposition fallback: {grp} fixed builder — {rec.get('reason')}"))
        self._redraw()          # 트리 라벨(스킬·요구 능력)도 갱신
        self._redraw_plan()

    def _redraw_plan(self):
        self.m_tbPlan.setHtml(build_plan_html(self.m_plans, self.m_statuses, self.m_ko, self.m_caps))

    def _plan_row(self, groups, node_name):
        """실행 node 이름 → 계획 기록의 subtask 행 — 지정 그룹들 안에서, 상태와 같은 run_id 의 계획만(모호하면 None)."""
        return plan_row_for(self.m_plans, self.m_statuses, groups, node_name)

    def _select_display_status(self, grp):
        """그룹의 표시 상태를 정한다: 계획이 있으면 그 run_id 의 상태(없으면 표시 없음 → '상태 미확인'),
        계획이 없으면 가장 최근에 수용한 회차의 상태(계획 없는 구버전 그룹 정책)."""
        rec = self.m_plans.get(grp)
        if rec:
            run = self.m_runs.get((grp, rec.get('run_id') or ''))
        else:
            runs = [(v['order'], v) for (g, _r), v in self.m_runs.items() if g == grp]
            run = max(runs)[1] if runs else None
        if run:
            self.m_statuses[grp] = run['status']
            self.m_status = run['status']
            if run['status'].get('state') == 'dissolved':
                self.m_dissolved.add(grp)
            else:
                self.m_dissolved.discard(grp)
        else:
            self.m_statuses.pop(grp, None)
            self.m_dissolved.discard(grp)

    def _prune_runs(self, grp):
        keys = sorted([k for k in self.m_runs if k[0] == grp], key=lambda k: self.m_runs[k]['order'])
        for k in keys[:-self.MAX_RUNS_PER_GROUP]:
            self.m_runs.pop(k, None)
            self.m_caps.pop(k, None)

    # /jnp/status : 그룹 상태 JSON — 회차(run_id)별로 보관·판정 (2차 검수 R2-M1a)
    def _on_status_line(self, line):
        try:
            status = json.loads(line)
        except ValueError:
            return
        if not isinstance(status, dict):
            return
        grp = status.get('group') or '?'
        rid = status.get('run_id') or ''
        key = (grp, rid)
        run = self.m_runs.get(key)
        # 같은 회차의 dissolved 는 최종 — 그 뒤에 오는 같은 회차의 forming/running/success/failed 는 수용하지 않는다.
        # (다른 회차의 해체 표식은 이 회차를 막지 않는다: 키가 다르다.)
        if run and run['dissolved'] and status.get('state') != 'dissolved':
            return
        # 트리가 빠진 상태 발행에도 마지막 트리를 유지 — 같은 회차의 보관 상태에서만
        if not status.get('tree') and run and run['status'].get('tree'):
            status['tree'] = run['status']['tree']
        # 수용 확정 → 그 뒤에만 보유 능력 이력을 갱신한다(거부된 잔여 상태가 마지막 관측 cap 을 바꾸지 않게)
        self.m_run_seq += 1
        self.m_runs[key] = {'status': status, 'dissolved': bool(run and run['dissolved']) or status.get('state') == 'dissolved',
                            'order': self.m_run_seq}
        if rid:
            hist = self.m_caps.setdefault(key, {})
            for m in status.get('members') or []:
                if isinstance(m, dict) and m.get('name') and isinstance(m.get('cap'), list):
                    hist[m['name']] = list(m['cap'])
        self._prune_runs(grp)
        prev = self.m_statuses.get(grp)
        prev_state = prev.get('state') if prev else None
        self._select_display_status(grp)
        cur = self.m_statuses.get(grp)
        if cur is status and status.get('state') != prev_state:
            self._log(f"coalition [{status.get('group','?')}] "
                      f"{prev_state or '-'} → {status.get('state')} "
                      f"({status.get('note','')})")
        elif cur is not status:
            self._log((f"[다른 회차 상태 보관] {grp} run={rid or '-'} state={status.get('state')} — 현재 계획의 회차가 아니라 표시하지 않음"
                       if self.m_ko else f"[other-run status kept] {grp} run={rid or '-'} state={status.get('state')} — not the current plan's run"))
        self._redraw()
        self._redraw_plan()

    # /jnp_agent_join_event : new / kill / task
    def _on_event_line(self, line):
        # 두 메시지가 한 줄로 붙어 들어오더라도(tap 쪽을 고쳤지만 과거 로그·경합 대비)
        # 접두어마다 잘라 각각 처리한다. 자르지 않으면 뒤 메시지가 앞 이름에 흡수되어
        # '/etri/tb3_waffle_0new:/etri/locobot_0' 같은 유령 에이전트가 생긴다.
        parts = [p for p in re.split(r'(?=(?:new|kill|task):)', line) if p]
        if len(parts) > 1:
            # 합쳐진 경로가 아직 규명되지 않았다. 다음 재현 때 정체를 알 수 있도록
            # 원문을 그대로 남긴다(따옴표 포함 — 눈에 안 보이는 문자까지 드러나게).
            self._log(f"[진단] 합쳐진 이벤트 원문: {line!r}")
            for p in parts:
                self._on_one_event(p)
            self._refresh_agents()
            return
        self._on_one_event(line)
        self._refresh_agents()

    def _on_one_event(self, line):
        if line.startswith('new:'):
            name = line[4:]
            if self.m_agents.get(name) != 'alive':
                self.m_agents[name] = 'alive'
                self._log(f"discovery: {name} 합류" if self.m_ko else f"discovery: {name} joined")
        elif line.startswith('kill:'):
            name = line[5:]
            if 'group' in name:
                self._log(f"그룹 해제 통지: {name}" if self.m_ko else f"group dissolved: {name}")
            elif name in self.m_agents:
                self.m_agents[name] = 'killed'
                self._log(f"이탈: {name}" if self.m_ko else f"left: {name}")
        elif line.startswith('task:'):
            self._log(f"task 발행: {line[5:]}" if self.m_ko else f"task published: {line[5:]}")

    # 'Group 해제' — 현재 그룹에 dissolve 명령 발행 (그룹이 kill 발행 후 종료)
    def _dissolve_group(self):
        targets = [g for g, st in self.m_statuses.items()
                   if st.get('state') in ('success', 'failed')]
        for group in targets:
            cmd = ("source /opt/ros/noetic/setup.bash; " + PATH_SOURCE_JNP082_SETUP
                   + "; rostopic pub -1 " + CMD_ROS_JNP082_TASK_TOPIC
                   + " std_msgs/String \"data: 'dissolve:" + group + "'\"")
            QtCore.QProcess.startDetached("bash", ["-c", cmd])
            self._log(f"그룹 해제 명령 발행: {group}" if self.m_ko
                      else f"dissolve command published: {group}")
        if targets:
            return
        group = (self.m_status or {}).get('group')
        if not group:
            self._log("해제할 그룹이 없습니다 (coalition 미형성)" if self.m_ko
                      else "no group to dissolve (no coalition formed)")
            return
        cmd = ("source /opt/ros/noetic/setup.bash; " + PATH_SOURCE_JNP082_SETUP
               + "; rostopic pub -1 " + CMD_ROS_JNP082_TASK_TOPIC
               + " std_msgs/String \"data: 'dissolve:" + group + "'\"")
        QtCore.QProcess.startDetached("bash", ["-c", cmd])
        self._log(f"그룹 해제 명령 발행: {group}" if self.m_ko
                  else f"dissolve command published: {group}")

    def _log(self, msg):
        stamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.ui.pteJnpLog.appendPlainText(f"[{stamp}] {msg}")

    def _refresh_agents(self):
        self.ui.lstJnpAgents.clear()
        known = dict(self.m_agents)
        in_group = set()
        # ── 그룹별 섹션 (다중 coalition) ──
        for grp in sorted(self.m_statuses):
            st = self.m_statuses[grp]
            if st.get('state') == 'dissolved':
                continue
            members = [m['name'] for m in st.get('members', [])]
            for m in members:
                known.setdefault(m, 'alive')
                in_group.add(m)
            # 빈 그룹(전원 이적/방출)도 헤더는 표시 — 그룹 생존과 명단을 구분해 보이게
            if members:
                txt = "▼ %s (goal=%s)" % (grp, st.get('goal', ''))
            else:
                note = '빈 그룹 — 전원 이적/방출' if self.m_ko else 'empty — all released'
                txt = "▼ %s (goal=%s)  [%s]" % (grp, st.get('goal', ''), note)
            hdr = QtWidgets.QListWidgetItem(txt)
            f = hdr.font(); f.setBold(True); hdr.setFont(f)
            hdr.setForeground(QtGui.QColor('#ffd54f'))
            self.ui.lstJnpAgents.addItem(hdr)
            caps = {mm.get('name'): mm.get('cap') or [] for mm in st.get('members', [])}
            for m in members:
                it = QtWidgets.QListWidgetItem("      ● " + m)
                it.setForeground(COLOR_DONE)
                if caps.get(m):
                    it.setToolTip('capability: ' + ', '.join(caps[m]))
                self.ui.lstJnpAgents.addItem(it)
                if caps.get(m):      # 보유 능력(스킬 매칭의 근거)을 한 줄 아래에
                    sub = QtWidgets.QListWidgetItem("          [" + ', '.join(caps[m]) + "]")
                    sub.setForeground(QtGui.QColor('#90a4ae'))
                    self.ui.lstJnpAgents.addItem(sub)
        grouped = bool(in_group)
        # ── 미소속 에이전트 ──
        rest = [(n, st) for n, st in sorted(known.items())
                if 'group' not in n and n not in in_group]
        if rest and grouped:
            sep = QtWidgets.QListWidgetItem('미소속:' if self.m_ko else 'Ungrouped:')
            sep.setForeground(COLOR_WAIT)
            self.ui.lstJnpAgents.addItem(sep)
        for name, state in rest:
            item = QtWidgets.QListWidgetItem(("● " if state == 'alive' else "○ ") + name)
            item.setForeground(COLOR_DONE if state == 'alive' else COLOR_WAIT)
            self.ui.lstJnpAgents.addItem(item)

    # ---------- Task tree 그리기 ----------
    def _redraw(self):
        self._refresh_agents()
        s = self.m_status
        if not s:
            return
        # ── 다중 그룹 요약 바 ──
        parts = []
        any_done = False
        for grp in sorted(self.m_statuses):
            st = self.m_statuses[grp]
            state = st.get('state', '?')
            color = {'forming': '#ffc107', 'running': '#03a9f4', 'success': '#4caf50',
                     'failed': '#f44336', 'dissolved': '#9e9e9e'}.get(state, '#e8e8e8')
            parts.append(f"{grp}(goal={st.get('goal','')}): "
                         f"<span style='color:{color}'><b>{state}</b></span>")
            if state in ('success', 'failed'):
                any_done = True
        if parts:
            self.ui.lbJnpCoalition.setText("   |   ".join(parts))
            # 라벨이 압축돼 잘릴 수 있으므로 전체 문구는 툴팁으로
            self.ui.lbJnpCoalition.setToolTip("\n".join(parts))
        # 해제 버튼: 완료(success/failed) 그룹이 하나라도 있으면 활성
        self.ui.btnDissolveGroup.setEnabled(any_done)
        # ── 그룹별 트리를 세로로 쌓아 그리기 ──
        self.m_scene.clear()
        # 루트 task 이름이 같은 그룹들(다목적 이동의 goal별 부분집합 coalition —
        # G1/G2 가 별도 그룹이지만 논리적으론 한 task)은 트리를 하나로 합쳐
        # 표시한다 (2026-08-10 지시: "task tree 는 하나여야")
        clusters = {}
        for grp in sorted(self.m_statuses):
            st = self.m_statuses[grp]
            root = (st.get('tree') or {}).get('name')
            clusters.setdefault(root or grp, []).append((grp, st))
        display = {}
        self._cluster_groups = {}
        for key, lst in clusters.items():
            if len(lst) == 1 or not lst[0][1].get('tree'):
                for g, st in lst:
                    display[g] = dict(st, tree=_tag_tree(st.get('tree'), g)) if st.get('tree') else st
                    self._cluster_groups[g] = [g]
                continue
            self._cluster_groups[' + '.join(g for g, _ in lst)] = [g for g, _ in lst]
            states = [st.get('state', '?') for _, st in lst]
            state = ('running' if 'running' in states else
                     'forming' if 'forming' in states else states[0])
            roots = [st['tree'] for _, st in lst]
            children = []
            for g, st in lst:
                # 합쳐 그려도 node 는 원래 그룹을 기억한다(R2-M1c) — 라벨 조회는 그 그룹의 계획·회차에서만
                children.extend(_tag_tree(st['tree'], g).get('children') or [])
            display[' + '.join(g for g, _ in lst)] = {
                'state': state,
                'tree': {'name': roots[0].get('name'),
                         'kind': roots[0].get('kind', 'composite'),
                         'state': ('done' if all(
                             r.get('state') == 'done' for r in roots) else ''),
                         'children': children}}
        y_off = 0.0
        for grp in sorted(display):
            st = display[grp]
            tree = st.get('tree')
            if not tree:
                continue
            state = st.get('state', '?')
            before = set(self.m_scene.items())
            cap = QtWidgets.QGraphicsSimpleTextItem(f"{grp}  [{state}]")
            cf = cap.font()
            cf.setPointSize(13)
            cf.setBold(True)
            cap.setFont(cf)
            cap.setBrush(QtGui.QBrush(QtGui.QColor(
                '#d32f2f' if state == 'dissolved' else '#37474f')))
            cap.setPos(0, -34)
            self.m_scene.addItem(cap)
            self._cur_groups = self._cluster_groups.get(grp, [grp])
            self._layout_tree(tree, 0, 0)
            new_items = [it for it in self.m_scene.items() if it not in before]
            if state == 'dissolved':
                for it in new_items:
                    it.setOpacity(0.35)
                cap.setOpacity(1.0)
            h_min = min(it.sceneBoundingRect().top() for it in new_items)
            h_max = max(it.sceneBoundingRect().bottom() for it in new_items)
            for it in new_items:
                it.moveBy(0, y_off - h_min)
            y_off += (h_max - h_min) + 60
        self.ui.gvJnpTree.setSceneRect(self.m_scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))

    def _leaf_count(self, node):
        ch = node.get('children') or []
        return max(1, sum(self._leaf_count(c) for c in ch)) if ch else 1

    def _layout_tree(self, node, x, depth):
        """재귀 배치: 리프 수 기반 좌표 계산 후 노드 상자·간선 그리기.
        반환 = (subtree 폭(px), 이 노드의 중심 x)"""
        y = depth * (NODE_H + GAP_Y)
        ch = node.get('children') or []
        if not ch:
            cx = x + NODE_W / 2
            self._draw_node(node, x, y)
            return NODE_W + GAP_X, cx
        total_w = 0
        centers = []
        for c in ch:
            w, ccx = self._layout_tree(c, x + total_w, depth + 1)
            centers.append(ccx)
            total_w += w
        cx = (centers[0] + centers[-1]) / 2
        self._draw_node(node, cx - NODE_W / 2, y)
        for ccx in centers:
            line = QtWidgets.QGraphicsLineItem(cx, y + NODE_H, ccx, y + NODE_H + GAP_Y)
            line.setPen(QtGui.QPen(COLOR_EDGE, 1.6))
            self.m_scene.addItem(line)
        return max(total_w, NODE_W + GAP_X), cx

    def _draw_node(self, node, x, y):
        kind = node.get('kind', 'atomic')
        state = node.get('state', '')
        if kind == 'atomic':
            fill = {'done': COLOR_DONE, 'running': COLOR_RUN}.get(state, COLOR_WAIT)
        else:
            fill = COLOR_DONE if state == 'done' else COLOR_COMPOSITE
        rect = QtWidgets.QGraphicsRectItem(x, y, NODE_W, NODE_H)
        rect.setBrush(QtGui.QBrush(fill))
        # 실행 중(NOW)은 굵은 빨간 테두리로 강조
        pen = QtGui.QPen(QtGui.QColor("#d32f2f"), 3) if state == 'running' \
            else QtGui.QPen(QtGui.QColor("#37474f"), 1)
        rect.setPen(pen)
        self.m_scene.addItem(rect)

        prefix = {'seq': '[S] ', 'par': '[P] '}.get(kind, '')
        label = prefix + node.get('name', '')
        agent = node.get('agent', '')
        owner = node.get('_grp')
        row = self._plan_row([owner] if owner else getattr(self, '_cur_groups', []), node.get('name')) if kind == 'atomic' else None
        if row and row.get('skill'):
            # 분할된 subtask 의 스킬과 요구 능력 — 스킬 매칭의 근거 (같은 회차의 계획 행만)
            label += "\n" + str(row['skill']) + " · " + ','.join(str(x) for x in (row.get('requirement') or []))
        if agent:
            # 할당 로봇 표기 — /etri/locobot_0 → locobot_0 (마지막 성분이 로봇 이름)
            label += "\n→ " + agent.strip('/').split('/')[-1]
        elif kind == 'atomic' and not (row and row.get('skill')):
            label += "\n(" + (node.get('goal', '') or '-')[:22] + ")"
        text = QtWidgets.QGraphicsSimpleTextItem(label)
        f = text.font()
        f.setPointSize(NODE_FONT_PT)
        f.setBold(True)                 # 전부 굵게 — 시인성
        text.setFont(f)
        text.setBrush(QtGui.QBrush(QtGui.QColor("#ffffff")))
        tb = text.boundingRect()
        text.setPos(x + (NODE_W - tb.width()) / 2, y + (NODE_H - tb.height()) / 2)
        self.m_scene.addItem(text)

    # 닫힐 때 워처 정리
    # tap 서브프로세스 정리 — 닫힘 경로가 둘이다:
    #  X 버튼 → closeEvent, Esc/reject() → done() (closeEvent 를 거치지 않음!)
    # 한쪽만 걸면 Esc 로 닫을 때 rospy tap 3개가 숨은 창에서 계속 돈다(누수).
    def _kill_taps(self):
        if getattr(self, '_taps_killed', False):
            return
        self._taps_killed = True
        self.m_statTimer.stop()
        for p in self.m_procs:
            p.kill()

    def done(self, r):
        self._kill_taps()
        super().done(r)

    def closeEvent(self, event):
        self._kill_taps()
        super().closeEvent(event)


# 단독 실행 (테스트/디버그용): python3 dlgJnpMonitor.py
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dlg = DialogJnpMonitor()
    dlg.show()
    sys.exit(app.exec())
