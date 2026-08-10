# -*- coding: utf-8 -*-
"""Nav 설정 다이얼로그 — 매 시뮬레이션(협업 Start)마다 반영되는 항법 파라미터.

핵심 프리셋(로봇 계열별 4개 + 공통 2개)만 노출한다. '기본값'은 현재 검증된
프로파일(설정 파일 실측, 2026-08-08)이고, 기본값과 다른 항목만 오버라이드로
내보내므로 만지지 않으면 동작이 완전히 동일하다. 값은 QSettings 에 저장되어
GUI 재시작 후에도 유지되며, Start 시 main.py 가 nav_overrides.launch 를 생성한다.
Baseline(단독 주행) launch 에는 연결되지 않는다.

2026-08-10 태스크별 스코프 추가: Start Collaboration Task 다이얼로그에서 열면
해당 태스크 전용(nav/<TASK>/...) 키로 저장되고, 그 태스크가 실제 사용하는 로봇
계열만 노출한다. 값 우선순위 = 태스크 전용 → 공통 → 기본값.
"""
from PySide6 import QtWidgets, QtCore, QtGui
import subprocess
import threading

# ★ 설정 저장소 통일 (2026-08-10): 이전 버전은 자체 앱 이름("Multi-Agent-Simulator")
#   저장소에 쓰는데 main.py 는 constant 의 "ROSSimulator" 저장소를 읽어
#   nav_overrides 를 생성했다 — 다이얼로그에서 저장해도 Start 에 반영되지 않던
#   실버그. constant 식별자로 통일하고 옛 저장소의 nav/* 키는 1회 이관한다.
try:
    from constant import SETTING_COMPANY, SETTING_APP
except Exception:                       # 단독 실행 폴백
    SETTING_COMPANY, SETTING_APP = "ETRI", "ROSSimulator"
_OLD_APP = "Multi-Agent-Simulator"


def _migrate_old_nav(settings):
    """옛 저장소(ETRI/Multi-Agent-Simulator)의 nav/* 키를 새 저장소로 1회 이관.
    새 저장소에 이미 있는 키는 보존(멱등)."""
    try:
        if str(settings.value('nav/_migrated') or '') == '1':
            return
        old = QtCore.QSettings(SETTING_COMPANY, _OLD_APP)
        for k in old.allKeys():
            if k.startswith('nav/') and settings.value(k) is None:
                settings.setValue(k, old.value(k))
        settings.setValue('nav/_migrated', '1')
        settings.sync()
    except Exception:
        pass


# (키, 라벨, 로봇계열별 기본값 {loco, tb3, waffle}, 최소, 최대, 소수자리)
NAV_FIELDS = [
    ('max_vel',   '최대 속도 max_vel_x (m/s)',        {'loco': 0.50, 'tb3': 0.22, 'waffle': 0.26}, 0.05, 1.5, 2),
    ('inflation', '안전 여유 inflation_radius (m)',   {'loco': 0.30, 'tb3': 1.00, 'waffle': 1.00}, 0.05, 2.0, 2),
    ('xy_tol',    '도착 허용 거리 xy_tolerance (m)',  {'loco': 0.10, 'tb3': 0.05, 'waffle': 0.05}, 0.02, 1.0, 2),
    ('yaw_tol',   '도착 허용 각도 yaw_tolerance (rad)', {'loco': 0.40, 'tb3': 0.17, 'waffle': 0.17}, 0.05, 3.14, 2),
]
# 플래너 선택 (재시작 시 적용 — move_base 는 기동 시에만 읽음)
NAV_PLANNERS = [
    ('loco_global', 'LoCoBot global planner',
     ['자동 (기본)', 'NavfnROS', 'GlobalPlanner']),
    ('loco_local', 'LoCoBot local planner',
     ['자동 (기본)', 'DWA', 'TrajectoryPlanner']),
    ('tb3_global', 'TB3 global planner',
     ['자동 (기본)', 'NavfnROS', 'GlobalPlanner']),
    # 지도제작/물건찾기 waffle SLAM 선택 — nav_overrides 미출력, main.py 가
    # Start 때 waffle_slam:= launch arg 로 전달 (재시작 시 반영)
    ('waffle_slam', 'Waffle SLAM',
     ['slam_toolbox (기본)', 'gmapping', 'rtabmap']),
]

NAV_CHECKS = [
    ('mutual',  '위치공유 충돌회피 (mutual obstacles)', True),
    ('zones',   '존 교통관제 (zone traffic control)', True),
    ('rotate',  '리커버리 360° 회전 사용', False),
]

# 로봇 계열 → 네임스페이스/표시명
CLASS_ROBOTS = {'loco': ('locobot_0', 'locobot_1'),
                'tb3': ('tb3_burger_0', 'tb3_burger_1'),
                'waffle': ('tb3_waffle_0',)}
CLASS_TITLES = {'loco': 'LoCoBot (locobot_0/1)',
                'tb3': 'TurtleBot3 burger (tb3_burger_0/1)',
                'waffle': 'TurtleBot3 waffle (tb3_waffle_0)'}

# 태스크별 실제 사용 로봇 + locobot 지역 플래너 ns (수치 파라미터의 목적지 —
# launch 게이트 실측 2026-08-10: MOVE/릴레이만 TrajectoryPlanner, 나머지 DWA)
TASK_NAV = {
    'RELAY':           {'label': '릴레이',     'classes': ('loco', 'tb3'),
                        'loco_ns': 'TrajectoryPlannerROS'},
    'MOVE':            {'label': '다목적 이동', 'classes': ('loco', 'tb3'),
                        'loco_ns': 'TrajectoryPlannerROS'},
    'AVOIDANCE':       {'label': '충돌회피',   'classes': ('loco', 'tb3'),
                        'loco_ns': 'DWAPlannerROS'},
    'SEARCH_MAKE_MAP': {'label': '지도제작',   'classes': ('loco', 'waffle'),
                        'loco_ns': 'DWAPlannerROS'},
    'SEARCH_FIND':     {'label': '물건찾기',   'classes': ('loco', 'waffle'),
                        'loco_ns': 'DWAPlannerROS'},
}


def task_nav_key(task):
    """협업 태스크 enum → TASK_NAV 키. 미지원 태스크(릴레이 등)는 None(공통)."""
    nm = getattr(task, 'name', None)
    return nm if nm in TASK_NAV else None


def nav_setting_value(settings, cls, key, task=None):
    """저장값 반환 — 태스크 전용 → 공통 → 기본값 순 폴백.
    cls: 'loco'|'tb3'|'waffle', key: NAV_FIELDS 의 키."""
    for k, _label, defaults, *_ in NAV_FIELDS:
        if k == key:
            cand = []
            if task:
                cand.append('nav/%s/%s_%s' % (task, cls, key))
            cand.append('nav/%s_%s' % (cls, key))
            for sk in cand:
                v = settings.value(sk)
                if v is None:
                    continue
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
            return defaults[cls]
    return None


def nav_check_value(settings, key, task=None):
    for k, _label, default in NAV_CHECKS:
        if k == key:
            cand = []
            if task:
                cand.append('nav/%s/%s' % (task, key))
            cand.append('nav/%s' % key)
            for sk in cand:
                v = settings.value(sk)
                if v is not None:
                    return str(v).lower() in ('true', '1', 'yes')
            return default
    return None


class DialogNavSettings(QtWidgets.QDialog):
    sigLiveDone = QtCore.Signal(str)     # 라이브 적용 결과 (작업 스레드 → UI 스레드)

    def __init__(self, parent=None, task_key=None):
        super(DialogNavSettings, self).__init__(parent)
        self.m_settings = QtCore.QSettings(SETTING_COMPANY, SETTING_APP)
        _migrate_old_nav(self.m_settings)
        info = TASK_NAV.get(task_key) if task_key else None
        self.m_task = task_key if info else None
        self.m_classes = info['classes'] if info else ('loco', 'tb3')
        self.m_loco_ns = info['loco_ns'] if info else 'TrajectoryPlannerROS'
        if self.m_task:
            self.setWindowTitle('Nav 설정 — %s 전용 (Nav Settings per Task)'
                                % info['label'])
        else:
            self.setWindowTitle('Nav 설정 (Nav Settings) - 매 시뮬레이션 Start 시 반영')
        font = QtGui.QFont()
        font.setPointSize(11)
        self.setFont(font)
        lay = QtWidgets.QVBoxLayout(self)
        if self.m_task:
            note = QtWidgets.QLabel(
                '이 태스크(%s)에만 적용되는 설정입니다. 저장한 항목만 태스크 전용으로\n'
                '기록되고, 그 외에는 공통 Nav 설정 → 기본값 순으로 적용됩니다.'
                % info['label'])
        else:
            note = QtWidgets.QLabel(
                '기본값과 다르게 바꾼 항목만 다음 Start 부터 적용됩니다.\n'
                '(실행 중인 시뮬레이션에는 영향 없음 — 재시작 단위 적용)')
        note.setStyleSheet('color:#555;')
        lay.addWidget(note)

        self.m_spins = {}      # (cls, key) → spinbox
        row_lay = QtWidgets.QHBoxLayout()
        for cls in self.m_classes:
            gb = QtWidgets.QGroupBox(CLASS_TITLES[cls])
            grid = QtWidgets.QGridLayout(gb)
            for i, (key, label, defaults, mn, mx, dec) in enumerate(NAV_FIELDS):
                grid.addWidget(QtWidgets.QLabel(label), i, 0)
                sp = QtWidgets.QDoubleSpinBox()
                sp.setRange(mn, mx)
                sp.setDecimals(dec)
                sp.setSingleStep(0.05)
                sp.setValue(nav_setting_value(self.m_settings, cls, key,
                                              self.m_task))
                grid.addWidget(sp, i, 1)
                dflt = QtWidgets.QLabel('기본 %.2f' % defaults[cls])
                dflt.setStyleSheet('color:#888;')
                grid.addWidget(dflt, i, 2)
                self.m_spins[(cls, key)] = sp
            row_lay.addWidget(gb)
        lay.addLayout(row_lay)

        # 태스크 스코프에선 그 태스크가 쓰는 로봇의 콤보만, 공통 스코프는 전부
        self.m_planners = {}
        pl = QtWidgets.QHBoxLayout()
        for key, label, opts in NAV_PLANNERS:
            if self.m_task:
                if key.startswith('loco_') and 'loco' not in self.m_classes:
                    continue
                if key == 'tb3_global' and 'tb3' not in self.m_classes:
                    continue
                if key == 'waffle_slam' and 'waffle' not in self.m_classes:
                    continue
            pl.addWidget(QtWidgets.QLabel(label + ':'))
            cb2 = QtWidgets.QComboBox()
            cb2.addItems(opts)
            cb2.setToolTip('플래너는 move_base 기동 시에만 적용 —\n'
                           '저장 후 다음 Start(재시작)부터 반영됩니다')
            saved = None
            if self.m_task:
                saved = self.m_settings.value(
                    'nav/%s/planner_%s' % (self.m_task, key))
            if saved is None:
                saved = self.m_settings.value('nav/planner_%s' % key)
            if saved is not None and str(saved) in opts:
                cb2.setCurrentText(str(saved))
            pl.addWidget(cb2)
            self.m_planners[key] = cb2
        pl.addStretch(1)
        lay.addLayout(pl)

        self.m_checks = {}
        for key, label, _default in NAV_CHECKS:
            cb = QtWidgets.QCheckBox(label)
            cb.setChecked(nav_check_value(self.m_settings, key, self.m_task))
            lay.addWidget(cb)
            self.m_checks[key] = cb

        btns = QtWidgets.QHBoxLayout()
        if self.m_task:
            btnReset = QtWidgets.QPushButton('공통 설정으로 복원 (Use Global)')
            btnReset.setToolTip('이 태스크 전용 저장값을 지우고\n'
                                '공통 Nav 설정(→기본값)을 따르게 합니다')
        else:
            btnReset = QtWidgets.QPushButton('기본값 복원 (Restore Defaults)')
        self.btnLive = QtWidgets.QPushButton('지금 적용 (Apply Live)')
        self.btnLive.setToolTip('떠 있는 시뮬레이션의 move_base 에 즉시 반영\n'
                                '(속도·허용오차·inflation — 리커버리/위치공유는 재시작 필요)')
        btnOk = QtWidgets.QPushButton('저장 (Save)')
        btnCancel = QtWidgets.QPushButton('취소 (Cancel)')
        btns.addWidget(btnReset)
        btns.addStretch(1)
        btns.addWidget(self.btnLive)
        btns.addWidget(btnOk)
        btns.addWidget(btnCancel)
        lay.addLayout(btns)
        btnReset.clicked.connect(self.OnReset)
        self.btnLive.clicked.connect(self.OnLiveApply)
        btnOk.clicked.connect(self.OnSave)
        btnCancel.clicked.connect(self.reject)
        self.sigLiveDone.connect(self._OnLiveDone)

    def _sk(self, tail):
        """이 스코프의 QSettings 키."""
        return ('nav/%s/%s' % (self.m_task, tail)) if self.m_task \
            else ('nav/%s' % tail)

    def OnReset(self):
        if self.m_task:
            # 태스크 전용 키 전부 제거 → 공통 설정(→기본값) 폴백으로 복귀
            self.m_settings.beginGroup('nav/%s' % self.m_task)
            self.m_settings.remove('')
            self.m_settings.endGroup()
            for (cls, key), sp in self.m_spins.items():
                sp.setValue(nav_setting_value(self.m_settings, cls, key))
            for key, cb in self.m_checks.items():
                cb.setChecked(nav_check_value(self.m_settings, key))
            for key, cb2 in self.m_planners.items():
                saved = self.m_settings.value('nav/planner_%s' % key)
                if saved is not None and cb2.findText(str(saved)) >= 0:
                    cb2.setCurrentText(str(saved))
                else:
                    cb2.setCurrentIndex(0)
            return
        for key, _label, defaults, *_ in NAV_FIELDS:
            for cls in self.m_classes:
                self.m_spins[(cls, key)].setValue(defaults[cls])
        for key, _label, default in NAV_CHECKS:
            self.m_checks[key].setChecked(default)
        for key in self.m_planners:
            self.m_planners[key].setCurrentIndex(0)

    def _SaveValues(self):
        for (cls, key), sp in self.m_spins.items():
            self.m_settings.setValue(self._sk('%s_%s' % (cls, key)), sp.value())
        for key, cb in self.m_checks.items():
            self.m_settings.setValue(self._sk(key), cb.isChecked())
        for key, cb2 in self.m_planners.items():
            self.m_settings.setValue(self._sk('planner_%s' % key),
                                     cb2.currentText())
        self.m_settings.sync()

    def OnSave(self):
        self._SaveValues()
        self.accept()

    def OnLiveApply(self):
        """떠 있는 move_base 에 dynamic_reconfigure 로 즉시 반영.
        (라이브 가능: 속도·허용오차·inflation / 재시작 필요: 리커버리·위치공유)"""
        self._SaveValues()                  # 다음 Start 와도 일치하도록 함께 저장
        vals = {(cls, key): sp.value() for (cls, key), sp in self.m_spins.items()}
        self.btnLive.setEnabled(False)
        self.btnLive.setText('적용 중... (Applying)')
        threading.Thread(target=self._LiveWorker, args=(vals,), daemon=True).start()

    def _LiveWorker(self, vals):
        plan_ns = {'loco': self.m_loco_ns, 'tb3': 'DWAPlannerROS',
                   'waffle': 'DWAPlannerROS'}
        cmds = []
        for cls in self.m_classes:
            pl = ("{'max_vel_x': %.3f, 'xy_goal_tolerance': %.3f, "
                  "'yaw_goal_tolerance': %.3f}"
                  % (vals[(cls, 'max_vel')], vals[(cls, 'xy_tol')],
                     vals[(cls, 'yaw_tol')]))
            infl = "{'inflation_radius': %.3f}" % vals[(cls, 'inflation')]
            for ns in CLASS_ROBOTS[cls]:
                cmds.append(('%s 플래너' % ns,
                             "dynparam set /%s/move_base/%s \"%s\"" % (ns, plan_ns[cls], pl)))
                for cm in ('local_costmap', 'global_costmap'):
                    cmds.append(('%s %s inflation' % (ns, cm),
                                 "dynparam set /%s/move_base/%s/inflation_layer \"%s\"" % (ns, cm, infl)))
        fails = []
        for label, c in cmds:
            r = subprocess.run(
                ['bash', '-c',
                 'source /opt/ros/noetic/setup.bash; timeout 12 rosrun dynamic_reconfigure ' + c],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode != 0:
                fails.append(label)
        if fails:
            msg = ('일부 항목 적용 실패 (%d/%d 성공):\n- ' % (len(cmds) - len(fails), len(cmds))
                   + '\n- '.join(fails[:6])
                   + '\n\n시뮬레이션(마스터)이 떠 있는지 확인하세요.')
        else:
            msg = ('라이브 적용 완료 (%d개 항목).\n\n'
                   '리커버리 회전/위치공유 변경은 다음 Start 부터 반영됩니다.' % len(cmds))
        self.sigLiveDone.emit(msg)

    def _OnLiveDone(self, msg):
        self.btnLive.setEnabled(True)
        self.btnLive.setText('지금 적용 (Apply Live)')
        QtWidgets.QMessageBox.information(self, 'Nav 설정', msg)


def generate_nav_overrides(settings, path, task_key=None):
    """QSettings 값으로 nav_overrides.launch 생성 — 기본값과 다른 항목만 param 으로.
    nav launch 문서 맨 끝에서 include 되므로 기존/게이트 값 위에 이긴다.
    task_key 가 TASK_NAV 에 있으면 그 태스크의 로봇 구성·전용 저장값을 쓴다."""
    _migrate_old_nav(settings)
    info = TASK_NAV.get(task_key) if task_key else None
    task = task_key if info else None
    classes = info['classes'] if info else ('loco', 'tb3')
    plan_ns = {'loco': (info['loco_ns'] if info else 'TrajectoryPlannerROS'),
               'tb3': 'DWAPlannerROS', 'waffle': 'DWAPlannerROS'}
    lines = ['<launch>',
             '  <!-- 자동 생성: Nav 설정 다이얼로그 (Start 시마다 재생성, 스코프=%s)'
             ' — 수동 편집 금지 -->' % (task or '공통')]
    par_key = {'max_vel': 'max_vel_x', 'xy_tol': 'xy_goal_tolerance',
               'yaw_tol': 'yaw_goal_tolerance'}
    for key, _label, defaults, *_ in NAV_FIELDS:
        for cls in classes:
            v = nav_setting_value(settings, cls, key, task)
            if abs(v - defaults[cls]) < 1e-6:
                continue                      # 기본값 그대로 — 내보내지 않음
            for ns in CLASS_ROBOTS[cls]:
                if key == 'inflation':
                    for cm in ('local_costmap', 'global_costmap'):
                        lines.append(
                            '  <param name="/%s/move_base/%s/inflation_layer/'
                            'inflation_radius" value="%.3f"/>' % (ns, cm, v))
                else:
                    lines.append(
                        '  <param name="/%s/move_base/%s/%s" value="%.3f"/>'
                        % (ns, plan_ns[cls], par_key[key], v))
    # ── 플래너 선택 (자동(기본) 이 아니면 출력 — 문서 맨끝 include 라 게이트도 이김) ──
    def _pl(key):
        if task:
            v = settings.value('nav/%s/planner_%s' % (task, key))
            if v is not None:
                return str(v)
        v = settings.value('nav/planner_%s' % key)
        return str(v) if v is not None else '자동 (기본)'
    if 'loco' in classes:
        _lg = _pl('loco_global')
        if _lg != '자동 (기본)':
            gp = ('global_planner/GlobalPlanner' if _lg == 'GlobalPlanner'
                  else 'navfn/NavfnROS')
            for ns in CLASS_ROBOTS['loco']:
                lines.append(f'  <param name="/{ns}/move_base/base_global_planner" value="{gp}"/>')
                if _lg == 'GlobalPlanner':
                    lines.append(f'  <param name="/{ns}/move_base/GlobalPlanner/allow_unknown" value="true"/>')
        _ll = _pl('loco_local')
        if _ll != '자동 (기본)':
            if _ll == 'DWA':
                for ns in CLASS_ROBOTS['loco']:
                    lines.append(f'  <param name="/{ns}/move_base/base_local_planner" value="dwa_local_planner/DWAPlannerROS"/>')
                    for k2, v2 in (('max_vel_x', 0.5), ('min_vel_x', 0.0),
                                   ('max_vel_trans', 0.5), ('min_vel_trans', 0.08),
                                   ('max_vel_theta', 1.5), ('min_vel_theta', 0.4),
                                   ('acc_lim_x', 1.0), ('acc_lim_theta', 2.5),
                                   ('sim_time', 1.7), ('vx_samples', 10),
                                   ('vth_samples', 20), ('path_distance_bias', 40.0),
                                   ('goal_distance_bias', 20.0), ('occdist_scale', 0.02),
                                   ('forward_point_distance', 0.325),
                                   ('xy_goal_tolerance', 0.35),
                                   ('yaw_goal_tolerance', 6.28)):
                        lines.append(f'  <param name="/{ns}/move_base/DWAPlannerROS/{k2}" value="{v2}"/>')
                    lines.append(f'  <param name="/{ns}/move_base/DWAPlannerROS/latch_xy_goal_tolerance" value="true"/>')
            else:
                for ns in CLASS_ROBOTS['loco']:
                    lines.append(f'  <param name="/{ns}/move_base/base_local_planner" value="base_local_planner/TrajectoryPlannerROS"/>')
    if 'tb3' in classes:
        _tg = _pl('tb3_global')
        if _tg != '자동 (기본)':
            gp = ('global_planner/GlobalPlanner' if _tg == 'GlobalPlanner'
                  else 'navfn/NavfnROS')
            for ns in CLASS_ROBOTS['tb3']:
                lines.append(f'  <param name="/{ns}/move_base/base_global_planner" value="{gp}"/>')
                if _tg == 'GlobalPlanner':
                    lines.append(f'  <param name="/{ns}/move_base/GlobalPlanner/allow_unknown" value="true"/>')
    if nav_check_value(settings, 'rotate', task):
        # 회전 리커버리 복원 (게이트 블록의 청소-전용 목록을 덮음)
        layers = {'loco': '[laser_layer, depth_layer]',
                  'tb3': '[obstacle_layer]', 'waffle': '[obstacle_layer]'}
        for cls in classes:
            for ns in CLASS_ROBOTS[cls]:
                lines.append('  <rosparam param="/%s/move_base/recovery_behaviors">'
                             '[{name: conservative_reset, type: clear_costmap_recovery/'
                             'ClearCostmapRecovery}, {name: rotate_recovery, type: '
                             'rotate_recovery/RotateRecovery}, {name: aggressive_reset, '
                             'type: clear_costmap_recovery/ClearCostmapRecovery}]'
                             '</rosparam>' % ns)
                lines.append('  <rosparam param="/%s/move_base/conservative_reset/'
                             'layer_names">%s</rosparam>' % (ns, layers[cls]))
                lines.append('  <rosparam param="/%s/move_base/aggressive_reset/'
                             'layer_names">%s</rosparam>' % (ns, layers[cls]))
    lines.append('</launch>')
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return path
