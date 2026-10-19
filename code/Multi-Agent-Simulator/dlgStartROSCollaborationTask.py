######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : 협업태스크 작업자 다이얼로그                ##
######################################################
import os
from PySide6 import QtWidgets
from PySide6.QtGui import QTextCursor
from widgetStartROSCollaborationTasktItem import WidgetStartROSCollaborationTaskItem
from dlgStartROSCollaborationTask_ui import Ui_DlgROSCollaborationTask
from taskRelay import TaskRelay

# 충돌회피(Avoidance) 시나리오 상수 — main.py 의 AVOID_POSITIONS 와 동기 유지
# R1=locobot_0: A(-3.0,1.4)→B(3.1,-1.6), R2=locobot_1: B→A, R3=tb3_burger_0: C(-2.9,-3.3)→D(2.9,2.3)
AVOID_BT = (0.28, -0.12, 1.35)         # 병목 중심/반경 (world 모델 오프셋 반영)
# 최종 goal 은 목적 구역 '중심 깊숙이' (2026-08-09 붉은 원 지시 — 문 앞 아님)
AVOID_ROUTES = {'locobot_0': ((-2.80, 1.04), (2.60, -3.00)),
                'locobot_1': ((3.30, -1.96), (-3.30, -0.30)),
                'tb3_burger_0': ((-2.70, -3.66), (2.20, 1.70))}
import subprocess
import copy
import time
import threading
import json
import sys
from PySide6.QtCore import QThread, Signal, QSettings

from constant import *
from simulator import *

class DialogStartROSCollaborationTask(
    QtWidgets.QDialog):

    # 릴레이 완료(백그라운드 스레드) → UI 스레드에서 버튼 복구용 시그널
    sigTaskDone = Signal()

    # Init
    def __init__(self, rosInfo, jnp081Active=False, jnp021Active=False, monitorOpener=None,
                 basePositions=None):
        super().__init__()
        self.ui = Ui_DlgROSCollaborationTask()
        self.ui.setupUi(self)
        self.sigTaskDone.connect(self.enableUI)

        self.m_simulator = copy.deepcopy(rosInfo)
        self.m_jnp081Active = jnp081Active      # JnP 0.8.1 에이전트 상주 여부 (자동 기동 판단)
        self.m_jnp021Active = jnp021Active      # 0.2.1 은 협업 태스크 미지원 — 안내만
        # BASE 슬롯 상수(이름→(x,y)) — 원 중심과 legacy 홈 좌표를 여기 고정
        self.m_basePos = basePositions
        self.m_baseXY = None
        if basePositions:
            xs = [v[0] for v in basePositions.values()]
            ys = [v[1] for v in basePositions.values()]
            self.m_baseXY = (sum(xs) / len(xs), sum(ys) / len(ys))
        self.m_monitorOpener = monitorOpener    # JnP 실행 시 Monitor 창 자동 표시용

        # 실행 방식 콤보 (0=JnP 0.8.1, 1=기존 launch) — 설정에 저장/복원, 한/영 라벨
        settings = QSettings(SETTING_COMPANY, SETTING_APP)
        self.m_ko = (settings.value('ui_lang') is None or int(settings.value('ui_lang') or 0) == 0)
        saved = settings.value('exec_mode')
        if saved is not None:
            self.ui.cmbExecMode.setCurrentIndex(int(saved))
        self.ui.cmbExecMode.currentIndexChanged.connect(
            lambda i: QSettings(SETTING_COMPANY, SETTING_APP).setValue('exec_mode', i))
        if not self.m_ko:
            self.ui.lbExecMode.setText('Execution :')
            self.ui.cmbExecMode.setItemText(1, 'Legacy launch')
        self.PATH_LOCO_INIT_SH = "/root/tesla/ros/navi/sh/loco_init_all.sh"

        # 태스크별 Nav 설정 버튼 (2026-08-10 지시) — 이 태스크가 실제 사용하는
        # 로봇 계열만 노출하는 전용 설정 창. 저장한 항목만 태스크 전용으로
        # 기록되고, 그 외에는 공통 Nav 설정 → 기본값 순으로 폴백.
        from dlgNavSettings import DialogNavSettings, task_nav_key
        _navk = task_nav_key(getattr(self.m_simulator, 'ros_collaboration', None))
        if _navk:
            self.btnNavSettings = QtWidgets.QPushButton(
                'Nav 설정...' if self.m_ko else 'Nav Settings...')
            self.btnNavSettings.setToolTip(
                ('이 태스크 전용 항법 설정 — 저장한 항목만 이 태스크에 적용,\n'
                 '저장하지 않은 항목은 공통 Nav 설정 → 기본값을 따릅니다')
                if self.m_ko else
                'Per-task nav settings; unsaved items fall back to the global settings')
            # Execution 라벨 바로 앞(우측 컨트롤 묶음의 맨 앞)에 배치 —
            # index 0 은 확장 스페이서 앞이라 창 좌측 끝에 홀로 떨어진다
            _ix = self.ui.horizontalLayout_2.indexOf(self.ui.lbExecMode)
            self.ui.horizontalLayout_2.insertWidget(max(0, _ix), self.btnNavSettings)
            self.btnNavSettings.clicked.connect(
                lambda _=False, k=_navk: DialogNavSettings(self, task_key=k).exec())

        # ── 다목적 이동 전용: Goals 편집 패널 (goal 수/위치/물품 수) ──
        # 릴레이 스킨(로봇별 Move-To)과 달리, goal 자체를 편집한다 (2026-08-08)
        self.m_goalRows = []
        if (getattr(self.m_simulator, 'ros_collaboration', None)
                == ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE):
            self._build_goals_panel()

        # UI 생성
        self.SetRobotsInfoToList(self.m_simulator.robots)

        # 이벤트 연결
        self.ui.btnROSCollaborationTaskStart.clicked.connect(self.StartColloaborationTask)

    # ── 다목적 이동 Goals 패널 ──
    def _build_goals_panel(self):
        gb = QtWidgets.QGroupBox(
            'Goals — 위치와 물품 수 (로봇들은 베이스에서 각 goal 로 왕복하며 물품을 소진)'
            if self.m_ko else
            'Goals — position & item count (robots shuttle from base, consuming items)')
        v = QtWidgets.QVBoxLayout(gb)
        head = QtWidgets.QHBoxLayout()
        self.m_chkTotalTime = QtWidgets.QCheckBox(
            '전체 시간 고려 배분' if self.m_ko else 'Optimize total time')
        self.m_chkTotalTime.setToolTip(
            '끄면 각 로봇이 자기가 가장 빨리 갈 수 있는 goal 을 선택,\n'
            '켜면 물품 비율 정원으로 전체 완료 시간을 고려해 배분' if self.m_ko else
            'Off: each robot picks its fastest goal.\n'
            'On: balanced by item ratio to optimize overall completion time')
        head.addWidget(self.m_chkTotalTime)
        btnAdd = QtWidgets.QPushButton('+ Goal')
        btnDel = QtWidgets.QPushButton('- Goal')
        btnAdd.setMaximumWidth(80)
        btnDel.setMaximumWidth(80)
        btnAdd.clicked.connect(self._add_goal_row_default)
        btnDel.clicked.connect(self._del_goal_row)
        head.addStretch(1)
        head.addWidget(btnAdd)
        head.addWidget(btnDel)
        v.addLayout(head)
        self.m_goalRowsLayout = QtWidgets.QVBoxLayout()
        v.addLayout(self.m_goalRowsLayout)
        self._add_goal_row(1.0, 0.5, 3)      # G1 기본
        self._add_goal_row(1.0, -4.0, 3)     # G2 기본
        lay = self.ui.verticalLayout_3
        lay.insertWidget(lay.count() - 1, gb)
        self.m_gbGoals = gb
        if (getattr(self.m_simulator, 'ros_collaboration', None)
                in (ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                    ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP)):
            gb.hide()      # 충돌회피: 시나리오 고정 (R1 A→B, R2 B→A, R3 C→D)

    def _add_goal_row(self, x, y, cnt):
        row = QtWidgets.QHBoxLayout()
        idx = len(self.m_goalRows) + 1
        lb = QtWidgets.QLabel(f'G{idx}')
        f = lb.font(); f.setBold(True); lb.setFont(f)
        ex = QtWidgets.QLineEdit(f'{x:.1f}')
        ey = QtWidgets.QLineEdit(f'{y:.1f}')
        ex.setMaximumWidth(90)
        ey.setMaximumWidth(90)
        sp = QtWidgets.QSpinBox()
        sp.setRange(1, 9)
        sp.setValue(cnt)
        row.addWidget(lb)
        row.addWidget(QtWidgets.QLabel('X:'))
        row.addWidget(ex)
        row.addWidget(QtWidgets.QLabel('Y:'))
        row.addWidget(ey)
        row.addWidget(QtWidgets.QLabel('물품 수:' if self.m_ko else 'Items:'))
        row.addWidget(sp)
        row.addStretch(1)
        self.m_goalRowsLayout.addLayout(row)
        self.m_goalRows.append((lb, ex, ey, sp, row))

    def _add_goal_row_default(self):
        if len(self.m_goalRows) < 4:
            self._add_goal_row(0.0, 0.0, 3)

    def _del_goal_row(self):
        if len(self.m_goalRows) <= 1:
            return
        lb, ex, ey, sp, row = self.m_goalRows.pop()
        while row.count():
            it = row.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        self.m_goalRowsLayout.removeItem(row)

    # Goals 패널 값 읽기 → [('G1', x, y, count), ...] (숫자 오류 시 ValueError)
    def _read_goals(self):
        out = []
        for k, (_lb, ex, ey, sp, _row) in enumerate(self.m_goalRows, 1):
            out.append((f'G{k}', float(ex.text()), float(ey.text()), int(sp.value())))
        return out

    # 로봇 정보를 이용해 리스트뷰에 로봇 정보 입력
    def SetRobotsInfoToList(self, robots):
        for i in range(len(robots)):
            lstRobot = self.ui.lstwROSCollaborationTaskRobots
            item = QtWidgets.QListWidgetItem(lstRobot)
            # 로봇 위젯 생성
            custom_widget = WidgetStartROSCollaborationTaskItem()
            item.setSizeHint(custom_widget.sizeHint())

            custom_widget.SetupListItem(robots[i].type, robots[i].name)
            custom_widget.SetRobotPosXYZ(str(robots[i].startX), str(robots[i].startY), str(robots[i].startZ))

            # 태스크별 Move-To 기본값
            #  - Relay: 마지막 로봇 것만 최종 목표로 사용 (앞 로봇 goal 은 자동 계산)
            #  - 다목적 이동: 로봇1/2 의 Move-To = G1/G2 지점 (베이스에서 왕복할 목적지)
            if (getattr(self.m_simulator, 'ros_collaboration', None)
                    in (ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE,
                        ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE,
                        ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP)):
                # 다목적/충돌회피/지도제작: Move to 박스 불필요 — 숨긴다
                custom_widget.SetRobotMoveToXYZ("0.0", "0.0", "0.0")
                try:
                    custom_widget.ui.gbWidgetStartROSCollaborationTaskItemMoveTo.hide()
                except Exception:
                    pass
            elif i == 0:
                custom_widget.SetRobotMoveToXYZ("1.0", "1.0", "0.0")
            elif i == 1:
                custom_widget.SetRobotMoveToXYZ("1.0", "-1.0", "0.0")
            elif i == 2:
                custom_widget.SetRobotMoveToXYZ("0.0", "0.0", "0.0")
            elif i == 3:
                custom_widget.SetRobotMoveToXYZ("1.0", "-6.0", "0.0")

            # 리스트뷰에 로봇 위젯 셋
            lstRobot.addItem(item)
            lstRobot.setItemWidget(item, custom_widget)

    # 협업 태스크 시작
    def StartColloaborationTask(self):
        # ★ ROS 마스터(=Gazebo) 확인 — 없이 진행하면 콘솔에 'Unable to communicate
        #   with master!'만 반복되고 이동 명령이 무한 대기한다 (2026-08-08 실측).
        #   먼저 환경/로봇을 띄우라는 팝업을 주고 아무것도 실행하지 않는다.
        try:
            import rosgraph
            master_ok = rosgraph.is_master_online()
        except Exception:
            master_ok = True        # 확인 불가 환경에서는 기존 동작 유지
        if not master_ok:
            lang = QSettings(SETTING_COMPANY, SETTING_APP).value('ui_lang')
            ko = (lang is None or int(lang) == 0)
            QtWidgets.QMessageBox.warning(
                self,
                '시뮬레이션 없음' if ko else 'Simulation not running',
                ('시뮬레이션이 실행 중이 아닙니다.\n'
                 '먼저 메인 화면의 Start 버튼으로 환경/로봇(Gazebo)을 띄운 후\n'
                 '협업 태스크를 시작하세요.') if ko else
                ('The simulation is not running.\n'
                 'Start the environment/robots (Gazebo) with the main Start button first,\n'
                 'then run the collaboration task.'))
            return
        # ★ JnP 모드 선택 + 0.2.1 에이전트 상태 — 협업 태스크 연동 미지원 안내 (실행 안 함)
        if self.ui.cmbExecMode.currentIndex() == 0 and self.m_jnp021Active:
            lang = QSettings(SETTING_COMPANY, SETTING_APP).value('ui_lang')
            ko = (lang is None or int(lang) == 0)
            QtWidgets.QMessageBox.information(
                self,
                'JnP 0.2.1' ,
                ('JnP 0.2.1은 협업 태스크 연동을 지원하지 않습니다.\n'
                 '(0.2.1은 discovery/description 데모 전용)\n'
                 'JnP 콤보를 0.8.1로 바꾸고 JnP Start 후 다시 시도하세요.') if ko else
                ('JnP 0.2.1 does not support collaboration task integration.\n'
                 '(0.2.1 is a discovery/description demo only)\n'
                 'Switch the JnP combo to 0.8.1, press JnP Start, and try again.'))
            return

        # 선택된 협업 태스크 종류 — legacy launch / JnP 두 방식 모두 지원 (2026-08-08 지시)
        is_move = (getattr(self.m_simulator, 'ros_collaboration', None)
                   == ENUM_ROS_COLLABORATION_TASK_TYPE.MOVE)
        is_avoid = (getattr(self.m_simulator, 'ros_collaboration', None)
                    == ENUM_ROS_COLLABORATION_TASK_TYPE.AVOIDANCE)
        is_map = (getattr(self.m_simulator, 'ros_collaboration', None)
                  == ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_MAKE_MAP)
        is_find = (getattr(self.m_simulator, 'ros_collaboration', None)
                   == ENUM_ROS_COLLABORATION_TASK_TYPE.SEARCH_FIND)

        self.disableUI()

        # ---- JnP 0.8.1 경로: task(goal) 발행 → 에이전트 coalition 이 트리/할당/스케줄로
        #      move_base 실주행까지 수행 (2026-08-08 실주행 연결 완료) ----
        if self.ui.cmbExecMode.currentIndex() == 0:
            # JnP 모드: task tree/coalition 관찰용 Monitor 창을 자동으로 연다
            if self.m_monitorOpener:
                try:
                    self.m_monitorOpener()
                except Exception as e:
                    print(f"Monitor 창 표시 실패: {e}")
            # 연쇄 릴레이 payload (stock relay 와 동일 의미, 2026-08-08):
            # i번째 로봇 goal = (i+1)번째 로봇 위치 0.9m 앞(접근 방향), 마지막 = 최종 목표.
            # 다리별 goal 은 build_relay_tree 가 트리로 만들고 AffinityAllocator 가
            # 이름 매칭으로 해당 로봇에 전담 배정한다.
            import math
            try:
                infos = []          # (name, startX, startY, moveToX, moveToY)
                for i in range(len(self.m_simulator.robots)):
                    rb = self.m_simulator.robots[i]
                    mtx, mty = 0.0, 0.0
                    if i < self.ui.lstwROSCollaborationTaskRobots.count():
                        list_item = self.ui.lstwROSCollaborationTaskRobots.item(i)
                        w = self.ui.lstwROSCollaborationTaskRobots.itemWidget(list_item)
                        mtx = float(w.GetRobotMoveToX())
                        mty = float(w.GetRobotMoveToY())
                    infos.append((rb.name, float(rb.startX), float(rb.startY), mtx, mty))
            except (ValueError, TypeError) as e:
                print(f"좌표가 숫자가 아닙니다 — task 발행 취소: {e}")
                self.enableUI()
                return
            if not infos:
                print("로봇 목록이 비어 있어 task를 발행하지 않습니다.")
                self.enableUI()
                return
            segments = []
            n = len(infos)
            if is_find:
                # 분산탐색-물건찾기 (2026-08-10): 알려진 지도 사전 분할 순회 +
                # YOLO v8 탐지 — 대상 클래스 전부 발견 시 조기 종료
                data = ("task:ObjectSearch:robots=locobot_0|locobot_1|tb3_waffle_0"
                        ";targets=sports_ball,orange;count=2")
            elif is_map:
                # 분산 탐색(지도 제작): coalition 이 RRT 탐사 스택을 기동·감독
                data = "task:MapExplore:robots=locobot_0|locobot_1|tb3_waffle_0"
            elif is_avoid:
                # 충돌회피: 고정 시나리오(R1 A→B, R2 B→A, R3 C→D) — 병목 통과
                # 순서는 그룹이 ETA 로 결정. robots= 명단으로 참여 로봇 한정.
                routes_s = "|".join(
                    f"{nm}:{a[0]:.2f},{a[1]:.2f}>{b[0]:.2f},{b[1]:.2f}"
                    for nm, (a, b) in AVOID_ROUTES.items())
                # mode=dynamic (2026-08-09): 그룹 선형성 없이 전원 병렬 출발 —
                # 충돌 '예측' 시점에 해당 로봇들끼리 동적 coalition 형성/해산
                data = (f"task:Avoidance:bt={AVOID_BT[0]:.2f},{AVOID_BT[1]:.2f},{AVOID_BT[2]:.2f}"
                        f";routes={routes_s};mode=dynamic"
                        f";robots=" + "|".join(AVOID_ROUTES))
            elif is_move:
                # 다목적 이동: Goals 패널(goal 수/위치/물품 수)에서 goal 목록을 읽는다.
                # 로봇들은 특성(시작위치-goal 거리)으로 할당되어 왕복하며 물품을 소진하고,
                # 한 goal 이 소진되면 남은 goal 로 자동 재할당된다.
                try:
                    goal_list = self._read_goals()
                except (ValueError, TypeError) as e:
                    print(f"Goal 좌표가 숫자가 아닙니다 — task 발행 취소: {e}")
                    self.enableUI()
                    return
                goals_s = "|".join(f"{gn}:{gx:.2f},{gy:.2f}:{gc}"
                                   for gn, gx, gy, gc in goal_list)
                optMode = 'total' if self.m_chkTotalTime.isChecked() else 'fast'
                # robots 명단은 넣지 않는다 — 에이전트들이 ETA 입찰로 스스로 goal 을
                # 선택하고 goal별 그룹을 만든다 (opt=fast/total 은 배분 기준 옵션)
                data = f"task:Mult-Goal:goals={goals_s};opt={optMode}"
                # BASE(출발영역) 표시 발행 — 슬롯 상수 중심(우선) 또는 시작위치 무게중심
                if infos:
                    if self.m_baseXY is not None:
                        bx, by = self.m_baseXY
                    else:
                        bx = sum(cx for _n, cx, _cy, _mx, _my in infos) / len(infos)
                        by = sum(cy for _n, _cx, cy, _mx, _my in infos) / len(infos)
                    baseCmd = (PATH_SOURCE_JNP081_SETUP + "; rostopic pub -1 /task_base "
                               "geometry_msgs/PoseStamped "
                               f"'{{header: {{frame_id: map}}, pose: {{position: {{x: {bx:.2f}, y: {by:.2f}}}, orientation: {{w: 1.0}}}}}}'")
                    subprocess.Popen(['bash', '-c', baseCmd])
            else:
                for i in range(n):
                    name, cx, cy, mtx, mty = infos[i]
                    if i < n - 1:
                        nx, ny = infos[i + 1][1], infos[i + 1][2]
                        dx, dy = nx - cx, ny - cy
                        d = math.hypot(dx, dy) or 1.0
                        gx = nx - 0.9 * dx / d
                        gy = ny - 0.9 * dy / d
                        th = math.atan2(dy, dx)
                    else:
                        gx, gy, th = mtx, mty, 0.0      # 마지막 로봇 = 최종 목표
                    segments.append(f"{name}={gx:.2f},{gy:.2f},{th:.2f}")
                data = "task:Relay:" + ";".join(segments)
            pubCmd = (PATH_SOURCE_JNP081_SETUP + "; rostopic pub -1 "
                      + CMD_ROS_JNP081_TASK_TOPIC + " std_msgs/String \"data: '" + data + "'\"")

            def _agents_running():
                out = subprocess.run(['pgrep', '-f', 'jnp_0.8.1/scripts/jnp_[a]gent'],
                                     stdout=subprocess.PIPE).stdout.decode().split()
                return out

            robot_names = [rb.name for rb in self.m_simulator.robots]

            def _run_jnp():
                try:
                    # 에이전트가 없으면 자동 기동 (메인 창 JnP Start 를 누른 것과 동일)
                    if not _agents_running():
                        print("JnP 0.8.1 에이전트 자동 기동...")
                        for name in robot_names:
                            cmd = (PATH_SOURCE_JNP081_SETUP + CMD_COMMON_SEMICOLON + CMD_COMMON_SPACE
                                   + CMD_ROS_COMMON_ROSRUN + CMD_COMMON_SPACE + CMD_ROS_JNP
                                   + CMD_COMMON_SPACE + CMD_ROS_JNP_JNP_AGENT + CMD_COMMON_SPACE
                                   + CMD_ROS_JNP_JNP_AGENT_NS + CMD_ROS_JNP_JNP_AGENT_NS_DEFAULT
                                   + CMD_COMMON_SPACE + CMD_ROS_JNP_JNP_AGENT_NAME + name
                                   + CMD_COMMON_SPACE + CMD_ROS_JNP081_AGENT_XML_ARG)
                            subprocess.Popen([CMD_EXCUTE_CMD_OPEN + cmd + CMD_EXCUTE_CMD_CLOSE], shell=True)
                            time.sleep(1)
                        for _ in range(30):     # 기동 대기
                            if len(_agents_running()) >= len(robot_names):
                                break
                            time.sleep(1)
                        time.sleep(8)           # 상호 발견(advertise/description) 여유
                    print(f"JnP 0.8.1 task 발행: {data}")
                    subprocess.Popen(['bash', '-c', pubCmd])
                    print("coalition 진행은 Monitor 창/에이전트 터미널에서 확인하세요.\n")
                finally:
                    self.sigTaskDone.emit()

            threading.Thread(target=_run_jnp, daemon=True).start()
            return

        # ★ Legacy launch + 다목적 이동: 동작 품질 미달로 비활성 (2026-08-08 지시)
        #   — 팝업 안내만 하고 실행하지 않음. Relay legacy 는 계속 지원.
        if is_move or is_avoid or is_map or is_find:
            lang = QSettings(SETTING_COMPANY, SETTING_APP).value('ui_lang')
            ko = (lang is None or int(lang) == 0)
            QtWidgets.QMessageBox.information(
                self,
                'Legacy launch',
                ('다목적 이동(Mult-Goal Move)의 Legacy launch 방식은\n'
                 '아직 구현이 완료되지 않았습니다.\n'
                 'Execution 을 "JnP 0.8.1" 로 선택해 실행해 주세요.') if ko else
                ('Legacy launch mode for Mult-Goal Move is not\n'
                 'implemented yet.\n'
                 'Please select "JnP 0.8.1" as the execution mode.'))
            self.enableUI()
            return
        # ---- 기존 경로: loco_init + 연쇄 릴레이 ----
        # ★ 백그라운드 스레드에서 실행 — UI 스레드에서 돌리면 릴레이가 끝날 때까지
        #   창 전체(메인 Stop 버튼 포함)가 얼어붙는다 (2026-08-08 실측)
        # 로봇 목록/좌표는 위젯 접근이라 스레드 시작 전에 UI 스레드에서 구성한다
        robots = []
        for i in range(len(self.m_simulator.robots)):
            rb = Robot()
            rb.id = self.m_simulator.robots[i].id
            rb.name = self.m_simulator.robots[i].name
            rb.option = self.m_simulator.robots[i].option
            rb.startX = self.m_simulator.robots[i].startX
            rb.startY = self.m_simulator.robots[i].startY
            rb.startZ = self.m_simulator.robots[i].startZ

            # i번째 위젯 가져오기
            if i < self.ui.lstwROSCollaborationTaskRobots.count():
                list_item = self.ui.lstwROSCollaborationTaskRobots.item(i)
                custom_widget = self.ui.lstwROSCollaborationTaskRobots.itemWidget(list_item)
                rb.moveToX = custom_widget.GetRobotMoveToX()
                rb.moveToY = custom_widget.GetRobotMoveToY()
                rb.moveToZ = custom_widget.GetRobotMoveToZ()

            robots.append(rb)

        # 태스크별 legacy runner 선택 (Relay / 다목적 이동 — JnP 미사용 비교 구현)
        try:
            if is_move:
                spec = {'goals': {}, 'robots': {},
                        'opt': 'total' if self.m_chkTotalTime.isChecked() else 'fast'}
                for gn, gx, gy, gc in self._read_goals():
                    spec['goals'][gn] = [gx, gy, gc]
                for rb in robots:
                    if self.m_basePos and rb.name in self.m_basePos:
                        # 홈 = 베이스 슬롯 상수 (UI 좌표 표류와 무관)
                        spec['robots'][rb.name] = list(self.m_basePos[rb.name])
                    else:
                        spec['robots'][rb.name] = [float(rb.startX), float(rb.startY)]
                if self.m_baseXY is not None:
                    spec['base'] = list(self.m_baseXY)   # 원 중심 고정 전달
                runnerFile = 'multigoal_runner.py'
                runnerArg = json.dumps(spec)
                taskLabel = '다목적 이동'
            else:
                runnerFile = 'relay_runner.py'
                runnerArg = json.dumps([{'name': rb.name,
                                         'startX': float(rb.startX), 'startY': float(rb.startY),
                                         'moveToX': float(rb.moveToX), 'moveToY': float(rb.moveToY)}
                                        for rb in robots])
                taskLabel = '릴레이'
        except (ValueError, TypeError) as e:
            print(f"좌표가 숫자가 아닙니다 — 실행 취소: {e}")
            self.enableUI()
            return

        def _run_legacy():
            print("loco_init_all.sh 스크립트를 실행합니다...")
            try:
                terminal_command = f"gnome-terminal -- bash -c 'bash {self.PATH_LOCO_INIT_SH}; exec bash'"
                process = subprocess.Popen(terminal_command, shell=True)
                process.wait()
                print("loco_init_all.sh 스크립트 실행이 완료되었습니다.\n")
            except Exception as e:
                print(f"터미널을 여는 중 오류가 발생했습니다: {e}")
                self.sigTaskDone.emit()
                return
            print(f"{taskLabel} 작업을 시작합니다.")
            try:
                # ★ 별도 프로세스로 실행 — GUI 안 rospy 는 마스터 재시작(Stop→Start) 후
                #   재초기화가 안 돼 두 번째 협업 실행이 먹통이 된다 (2026-08-08 실측).
                #   새 프로세스면 매번 깨끗하고, Stop(stop_sim.sh)이 실행도 중단시킬 수 있다.
                runner = os.path.join(os.path.dirname(os.path.abspath(__file__)), runnerFile)
                subprocess.run([sys.executable, runner, runnerArg])
                print(f"{taskLabel} 작업이 완료되었습니다.\n")
            except Exception as e:
                print(f"{taskLabel} 실행 오류: {e}")
            self.sigTaskDone.emit()     # UI 복구는 시그널로 (스레드에서 위젯 직접 접근 금지)

        threading.Thread(target=_run_legacy, daemon=True).start()

    # System Message
    def SystemMessage(self, msg):
        current_text = self.ui.pteditROSCollaborationTaskMsg.toPlainText()
        new_text = current_text + msg + "\n"
        self.ui.pteditROSCollaborationTaskMsg.setPlainText(new_text)

        # Move cursor to the end
        cursor = self.ui.pteditROSCollaborationTaskMsg.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.ui.pteditROSCollaborationTaskMsg.setTextCursor(cursor)
        self.ui.pteditROSCollaborationTaskMsg.ensureCursorVisible()

    # 시스템 UI 프리즈
    def disableUI(self):
        self.ui.btnROSCollaborationTaskStart.setEnabled(False)

    # 시스템 UI 릴리즈
    def enableUI(self):
        self.ui.btnROSCollaborationTaskStart.setEnabled(True)

    def showModal(self):
        return super().exec_()
    