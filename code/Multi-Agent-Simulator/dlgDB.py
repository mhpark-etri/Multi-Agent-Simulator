########################################################
## Teslasystem Co.,Ltd.                               ##
## 제작 : 박태순                                       ##
## 설명 : 3D Agent Simulator 프로그램의 mainDB 스크립트 ##
########################################################
from PySide6 import QtWidgets
from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtCore import Qt
from ui_dlgDB import Ui_DlgDB
import mysql.connector

from constant import *

class DialogDB(QtWidgets.QDialog):
    # member
    m_DB_HOST = ""
    m_DB_ID = ""
    m_DB_PW = ""
    m_DB_NAME = ""
    m_db = ""

    # Init
    def __init__(self, host, id, pw, name):
        super().__init__()
        self.ui = Ui_DlgDB()
        self.ui.setupUi(self)
        self.m_DB_HOST = host
        self.m_DB_ID = id
        self.m_DB_PW = pw
        self.m_DB_NAME = name

        # MySQL 서버에 연결
        self.m_db = mysql.connector.connect(
            host=self.m_DB_HOST,
            user=self.m_DB_ID,
            password=self.m_DB_PW,
            database=self.m_DB_NAME
        )

        ## UI Event
        self.ui.btnDBOK.clicked.connect(self.CloseDB)
        self.ui.lstDBTableList.itemSelectionChanged.connect(self.on_item_selection_changed_DBTableList)

        ## SetUI
        self.SetUI()

    # Set UI
    def SetUI(self):
        # 커서 생성
        mycursor = self.m_db.cursor()

        # 데이터베이스의 모든 테이블 목록 가져오기
        mycursor.execute("SHOW TABLES")

        # 결과 가져오기
        tables = mycursor.fetchall()

        # 테이블 목록 출력
        self.ui.lstDBTableList.clear()
        for table in tables:
            self.ui.lstDBTableList.addItem(table[0])

        self.ui.lstDBTableList.setCurrentRow(0)

    # 컬럼 테이블 내용 변경
    def on_item_selection_changed_DBTableList(self):
        # 컬럼 테이블 정보 삭제
        self.ui.tbDB.clear()

        # 커서 생성
        mycursor = self.m_db.cursor()

        # 데이터베이스에서 모든 데이터 가져오기
        selected_items = self.ui.lstDBTableList.selectedItems()
        strSQL = "SELECT * FROM " + selected_items[0].text()
        mycursor.execute(strSQL)
        data = mycursor.fetchall()

        # 컬럼명 가져오기
        columns = [column[0] for column in mycursor.description]

        # 테이블의 행과 열 설정
        self.ui.tbDB.setRowCount(len(data)) # 데이터의 행 수
        self.ui.tbDB.setColumnCount(len(data[0])) # 데이터의 열 수

        # 컬럼명을 테이블에 설정
        self.ui.tbDB.setHorizontalHeaderLabels(columns)

        # 테이블에 데이터 추가
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.ui.tbDB.setItem(i, j, item)

    # Finished 이벤트
    def on_finished(self, result):
        self.m_db.close()

    # Close
    def CloseDB(self):
        self.close()

    def showModal(self):
        return super().exec_()