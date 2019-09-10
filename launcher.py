from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QGraphicsDropShadowEffect,
    QAbstractButton)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush, QColor, QFont, QFontDatabase, QPixmap, QPainter

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


import requests
import sys
import webbrowser
import os
import subprocess
import winreg
import shutil
import hashlib
import json

class Button(QPushButton):
    def __init__(self, name, pixmap, parent=None):
        super(QPushButton, self).__init__(name, parent)
        self.pixmap = pixmap
        self.name = name

    def enterEvent(self, QEvent):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(255, 255, 255, 255))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def leaveEvent(self, QEvent):
        self.parent()._generate_shadow(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.url_support = "https://www.moddb.com/mods/the-horse-lords-a-total-modification-for-bfme/tutorials/installing-age-of-the-ring-and-common-issues"
        self.url_discord = "https://discord.gg/SHm3QrZ"

        self.about_text_intro = "About Age of the Ring"
        self.about_text_full = "Age of the Ring is a fanmade, not-for-profit game modification. \n The Battle for Middle-earth 2 - Rise of the Witch-king © 2006 Electronic Arts Inc. All Rights Reserved. All “The Lord of the Rings” related content other than content from the New Line Cinema Trilogy of “The Lord of the Rings” films © 2006 The Saul Zaentz Company d/b/a Tolkien Enterprises (”SZC”). All Rights Reserved. All content from “The Lord of the Rings” film trilogy © MMIV New Line Productions Inc. All Rights Reserved. “The Lord of the Rings” and the names of the characters, items, events and places therein are trademarks or registered trademarks of SZC under license."

        self.path_aotr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aotr")
        self.uninstaller = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uninst000.exe")
        self.file_rotwk = "cahfactions.ini"
        self.api_key = "AIzaSyDel_-8cgfVDVBa66eAfETPYx-ATj-jazE"

        self.scopes = ['https://www.googleapis.com/auth/drive.metadata.readonly']
        self.credentials = {"installed":{"client_id":"1079743723117-p6ikghhc5976t34ojs85nsg3hrf5f13e.apps.googleusercontent.com","project_id":"quickstart-1566468291948","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"v5Sn4rX-DrdFlCHNJS8feScy","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}

        self.init_ui()

    def _generate_shadow(self, button):
        shadow = QGraphicsDropShadowEffect(button)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        button.setGraphicsEffect(shadow)

    def init_ui(self):
        self.launch_btn = Button("Play", QPixmap('launcher_assets/launcher_play_button.png'), self)
        self.launch_btn.resize(177, 70)
        self.launch_btn.move(162, 111)
        self.launch_btn.clicked.connect(self.launch)
        self._generate_shadow(self.launch_btn)

        self.update_btn = Button("Update", QPixmap('launcher_assets/launcher_update_button.png'), self)
        self.update_btn.resize(177, 70)
        self.update_btn.move(162, 207)
        self.update_btn.clicked.connect(self.update)
        self._generate_shadow(self.update_btn)

        self.discord_btn = Button("Discord", QPixmap('launcher_assets/launcher_discord_button.png'), self)
        self.discord_btn.resize(87, 34)
        self.discord_btn.move(207, 303)
        self.discord_btn.clicked.connect(lambda: webbrowser.open_new(self.url_discord))
        self._generate_shadow(self.discord_btn)

        self.support_btn = Button("Support", QPixmap('launcher_assets/launcher_support_button.png'), self)
        self.support_btn.resize(87, 34)
        self.support_btn.move(207, 363)
        self.support_btn.clicked.connect(lambda: webbrowser.open_new(self.url_support))
        self._generate_shadow(self.support_btn)
        
        self.about_window = QMessageBox()
        self.about_window.setIcon(QMessageBox.Information)
        self.about_window.setText(self.about_text_intro)
        self.about_window.setInformativeText(self.about_text_full)
        self.about_window.setStandardButtons(QMessageBox.Ok)
        self.about_window.setWindowTitle("About")
        self.about_window.setWindowIcon(QIcon("launcher_assets/aotr.ico"))
        self.about_window.buttonClicked.connect(self.about_window.close)

        bar = self.menuBar()
        bar.setStyleSheet("QMenuBar {background-color: white;}")
        about_act = bar.addAction('About')
        about_act.triggered.connect(self.about_window.show)
        uninstall_act = bar.addAction('Uninstall')
        uninstall_act.triggered.connect(self.uninstall)
        repair_act = bar.addAction('Repair')
        repair_act.triggered.connect(self.repair)

        self.setFixedSize(500, 500)
        self.setWindowTitle('Age of the Ring')
        self.setWindowIcon(QIcon("launcher_assets/aotr.ico"))

        oImage = QImage("launcher_assets/launcherBG.jpg")
        sImage = oImage.scaled(QSize(500, 500))  # resize Image to widgets size
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))  # 10 = WindowRole
        self.setPalette(palette)

        self.show()

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2ep1.exe")
            self.path_rotwk = winreg.EnumValue(key, 5)[1]
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not locate ROTWK installation. Make sure ROTWK is installed", QMessageBox.Ok, QMessageBox.Ok)

    def launch(self):
        #Launch game with the -mod command
        try:
            subprocess.run([f"{self.path_rotwk}\\lotrbfme2ep1.exe", "-mod", f"{self.path_aotr}"])
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)

    def update(self):
        try:
            self.file_fixer()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
        else:
            reply = QMessageBox.information(self, "Update Successful", "Age of the Ring updated, would you like to read the changelog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                webbrowser.open(os.path.join(self.path_aotr, "readme.txt"))

    def repair(self):
        try:
            self.file_fixer()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Repair Successful", "Age of the Ring has been reset to its original state", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

    def uninstall_dialog(self):
        reply = QMessageBox.question(self, 'Uninstall Age of the Ring', "Are you sure you want to uninstall Age of the Rings?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.uninstall()

    def uninstall(self):
        os.remove(f"{self.path_rotwk}\\{self.file_rotwk}")
        subprocess.run([f"{self.uninstaller}"])
        self.close()

    def hash_file(self, path):
        hasher = hashlib.md5()
        with open(path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)

        return hasher.hexdigest()

    def file_fixer(self):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            q="'11B-ugfKzzjjtFZ4fYfxwQaiu2BqKPkTq' in parents",
            pageSize=10, fields="*").execute()
        files = results.get('files', [])
        tree = next((file for file in files if file['name'] == "tree.json"), None)
        r = requests.get(tree["webContentLink"])
        tree = json.loads(r.content.decode('utf-8'))

        for file in tree:
            full_path = os.path.join(self.path_aotr, file["path"])
            if not os.path.exists(full_path):
                #download new files
                download = next((f for f in files if f['name'] == file["name"]), None)
                r = requests.get(download["webContentLink"])
                with open(full_path, "wb") as f:
                    f.write(r.content)
            else:
                md5 = self.hash_file(full_path)
                if md5 != file["hash"]:
                    #update existing files
                    download = next((f for f in files if f['name'] == file["name"]), None)
                    r = requests.get(download["webContentLink"])
                    with open(full_path, "wb") as f:
                        f.write(r.content)

    def about(self):
        self.about_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = Launcher()
    sys.exit(app.exec_())
