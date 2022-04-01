import sys
import requests
from datetime import datetime, timedelta
from itertools import cycle
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton
from PyQt5.QtWidgets import QLineEdit, QWidget, QGridLayout, QPlainTextEdit
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class Worker(QObject):
    finished = pyqtSignal()

    def run(self):
        key = app.key_input.text().strip()
        token = app.token_input.text().strip()

        date_ini = datetime.strptime(app.ini_input.text().strip(), '%Y-%m-%d')
        date_end = datetime.strptime(app.end_input.text().strip(), '%Y-%m-%d')

        try:
            breaks = app.breaks_input.text().split(',')
            bdates = [datetime.strptime(b.strip(), '%Y-%m-%d') for b in breaks]
        except ValueError:
            bdates = []

        dates = []
        date_aux = date_ini
        while date_aux < date_end:
            if date_aux not in bdates:
                dates.append(date_aux)
            date_aux += timedelta(days=7)

        m_list = app.members_input.toPlainText()
        members = [member.upper().strip() for member in m_list.split(',')]

        members.sort()

        rgs = list(zip(dates, cycle(members)))

        for n, rg in enumerate(rgs):
            app.create_card(key, token, rg, n + 1)


class App(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('AutoRG')

        self.cw = QWidget()
        self.grid = QGridLayout(self.cw)

        self.auth_label = QLabel(
            'Inform your Trello API Key and access token:'
        )

        self.key_label = QLabel('API Key:')
        self.key_input = QLineEdit('')

        self.token_label = QLabel('Token:')
        self.token_input = QLineEdit(
            ''
        )

        self.dates_label = QLabel(
            'Inform the period of meetings in YYYY-MM-DD format:'
        )
        self.dates_label.setStyleSheet('margin-top: 20px;')

        self.ini_label = QLabel('Initial date:')
        self.ini_input = QLineEdit()

        self.end_label = QLabel('Final date:')
        self.end_input = QLineEdit()

        self.breaks_label = QLabel(
            "Inform the dates that won't have meetings (comma-separated):"
        )
        self.breaks_label.setStyleSheet('margin-top: 20px;')
        self.breaks_input = QLineEdit('YYYY-MM-DD, YYYY-MM-DD')

        self.members_label = QLabel(
            'Members responsible for the minutes (comma-separated):'
        )
        self.members_label.setStyleSheet('margin-top: 20px;')
        self.members_input = QPlainTextEdit('ABC, XYZ, CVP')

        self.submit = QPushButton('Create cards')
        self.submit.clicked.connect(self.fill_trello)

        self.grid.addWidget(self.auth_label, 0, 0, 1, 2)
        self.grid.addWidget(self.key_label, 1, 0, 1, 1)
        self.grid.addWidget(self.token_label, 1, 1, 1, 1)
        self.grid.addWidget(self.key_input, 2, 0, 1, 1)
        self.grid.addWidget(self.token_input, 2, 1, 1, 1)
        self.grid.addWidget(self.dates_label, 3, 0, 1, 2)
        self.grid.addWidget(self.ini_label, 4, 0, 1, 1)
        self.grid.addWidget(self.end_label, 4, 1, 1, 1)
        self.grid.addWidget(self.ini_input, 5, 0, 1, 1)
        self.grid.addWidget(self.end_input, 5, 1, 1, 1)
        self.grid.addWidget(self.breaks_label, 6, 0, 1, 2)
        self.grid.addWidget(self.breaks_input, 7, 0, 1, 2)
        self.grid.addWidget(self.members_label, 8, 0, 1, 2)
        self.grid.addWidget(self.members_input, 9, 0, 1, 2)
        self.grid.addWidget(self.submit, 10, 0, 1, 2)

        self.setCentralWidget(self.cw)

    def create_card(self, key, token, rg, n):
        url = 'https://api.trello.com/1/cards'
        querystring = {
            'name': f'Reunião {n} ({rg[0].strftime("%d/%m")}) - {rg[1]}',
            'idCardSource': '',  # Card that will be copied
            'keepFromSource': ['checklists', 'customFields', 'labels'],
            'pos': 'bottom',
            'idList': '',  # List where the card will be created
            'key': key,
            'token': token
        }
        requests.request('POST', url, params=querystring)

    def fill_trello(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        self.submit.setDisabled(True)
        self.thread.finished.connect(
            lambda: self.submit.setDisabled(False)
        )


if __name__ == '__main__':
    qt = QApplication(sys.argv)
    app = App()
    app.show()
    qt.exec_()
