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


def build_plan_html(plans, statuses, ko=True):
    """[JnP-0.8.2 2026-10-14] '미션 → 분할된 subtask → 스킬 매칭' HTML.
    plans: 그룹명 -> /jnp/plan 기록(JSON), statuses: 그룹명 -> /jnp/status 상태(멤버 capability·트리 상태).
    행마다: canonical subtask(스킬·인수) → 요구 능력 → 실행 node → 배정 에이전트[보유 능력] → 매칭 → 상태."""
    if not plans:
        return ("<p style='color:#777'>%s</p>" % (
            '협업 태스크를 발행하면 미션의 분할 결과와 스킬 매칭이 여기에 표시됩니다' if ko
            else 'Publish a collaboration task to see the decomposition and skill matching'))
    out = ["<style>table{border-collapse:collapse} td,th{border:1px solid #cfd8dc;padding:2px 6px;font-size:12px} "
           "th{background:#eceff1} .ok{color:#2e7d32;font-weight:bold} .no{color:#c62828;font-weight:bold} "
           ".run{color:#f57c00;font-weight:bold} .done{color:#2e7d32} .wait{color:#757575}</style>"]
    for grp in sorted(plans):
        rec = plans[grp]
        st = statuses.get(grp) or {}
        caps = {m.get('name'): m.get('cap') or [] for m in st.get('members') or []}
        # 실행 트리 상태(노드 이름 → state/agent)
        node_state = {}

        def walk(n):
            if not n:
                return
            node_state[n.get('name')] = n
            for c in n.get('children') or []:
                walk(c)
        walk(st.get('tree'))
        src = rec.get('source', '?')
        psrc = (rec.get('plan_source') or 'unknown').lower()
        # 계획 출처 배지 — example: 사람이 LLM-TDM 형식으로 직접 쓴 템플릿(LLM-TDM 모듈 출력이 아님)
        if psrc == 'example':
            badge = ("<span style='background:#fff3e0;color:#e65100;border:1px solid #ffb74d;border-radius:3px;padding:0 4px;font-weight:bold'>EXAMPLE</span> "
                     + ("<span style='color:#8d6e63'>(사람이 쓴 분할 템플릿 — LLM-TDM 모듈 출력 아님)</span>" if ko
                        else "<span style='color:#8d6e63'>(hand-written template, not LLM-TDM output)</span>"))
        else:
            badge = "<span style='background:#e3f2fd;color:#0d47a1;border:1px solid #64b5f6;border-radius:3px;padding:0 4px;font-weight:bold'>%s</span>" % _esc(psrc.upper())
        head = "<b>%s</b> &nbsp; goal=<b>%s</b> &nbsp; %s" % (_esc(grp), _esc(rec.get('goal', '')),
               ("분할 계획 <code>%s</code> %s" % (_esc(rec.get('plan_name') or ''), badge)) if src == 'plan' and ko else
               ("plan <code>%s</code> %s" % (_esc(rec.get('plan_name') or ''), badge)) if src == 'plan' else
               ("<span class='no'>%s</span> (%s)" % ('고정 빌더로 대체' if ko else 'fixed builder (fallback)', _esc(rec.get('reason', '')))))
        out.append("<p style='margin:4px 0'>%s</p>" % head)
        desc = rec.get('task_description') or ''
        if desc:
            out.append("<p style='margin:2px 0'><b>%s</b> <i>%s</i></p>" % (
                ('미션(자연어, example):' if psrc == 'example' else '미션(자연어):') if ko
                else ('Mission (example):' if psrc == 'example' else 'Mission:'), _esc(desc)))
        b = rec.get('bindings') or {}
        if b:
            bs = '; '.join('%s=%s' % (k, json.dumps(v, ensure_ascii=False)) for k, v in b.items())
            out.append("<p style='margin:2px 0;color:#455a64'><b>%s</b> %s</p>" % ('바인딩(payload→상수):' if ko else 'bindings:', _esc(bs)[:600]))
        rows = rec.get('subtasks') or []
        if ko:
            out.append("<table><tr><th>#</th><th>분할된 subtask (스킬·인수)</th><th>요구 능력</th><th>실행 node</th>"
                       "<th>배정 에이전트 [보유 능력]</th><th>매칭</th><th>상태</th></tr>")
        else:
            out.append("<table><tr><th>#</th><th>subtask (skill·args)</th><th>needs</th><th>exec node</th>"
                       "<th>agent [capabilities]</th><th>match</th><th>state</th></tr>")
        for i, r in enumerate(rows, 1):
            skill = r.get('skill')
            args = r.get('args') or {}
            sub = ("%s(%s)" % (skill, ', '.join('%s=%s' % (k, v) for k, v in args.items()))) if skill                 else (r.get('exec_goal') or '')
            extra = [x for x in (r.get('required_skills') or []) if x != skill]
            if extra:
                sub += " +" + ','.join(extra)
            req = r.get('requirement') or []
            ns = node_state.get(r.get('node')) or {}
            agent = ns.get('agent') or r.get('preassigned_agent') or ''
            state = ns.get('state') or ('wait' if not r.get('preassigned') else 'service')
            if r.get('preassigned'):
                match = "<span class='ok'>%s</span>" % ('상시 서비스' if ko else 'standing service')
                agent_txt = _esc(agent.strip('/').split('/')[-1] if agent else '')
            elif 'virtual' in req:
                match = "<span class='wait'>%s</span>" % ('그룹이 완료 처리' if ko else 'completed by group')
                agent_txt = '—'
            elif agent:
                have = caps.get(agent) or caps.get('/' + agent.strip('/')) or []
                ok = set(req) <= set(have)
                match = "<span class='%s'>%s</span>" % ('ok' if ok else 'no', ('✓ ' if ok else '✗ ') + '⊆'.join([','.join(req), '{' + ','.join(have) + '}']))
                agent_txt = "%s [%s]" % (_esc(agent.strip('/').split('/')[-1]), _esc(','.join(have)))
            else:
                # 미배정 — 요구 능력을 가진 후보 멤버 수를 보여 준다
                cands = [n.strip('/').split('/')[-1] for n, c in caps.items() if set(req) <= set(c or [])]
                match = "<span class='wait'>%s %s</span>" % ('후보' if ko else 'candidates', _esc(','.join(cands)) or '0')
                agent_txt = ('(미배정)' if ko else '(unassigned)')
            st_txt = {'running': ('실행 중' if ko else 'running'), 'done': ('완료' if ko else 'done'),
                      'wait': ('대기' if ko else 'wait'), 'service': ('상시' if ko else 'service')}.get(state, state)
            out.append("<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%s</td></tr>" % (
                i, _esc(sub), _esc(','.join(req)) + (' (optional)' if r.get('optional') else ''), _esc(r.get('node', '')),
                agent_txt, match, state if state in ('running', 'done', 'wait') else 'wait', _esc(st_txt)))
        out.append("</table>")
        if rec.get('warnings'):
            out.append("<p style='color:#8d6e63;margin:2px 0'>%s %s</p>" % ('변환 경고:' if ko else 'warnings:', _esc('; '.join(rec['warnings']))))
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
        self.m_tbPlan.setMinimumHeight(150)
        self.m_tbPlan.setMaximumHeight(300)
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
        grp = rec.get('group') or '?'
        self.m_plans[grp] = rec
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
        self._redraw_plan()

    def _redraw_plan(self):
        self.m_tbPlan.setHtml(build_plan_html(self.m_plans, self.m_statuses, self.m_ko))

    def _plan_row(self, node_name):
        """실행 node 이름 → 계획 기록의 subtask 행 (트리 노드 라벨에 스킬·요구 능력을 쓰기 위해)."""
        for rec in self.m_plans.values():
            for r in rec.get('subtasks') or []:
                if r.get('node') == node_name:
                    return r
        return None

    # /jnp/status : 그룹 상태 JSON
    def _on_status_line(self, line):
        try:
            status = json.loads(line)
        except ValueError:
            return
        grp = status.get('group') or '?'
        # 해체 이후 늦게 도착하는 완료 상태는 무시 (해체가 최종 — 역전 레이스 방어)
        if grp in self.m_dissolved and status.get('state') in ('success', 'failed'):
            return
        if status.get('state') == 'dissolved':
            self.m_dissolved.add(grp)
        elif status.get('state') in ('forming', 'running'):
            self.m_dissolved.discard(grp)
        prev = self.m_statuses.get(grp)
        prev_state = prev.get('state') if prev else None
        # 트리가 빠진 상태 발행에도 마지막 트리를 유지 (그룹별)
        if not status.get('tree') and prev and prev.get('tree'):
            status['tree'] = prev['tree']
        self.m_statuses[grp] = status
        self.m_status = status
        if status.get('state') != prev_state:
            self._log(f"coalition [{status.get('group','?')}] "
                      f"{prev_state or '-'} → {status.get('state')} "
                      f"({status.get('note','')})")
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
        for key, lst in clusters.items():
            if len(lst) == 1 or not lst[0][1].get('tree'):
                display.update(dict(lst))
                continue
            states = [st.get('state', '?') for _, st in lst]
            state = ('running' if 'running' in states else
                     'forming' if 'forming' in states else states[0])
            roots = [st['tree'] for _, st in lst]
            children = []
            for r in roots:
                children.extend(r.get('children') or [])
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
        row = self._plan_row(node.get('name')) if kind == 'atomic' else None
        if row and row.get('skill'):
            # 분할된 subtask 의 스킬과 요구 능력 — 스킬 매칭의 근거
            label += "\n" + row['skill'] + " · " + ','.join(row.get('requirement') or [])
        if agent:
            # 할당 로봇 표기 — /etri/locobot_0 → locobot_0 (마지막 성분이 로봇 이름)
            label += "\n→ " + agent.strip('/').split('/')[-1]
        elif kind == 'atomic' and not row:
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
