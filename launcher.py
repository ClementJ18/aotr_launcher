from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QGraphicsDropShadowEffect,
    QAbstractButton, QProgressBar, QInputDialog)
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush, QColor, QFont, QFontDatabase, QPixmap, QPainter

import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


import requests
import sys
import webbrowser
import os
import subprocess
import winreg
import hashlib
import json
import logging
import datetime
import traceback
import shutil
from pathlib import Path
import time


logging.basicConfig(level=logging.DEBUG, filename= os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher.log"), filemode="w")

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

class ProgressBar(QMainWindow):
    def __init__(self, parent=None):
        super(ProgressBar, self).__init__(parent)

        self.init_ui()

    def init_ui(self):
        self.label = QLabel("Gathering file data...", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.move(50, 50)
        self.label.resize(self.label.sizeHint())

        self.bar = QProgressBar(self)
        self.bar.move(50, 100)
        self.bar.resize(400, 25)      

        self.setFixedSize(500, 200)
        self.setWindowTitle('Update Progress')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))

class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.url_support = "https://www.moddb.com/mods/the-horse-lords-a-total-modification-for-bfme/tutorials/installing-age-of-the-ring-and-common-issues"
        self.url_discord = "https://discord.gg/SHm3QrZ"
        self.url_wiki    = "https://aotr.wikia.com/wiki/AOTR_Wiki"
        self.url_forums  = "https://forums.revora.net/forum/2601-age-of-the-ring/"

        self.about_text_intro = "About Age of the Ring"
        self.about_text_full = "Age of the Ring is a fanmade, not-for-profit game modification. \n The Battle for Middle-earth 2 - Rise of the Witch-king © 2006 Electronic Arts Inc. All Rights Reserved. All “The Lord of the Rings” related content other than content from the New Line Cinema Trilogy of “The Lord of the Rings” films © 2006 The Saul Zaentz Company d/b/a Tolkien Enterprises (”SZC”). All Rights Reserved. All content from “The Lord of the Rings” film trilogy © MMIV New Line Productions Inc. All Rights Reserved. “The Lord of the Rings” and the names of the characters, items, events and places therein are trademarks or registered trademarks of SZC under license. \n\n The launcher was created by Necro#6714, full source code is available at: https://github.com/ClementJ18/aotr_launcher"

        self.path_aotr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aotr")
        self.uninstaller = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path_flags = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/flags.txt")
        self.file_rotwk = "cahfactions.ini"
        self.folder_id = '1LgPndLiRyS93Sl9HwNCTOnKh7_Kmop4D'

        self.scopes = ['https://www.googleapis.com/auth/drive.metadata.readonly']

        creds = None
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/token.pickle"), 'rb') as token:
            creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

        service = build('drive', 'v3', credentials=creds)
        self.files_service = service.files()

        self.init_ui()

    def _generate_shadow(self, button):
        shadow = QGraphicsDropShadowEffect(button)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        button.setGraphicsEffect(shadow)

    def init_ui(self):
        self.launch_btn = Button("Play", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_play_button.png')), self)
        self.launch_btn.resize(177, 70)
        self.launch_btn.move(162, 111)
        self.launch_btn.clicked.connect(self.launch)
        self._generate_shadow(self.launch_btn)

        self.update_btn = Button("Update", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher_update_button.png")), self)
        self.update_btn.resize(177, 70)
        self.update_btn.move(162, 207)
        self.update_btn.clicked.connect(self.update)
        self._generate_shadow(self.update_btn)

        self.discord_btn = Button("Discord", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_discord_button.png')), self)
        self.discord_btn.resize(87, 34)
        self.discord_btn.move(207, 303)
        self.discord_btn.clicked.connect(lambda: webbrowser.open_new(self.url_discord))
        self._generate_shadow(self.discord_btn)

        self.support_btn = Button("Support", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_support_button.png')), self)
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
        self.about_window.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))
        self.about_window.buttonClicked.connect(self.about_window.close)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()

        bar = self.menuBar()
        bar.setStyleSheet("QMenuBar {background-color: white;}")
        about_act = bar.addAction('About')
        about_act.triggered.connect(self.about_window.show)
        repair_act = bar.addAction('Repair')
        repair_act.triggered.connect(self.repair)
        wiki_act = bar.addAction('Wiki')
        wiki_act.triggered.connect(lambda: webbrowser.open_new(self.url_wiki))
        forums_act = bar.addAction('Forums')
        forums_act.triggered.connect(lambda: webbrowser.open_new(self.url_forums))
        
        options_menu = bar.addMenu("Options")
        flags_act = options_menu.addAction("Launch Flags")
        flags_act.triggered.connect(self.flags_dialog)
        uninstall_act = options_menu.addAction('Uninstall')
        uninstall_act.triggered.connect(self.uninstall_dialog)

        self.setFixedSize(500, 500)
        self.setWindowTitle('Age of the Ring')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))

        oImage = QImage(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcherBG.jpg"))
        sImage = oImage.scaled(QSize(500, 500)) 
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))
        self.setPalette(palette)

        self.show()

        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2ep1.exe")
            self.path_rotwk = winreg.EnumValue(key, 5)[1]
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not locate ROTWK installation. Make sure ROTWK is installed", QMessageBox.Ok, QMessageBox.Ok)

        if os.path.exists(os.path.join(self.path_aotr, "tree.json")):
            request = self.files_service.list(q=f"'{self.folder_id}' in parents and name = 'tree.json'", pageSize=1000, fields="nextPageToken, files(id, name, webContentLink)").execute()
            r = requests.get(request["files"][0]["webContentLink"])
            
            with open(os.path.join(self.path_aotr, "tree.json"), "r") as f:
                version = json.load(f)["version"]
                version_online = json.loads(r.content.decode('utf-8'))["version"]

                if version != version_online:
                    QMessageBox.information(self, "Update Available", "An update is available, click the update button to begin updating.",    QMessageBox.Ok, QMessageBox.Ok)
        else:
            QMessageBox.information(self, "Update Available", "An update is available, click the update button to begin updating.",    QMessageBox.Ok, QMessageBox.Ok)

        Path(self.path_flags).touch(exist_ok=True)

    def flags_dialog(self):
        with open(self.path_flags, "r") as f:
            current_flags = f.read()

        new_flags, ok = QInputDialog.getText(self, "Flags","Additional launch flags: ", 
            QLineEdit.Normal, current_flags, flags=Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        if ok:
            with open(self.path_flags, "w") as f:
                f.write(new_flags)

    def launch(self):
        #Launch game with the -mod command
        with open(self.path_flags, "r") as f:
            flags = f.read().split(" ")

        try:
            subprocess.Popen([os.path.join(self.path_aotr, "BFME2X.exe")], cwd=self.path_aotr)
            time.sleep(5)
            subprocess.Popen([os.path.join(self.path_rotwk, "lotrbfme2ep1.exe"), "-mod", f"{self.path_aotr}", *flags], cwd=self.path_aotr)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)

    def update(self):
        try:
            updated = self.file_fixer()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()
        else:
            if updated:
                reply = QMessageBox.information(self, "Update Successful", "Age of the Ring updated, would you like to read the changelog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    webbrowser.open(os.path.join(self.path_aotr, "AgeOfTheRing_README.rtf"))
            else:
                QMessageBox.information(self, "No Update", "No new update was available, no files have been modified.", QMessageBox.Ok, QMessageBox.Ok)

    def repair(self):
        try:
            self.file_fixer()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()
        else:
            QMessageBox.information(self, "Repair Successful", "Age of the Ring has been reset to its original state", QMessageBox.Ok, QMessageBox.Ok)

    def uninstall_dialog(self):
        reply = QMessageBox.question(self, 'Uninstall Age of the Ring', "Are you sure you want to uninstall Age of the Ring?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.uninstall()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)

    def uninstall(self):
        shutil.rmtree(self.path_aotr)
        try:
            os.remove(os.path.join(self.path_rotwk, self.file_rotwk))
        except FileNotFoundError:
            pass
        
        folder = '{}'.format(os.path.dirname(os.path.abspath(__file__)))
        print(self.uninstaller)
        subprocess.Popen(['timeout', '5', '&', 'rmdir', '/Q', '/S', folder], shell=True, cwd=self.uninstaller)
        self.close()

    def hash_file(self, path):
        hasher = hashlib.md5()
        with open(path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)

        return hasher.hexdigest()

    def file_fixer(self):
        self.progress_bar.label.setText("Gathering file data...")
        self.progress_bar.label.resize(self.progress_bar.label.sizeHint())
        self.progress_bar.bar.setValue(0)
        self.progress_bar.show()
        # check if update is possible by making sure that files aren't currently being uploaded.
        folder = self.files_service.get(fileId=self.folder_id, fields="*").execute()
        
        # results = self.activity_service.query(body={
        #     'pageSize': 10
        # }).execute()
        # activities = results.get('activities', [])

        modified_by = datetime.datetime.strptime(folder["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fz")
        if modified_by > (datetime.datetime.now() - datetime.timedelta(minutes=30)):
            raise ValueError("Cannot currently update, please try again later.")

        request = self.files_service.list(q=f"'{self.folder_id}' in parents", pageSize=1000, fields="nextPageToken, files(id, name, webContentLink)")

        files = []
        counter = 0
        while request is not None:
            QCoreApplication.processEvents()
            result = request.execute()
            counter += 1
            self.progress_bar.bar.setValue((counter/20)*100)
            files.extend(result.get("files", []))
            request = self.files_service.list_next(request, result)

        try:
            tree = next((file for file in files if file['name'] == "tree.json"), None)
            r = requests.get(tree["webContentLink"])
        except TypeError:
            raise TypeError("Did not find tree.json, please report this bug to the discord.")

        with open(os.path.join(self.path_aotr, "tree.json"), "wb") as f:
            f.write(r.content)

        self.progress_bar.label.setText("Verifying file integrity...")
        self.progress_bar.label.resize(self.progress_bar.label.sizeHint())
        tree = json.loads(r.content.decode('utf-8'))
        tree_len = len(tree["files"])
        tree_values = list(tree["files"].values())
        to_download = []
        for file in tree_values:
            QCoreApplication.processEvents()
            self.progress_bar.bar.setValue((tree_values.index(file)/tree_len)*100)
            full_path = os.path.join(self.path_aotr, file["path"])
            download = next((f for f in files if f['name'] == file["path"].replace("\\", ".")), None)
            if download is None:
                QMessageBox.critical(self, "Error", f"Could not find file {file['name']} online", QMessageBox.Ok, QMessageBox.Ok)
                continue

            if not os.path.exists(full_path):
                #download new files
                to_download.append({"link": download["webContentLink"], "path": full_path})
                logging.debug(f"Downloaded {file['path']}")
            else:
                md5 = self.hash_file(full_path)
                if md5 != file["hash"]:
                    #update existing files
                    to_download.append({"link": download["webContentLink"], "path": full_path})
                    logging.debug(f"Downloaded {file['path']}")
                else:
                    logging.debug(f"Did not download file {file['path']}")

        if not to_download:
            self.progress_bar.hide()
            return False

        #actually downloadfiles
        self.progress_bar.label.setText("Downloading files...")
        self.progress_bar.label.resize(self.progress_bar.label.sizeHint())
        for file in to_download:
            QCoreApplication.processEvents()
            self.progress_bar.bar.setValue((to_download.index(file)/len(to_download))*100)
            r = requests.get(file["link"])
            os.makedirs(os.path.dirname(file["path"]), exist_ok=True)
            with open(file["path"], "wb") as f:
                f.write(r.content)

        #figure out which things need to get removed
        self.progress_bar.label.setText("Cleanup...")
        self.progress_bar.label.resize(self.progress_bar.label.sizeHint())
        self.progress_bar.bar.setValue(0)
        counter = 0
        for path, _, files in os.walk(self.path_aotr):
            for name in files:
                QCoreApplication.processEvents()
                if name in ["desktop.ini", "tree.json"]:
                    continue

                file_path = os.path.join(path, name)
                subdir_path = file_path.replace(f"{self.path_aotr}\\", '')

                if subdir_path not in tree["files"]:
                    logging.debug(f"Detected foreign file: {subdir_path}")
                    os.remove(file_path)
            counter += 1
            self.progress_bar.bar.setValue((counter%20)/20)

        self.progress_bar.hide()
        return True

    def about(self):
        self.about_window.show()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        gui = Launcher()
        app.exec_()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sam =  traceback.format_exception(exc_type, exc_value, exc_traceback)
        logging.error(sam)
