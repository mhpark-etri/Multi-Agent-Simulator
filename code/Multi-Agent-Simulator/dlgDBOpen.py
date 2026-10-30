######################################################
## Teslasystem Co.,Ltd.                             ##
## 제작 : 박태순                                      ## 
## 설명 : DBOpen Dialog                              ##
######################################################

import mysql.connector

from PySide6 import QtWidgets
from PySide6.QtCore import QSettings
from ui_dlgDBOpen import Ui_DlgDBOpen
from dlgDB import DialogDB

from constant import *


class DialogDBOpen(QtWidgets.QDialog):

    # Init
    def __init__(self):
        super().__init__()

        self.ui = Ui_DlgDBOpen()
        self.ui.setupUi(self)

        # UI Event
        self.ui.dlgBtnDBOpen.clicked.connect(self.OpenDB)
        self.ui.dlgBtnDBClose.clicked.connect(self.CloseDBOpen)

        # Preference
        self.settings = QSettings(SETTING_COMPANY, SETTING_APP)  # 설정 파일 이름 설정

        # 기본 정보 ID PW 정보 불러오기
        dbID = self.settings.value(SETTING_DB_ID)
        if dbID is None:
            dbID = SETTING_DB_ID

        dbPW = self.settings.value(SETTING_DB_PW)
        if dbPW is None:
            dbPW = CONST_SETTING_DB_PW

        self.ui.dlgEdtDBID.setText(dbID)
        self.ui.dlgEdtDBPW.setText(dbPW)

    # DB 연결 여부
    def connect_to_database(self, host, user, password, database):
        try:
            # MySQL 서버에 연결 시도
            mydb = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            print("Database 연결 성공")
            mydb.close()
            return True

        except mysql.connector.Error as err:
            # 연결 실패 시 오류 메시지 출력
            print("Database 연결 실패:", err)
            return False

    # DB 연동
    def OpenDB(self):
        # 먼저 ID PW 비어있나 체크
        editID = self.ui.dlgEdtDBID.toPlainText()
        editPW = self.ui.dlgEdtDBPW.toPlainText()

        if not editID:
            QtWidgets.QMessageBox.question(
                self, 'Open DB', "Please input your ID.",
                QtWidgets.QMessageBox.Ok
            )
            return

        if not editPW:
            QtWidgets.QMessageBox.question(
                self, 'Open DB', "Please input your Password.",
                QtWidgets.QMessageBox.Ok
            )
            return

        # DB 연결
        if self.connect_to_database(
            CONST_SETTING_DB_DEFAULT_HOST,
            editID,
            editPW,
            CONST_SETTING_DB_DEFAULT_NAME
        ):
            dlg = DialogDB(
                CONST_SETTING_DB_DEFAULT_HOST,
                editID,
                editPW,
                CONST_SETTING_DB_DEFAULT_NAME
            )
            dlg.showModal()
            self.close()

        else:
            QtWidgets.QMessageBox.question(
                self, 'Open DB', "Please verify your ID and password.",
                QtWidgets.QMessageBox.Ok
            )

    # DB 연동 종료
    def CloseDBOpen(self):
        self.close()

    def showModal(self):
        return super().exec()