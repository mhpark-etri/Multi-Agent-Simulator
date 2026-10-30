########################################################
## Teslasystem Co.,Ltd.                               ##
## 제작 : 박태순                                       ##
## 설명 : 3D Agent Simulator 프로그램의 mainDB 스크립트 ##
########################################################

import mysql.connector

from PySide6 import QtWidgets
from PySide6.QtWidgets import QTableWidgetItem
from ui_dlgDB import Ui_DlgDB


class DialogDB(QtWidgets.QDialog):
    # member
    m_db = None

    # Init
    def __init__(self, host, id, pw, name):
        super().__init__()

        self.ui = Ui_DlgDB()
        self.ui.setupUi(self)

        # MySQL 서버에 연결
        self.m_db = mysql.connector.connect(
            host=host,
            user=id,
            password=pw,
            database=name
        )

        ## UI Event
        self.ui.btnDBOK.clicked.connect(self.CloseDB)
        self.ui.lstDBTableList.itemSelectionChanged.connect(
            self.on_item_selection_changed_DBTableList
        )
        self.finished.connect(self.on_finished)

        ## SetUI
        self.SetUI()

    # Set UI
    def SetUI(self):
        # 커서 생성
        cursor = self.m_db.cursor()

        try:
            # 데이터베이스의 모든 테이블 목록 가져오기
            cursor.execute("SHOW TABLES")

            # 결과 가져오기
            tables = cursor.fetchall()
        finally:
            cursor.close()

        # 테이블 목록 출력
        self.ui.lstDBTableList.clear()

        for table in tables:
            self.ui.lstDBTableList.addItem(table[0])

        if tables:
            self.ui.lstDBTableList.setCurrentRow(0)

    # 컬럼 테이블 내용 변경
    def on_item_selection_changed_DBTableList(self):
        # 컬럼 테이블 정보 삭제
        table = self.ui.tbDB
        table.clear()
        table.setRowCount(0)
        table.setColumnCount(0)

        selected_items = self.ui.lstDBTableList.selectedItems()

        if not selected_items:
            return

        # 커서 생성
        cursor = self.m_db.cursor()

        try:
            # 데이터베이스에서 모든 데이터 가져오기
            table_name = selected_items[0].text().replace("`", "``")
            cursor.execute(f"SELECT * FROM `{table_name}`")
            data = cursor.fetchall()

            # 컬럼명 가져오기
            columns = [column[0] for column in cursor.description]
        finally:
            cursor.close()

        # 테이블의 행과 열 설정
        table.setRowCount(len(data))
        table.setColumnCount(len(columns))

        # 컬럼명을 테이블에 설정
        table.setHorizontalHeaderLabels(columns)

        # 테이블에 데이터 추가
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(value)))

    # Finished 이벤트
    def on_finished(self, result):
        if self.m_db.is_connected():
            self.m_db.close()

    # Close
    def CloseDB(self):
        self.close()

    def showModal(self):
        return super().exec()