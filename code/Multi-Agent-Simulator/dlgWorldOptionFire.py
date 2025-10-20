######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                     ## 
## 설명 : WorldOption Fire Dialog                    ##
######################################################
import os
from PySide6 import QtWidgets
from PySide6.QtCore import QSettings, Qt, QProcess
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QFileDialog, QMessageBox, QPushButton, QLineEdit, QProgressDialog, QApplication
from ui_dlgWorldOptionFire import Ui_DlgWorldOptionFire
import subprocess

from constant import *
from simulator import *

class DialogWorldOptionFire(
    QtWidgets.QDialog):

    DEFAULT_VALUE_PARTICLE_FOLDER = "/root/tesla/particle_emitter"
    DEFAULT_VALUE_SPAWN_PARTICLE_PATH = "/root/tesla/particle_emitter/spawn_particles.py"
    DEFAULT_VALUE_PARTICLE_EMITTER_PATH = "/root/tesla/particle_emitter/particle_emitter.py"
    DEFAULT_VALUE_SDF_FILE_PATH = "/root/tesla/particle_emitter/particle_template_grey.sdf"
    DEFAULT_VALUE_PARTICLE_COUNT = "300"
    DEFAULT_VALUE_GROUP_COUNT = "15"
    DEFAULT_VALUE_SPREAD_SCALE = "0.3"

    # Init
    def __init__(self):
        super().__init__()
        self.ui = Ui_DlgWorldOptionFire()
        self.ui.setupUi(self)

        self.processParticleEmitter = QProcess(self)

        # Preference
        self.settings = QSettings(SETTING_COMPANY, SETTING_APP)  # 설정 파일 이름 설정
        self.Load_World_Option_Fire()

        # 이벤트 연결
        self.ui.btnWorldOptionFireStart.clicked.connect(self.StartFireSimulate)
        self.ui.btnWorldOptionFireCancel.clicked.connect(self.Cancel)
        self.ui.btnWorldOptionFireSpawnParticlesOpen.clicked.connect(self.OpenSpawnParticlePath)
        self.ui.btnWorldOptionFireParticleEmitterOpen.clicked.connect(self.OpenParticleEmitterPath)
        self.ui.btnWorldOptionFireSDFPathOpen.clicked.connect(self.OpenSDFFilePath)
        self.ui.leditWorldOptionFireParticleCount.textChanged.connect(self.onWorldOptionFireParticleCountChanged)
        self.ui.leditWorldOptionFireGroupCount.textChanged.connect(self.onWorldOptionFireGroupCountChanged)
        self.ui.leditWorldOptionFireSpreadScale.textChanged.connect(self.onWorldOptionFireSpreadScaleChanged)

    # 로봇 정보 변경
    def onRobotChanged(self, index):
        self.m_currentSimulatorIdx = index
        # X,Y,Z 포지션 정보 업데이트
        posX = float(self.m_simulator.robots[index].startX)
        posY = float(self.m_simulator.robots[index].startY)
        posZ = float(self.m_simulator.robots[index].startZ)
        self.ui.ledtROSNaviRobotsPosX.setText(f"{posX:.1f}")
        self.ui.ledtROSNaviRobotsPosY.setText(f"{posY:.1f}")
        self.ui.ledtROSNaviRobotsPosZ.setText(f"{posZ:.1f}")
    
    # Particle Count 변경
    def onWorldOptionFireParticleCountChanged(self, text):
        if self.CheckIsNumber(text):
            pass
        else:
            self.ShowWarningMsg("You can only enter numbers.")

    # Groud Count 변경
    def onWorldOptionFireGroupCountChanged(self, text):
        if self.CheckIsNumber(text):
            pass
        else:
            self.ShowWarningMsg("You can only enter numbers.")

    # Spread Scale 변경
    def onWorldOptionFireSpreadScaleChanged(self, text):
        if self.CheckIsNumber(text):
            pass
        else:
            self.ShowWarningMsg("You can only enter numbers.")

    # 숫자인지 점검
    def CheckIsNumber(self, text):
        try:
            # float로 변환 가능하면 숫자
            float(text)
            return True
        except ValueError:
            # 변환할 수 없으면 숫자가 아님
            return False

    # 경고창 출력
    def ShowWarningMsg(self, msg):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Warning")
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    # Spawn Paricle 경로 입력
    def OpenSpawnParticlePath(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly 
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", self.DEFAULT_VALUE_PARTICLE_FOLDER, "Spawn Particle Files (*.py)", options=options
        )

        if file_name:
            print("Selected file:", file_name)
            # 경로 입력
            self.ui.leditWorldOptionFireSpawnParticlesPath.setText(file_name)

    # Particle Emitter 경로 입력
    def OpenParticleEmitterPath(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly 
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", self.DEFAULT_VALUE_PARTICLE_FOLDER, "Particle Emitter Files (*.py)", options=options
        )

        if file_name:
            print("Selected file:", file_name)
            # 경로 입력
            self.ui.leditWorldOptionFireParticleEmitterPath.setText(file_name)

    # SDF 파일 경로 입력
    def OpenSDFFilePath(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly 
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", self.DEFAULT_VALUE_PARTICLE_FOLDER, "SDF Files (*.sdf)", options=options
        )

        if file_name:
            print("Selected file:", file_name)
            # 경로 입력
            self.ui.leditWorldOptionFireSDFFilePath.setText(file_name)

    # 화재 시뮬레이팅 시작
    def StartFireSimulate(self):
        spawnParticlePath =  self.ui.leditWorldOptionFireSpawnParticlesPath.text()
        particleEmitterPath = self.ui.leditWorldOptionFireParticleEmitterPath.text()
        sdfFilePath = self.ui.leditWorldOptionFireSDFFilePath.text()
        particleCount = self.ui.leditWorldOptionFireParticleCount.text()
        groupCount = self.ui.leditWorldOptionFireGroupCount.text()
        spreadScale = self.ui.leditWorldOptionFireSpreadScale.text()

        # ===== 로딩 다이얼로그 생성 =====
        progress = QProgressDialog("입자 생성 중...", None, 0, 0, self)
        progress.setWindowTitle("작업 진행 중")
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)   # 취소 버튼 제거
        progress.show()
        QApplication.processEvents()

        # 1. Particle 생성
        cmd = [
            "python3", spawnParticlePath,
            "-n", particleCount,
            "-f", sdfFilePath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("[성공] Spawn 스크립트 실행 완료")
        else:
            print("[실패] Spawn 스크립트 오류")
            print(result.stderr)
            progress.close()
            self.ShowWarningMsg("Spawn_Paricle 문제 발생.")
            return

        # ===== 로딩 다이얼로그 텍스트 변경 =====
        progress.setLabelText("입자 방출 시작 중...")
        QApplication.processEvents()

        # 2. Paricle 방출 시작
        self.processParticleEmitter.setProgram("python3")
        self.processParticleEmitter.setArguments([
            particleEmitterPath,
            "--particle-count", particleCount,
            "--group-count", groupCount,
            "--spread-scale", spreadScale
        ])
        self.processParticleEmitter.readyReadStandardOutput.connect(lambda: print(self.processParticleEmitter.readAllStandardOutput().data().decode()))
        self.processParticleEmitter.readyReadStandardError.connect(lambda: print(self.processParticleEmitter.readAllStandardError().data().decode()))
        self.processParticleEmitter.finished.connect(lambda: print("[완료] fire_emitter 종료됨"))
        self.processParticleEmitter.start()

        progress.close()  # 로딩 다이얼로그 닫기
    
    # 작업 취소
    def Cancel(self):
        self.close()

    # 마지막으로 저장 된 화재 옵션 불러오기
    def Load_World_Option_Fire(self):
        # 1. Spawn Particle Path
        lastWorldOptionFireSpawnParticle = self.settings.value(SETTING_WORLD_OPTION_FIRE_SPAWN_PARTICLE_PATH)
        if lastWorldOptionFireSpawnParticle is not None:
            self.ui.leditWorldOptionFireSpawnParticlesPath.setText(lastWorldOptionFireSpawnParticle)
        else:
            self.ui.leditWorldOptionFireSpawnParticlesPath.setText(self.DEFAULT_VALUE_SPAWN_PARTICLE_PATH)

        # 2. Particle Emitter Path
        lastWorldOptionFireParticleEmitter = self.settings.value(SETTING_WORLD_OPTION_FIRE_PARTICLE_EMITTER_PATH)
        if lastWorldOptionFireParticleEmitter is not None:
            self.ui.leditWorldOptionFireParticleEmitterPath.setText(lastWorldOptionFireParticleEmitter)
        else:
            self.ui.leditWorldOptionFireParticleEmitterPath.setText(self.DEFAULT_VALUE_PARTICLE_EMITTER_PATH)

        # 3. SDF File Path
        lastWorldOptionFireSDFFilePath = self.settings.value(SETTING_WORLD_OPTION_FIRE_SDF_FILE_PATH)
        if lastWorldOptionFireSDFFilePath is not None:
            self.ui.leditWorldOptionFireSDFFilePath.setText(lastWorldOptionFireSDFFilePath)
        else:
            self.ui.leditWorldOptionFireSDFFilePath.setText(self.DEFAULT_VALUE_SDF_FILE_PATH)

        # 4. Particle Count
        lastWorldOptionFireParticleCount= self.settings.value(SETTING_WORLD_OPTION_FIRE_PARTICLE_COUNT)
        if lastWorldOptionFireParticleCount is not None:
            self.ui.leditWorldOptionFireParticleCount.setText(lastWorldOptionFireParticleCount)
        else:
            self.ui.leditWorldOptionFireParticleCount.setText(self.DEFAULT_VALUE_PARTICLE_COUNT)

        # 5. Group Count
        lastWorldOptionFireGroupCount= self.settings.value(SETTING_WORLD_OPTION_FIRE_GROUP_COUNT)
        if lastWorldOptionFireGroupCount is not None:
            self.ui.leditWorldOptionFireGroupCount.setText(lastWorldOptionFireGroupCount)
        else:
            self.ui.leditWorldOptionFireGroupCount.setText(self.DEFAULT_VALUE_GROUP_COUNT)

        # 6. Spread Scale
        lastWorldOptionFireSpreadScale= self.settings.value(SETTING_WORLD_OPTION_FIRE_SPREAD_SCALE)
        if lastWorldOptionFireSpreadScale is not None:
            self.ui.leditWorldOptionFireSpreadScale.setText(lastWorldOptionFireSpreadScale)
        else:
            self.ui.leditWorldOptionFireSpreadScale.setText(self.DEFAULT_VALUE_SPREAD_SCALE)

    # 화재 옵션 정보 저장
    def Savel_World_Option_Fire(self):
        # 1. Spawn Particle Path
        spawnParticlePath = self.ui.leditWorldOptionFireSpawnParticlesPath.text()
        if spawnParticlePath is not None:
            self.settings.setValue(SETTING_WORLD_OPTION_FIRE_SPAWN_PARTICLE_PATH, spawnParticlePath)
            
        # 2. Particle Emitter Path
        particleEmitterPath = self.ui.leditWorldOptionFireParticleEmitterPath.text()
        if particleEmitterPath is not None:
            self.settings.setValue(SETTING_WORLD_OPTION_FIRE_PARTICLE_EMITTER_PATH, particleEmitterPath)

        # 3. SDF File Path
        SDFFilePath = self.ui.leditWorldOptionFireSDFFilePath.text()
        if SDFFilePath is not None:
            self.settings.setValue(SETTING_WORLD_OPTION_FIRE_SDF_FILE_PATH, SDFFilePath)

        # 4. Particle Count
        particleCount = self.ui.leditWorldOptionFireParticleCount.text()
        if particleCount is not None:
            self.settings.setValue(SETTING_WORLD_OPTION_FIRE_PARTICLE_COUNT, particleCount)

        # 5. Group Count
        groupCount = self.ui.leditWorldOptionFireGroupCount.text()
        if groupCount is not None:
            self.settings.setValue(SETTING_WORLD_OPTION_FIRE_GROUP_COUNT, groupCount)

        # 6. Spread Scale
        spreadScale = self.ui.leditWorldOptionFireSpreadScale.text()
        if spreadScale is not None:
            self.settings.setValue(SETTING_WORLD_OPTION_FIRE_SPREAD_SCALE, spreadScale)

    def showModal(self):
        return super().exec_()
        