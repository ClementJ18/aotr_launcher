from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QGraphicsDropShadowEffect,
    QAbstractButton, QProgressBar, QInputDialog, QDialog)
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush, QColor, QPixmap, QPainter

import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import TransportError

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
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random

logging.basicConfig(level=logging.DEBUG, filename= os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher.log"), filemode="w")

user_agent_list = [
    #Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    #Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]

# this allows us to create our buttons with custom images and generate the highligh on hover, this does break writing 
# on top of the buttons so we cheat by just putting the text on the image
class Button(QPushButton):
    def __init__(self, name, pixmap, parent=None):
        super(QPushButton, self).__init__(name, parent)
        self.pixmap = pixmap
        self.name = name

    def enterEvent(self, QEvent):
        #generate white highlight
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(255, 255, 255, 255))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def leaveEvent(self, QEvent):
        #reset to normal shadow
        self.parent()._generate_shadow(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

# this is the progress bar for the update process, this is initialzied during the creation of the GUI
# and then we hide it and only show it when the user clicks on the button.
class ProgressBar(QDialog):
    def __init__(self, parent=None):
        super(ProgressBar, self).__init__(parent)
        self.init_ui()

        self.in_progress = True

    def change_text(self, text):
        self.label.setText(text)
        self.label.resize(self.label.sizeHint())

    def change_percent(self, value):
        self.bar.setValue(value)

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
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint)

    def closeEvent(self, evnt):
        if not self.in_progress:
            super(ProgressBar, self).closeEvent(evnt)
        else:
            evnt.ignore()

    def keyPressEvent(self, evnt):
        if not evnt.key() == Qt.Key_Escape:
            super(ProgressBar, self).keyPressEvent(evnt)

#main window
class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        #links for the menu buttons
        self.url_support = "https://www.moddb.com/mods/the-horse-lords-a-total-modification-for-bfme/tutorials/installing-age-of-the-ring-and-common-issues"
        self.url_discord = "https://discord.gg/SHm3QrZ"
        self.url_wiki    = "https://aotr.wikia.com/wiki/AOTR_Wiki"
        self.url_forums  = "https://forums.revora.net/forum/2601-age-of-the-ring/"

        #text for the about menu button
        self.about_text_intro = "About Age of the Ring"
        self.about_text_full = "Age of the Ring is a fanmade, not-for-profit game modification. \n The Battle for Middle-earth 2 - Rise of the Witch-king © 2006 Electronic Arts Inc. All Rights Reserved. All “The Lord of the Rings” related content other than content from the New Line Cinema Trilogy of “The Lord of the Rings” films © 2006 The Saul Zaentz Company d/b/a Tolkien Enterprises (”SZC”). All Rights Reserved. All content from “The Lord of the Rings” film trilogy © MMIV New Line Productions Inc. All Rights Reserved. “The Lord of the Rings” and the names of the characters, items, events and places therein are trademarks or registered trademarks of SZC under license. \n\n The launcher was created by Necro#6714, full source code is available at: https://github.com/ClementJ18/aotr_launcher\n\nMod Version: {mod_version}\nLauncher Version: {launcher_version}"

        #handy paths to avoid having to constantly recreate them
        self.path_aotr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aotr")
        self.uninstaller = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #directory where the mod folder is
        self.path_flags = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/flags.txt")

        #name  of the rotwk file we need
        self.file_rotwk = "cahfactions.ini"

        #google drive id of the folder used in the update process, this is where all the updates downloadedfrom
        self.folder_id = '1LgPndLiRyS93Sl9HwNCTOnKh7_Kmop4D'

        #bit of code required for google drive, don't touch
        self.scopes = ['https://www.googleapis.com/auth/drive.metadata.readonly']

        self.launcher_version = "v1b2"
        self.mod_version = 'unknown'

        self.is_gr = False

        #initialize the google drive credentials and store them into memory
        try:
            self._get_service()
        except TransportError:
            self.is_gr = True
            self.files_service = None

        self.init_ui()

    def _get_service(self):
        creds = None
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/token.pickle"), 'rb') as token:
            creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

        service = build('drive', 'v3', credentials=creds)
        self.files_service = service.files()


    def _generate_shadow(self, button):
        #used to generate the standard black shadow for buttons
        shadow = QGraphicsDropShadowEffect(button)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        button.setGraphicsEffect(shadow)

    def enabled(self, value):
        self.menuBar().setEnabled(value)
        self.launch_btn.setEnabled(value)
        self.update_btn.setEnabled(value)
        self.discord_btn.setEnabled(value)
        self.support_btn.setEnabled(value)

        self.progress_bar.in_progress = not value

    def init_ui(self):
        #button that launches the mod
        self.launch_btn = Button("Play", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_play_button.png')), self)
        self.launch_btn.resize(177, 70)
        self.launch_btn.move(162, 111)
        self.launch_btn.clicked.connect(self.launch)
        self._generate_shadow(self.launch_btn)

        #button that updates the mod
        self.update_btn = Button("Update", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher_update_button.png")), self)
        self.update_btn.resize(177, 70)
        self.update_btn.move(162, 207)
        self.update_btn.clicked.connect(self.update)
        self._generate_shadow(self.update_btn)

        #button that opens a webbrowser to invite you to the aotr community server
        self.discord_btn = Button("Discord", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_discord_button.png')), self)
        self.discord_btn.resize(87, 34)
        self.discord_btn.move(207, 303)
        self.discord_btn.clicked.connect(lambda: webbrowser.open_new(self.url_discord))
        self._generate_shadow(self.discord_btn)

        #button that oppens a webbrowser to the moddb page for support help
        self.support_btn = Button("Support", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_support_button.png')), self)
        self.support_btn.resize(87, 34)
        self.support_btn.move(207, 363)
        self.support_btn.clicked.connect(lambda: webbrowser.open_new(self.url_support))
        self._generate_shadow(self.support_btn)
        
        #about box containing disaclaimer, hidden at the start
        self.about_window = QMessageBox()
        self.about_window.setIcon(QMessageBox.Information)
        self.about_window.setText(self.about_text_intro)
        self.about_window.setInformativeText(self.about_text_full)
        self.about_window.setStandardButtons(QMessageBox.Ok)
        self.about_window.setWindowTitle("About")
        self.about_window.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))
        self.about_window.buttonClicked.connect(self.about_window.close)

        #progress bar for update progress, hidden at the start
        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()

        #menu containing the rest of the buttons
        bar = self.menuBar()
        bar.setStyleSheet("QMenuBar {background-color: white;}")
        about_act = bar.addAction('About') # about box
        about_act.triggered.connect(self.about)
        repair_act = bar.addAction('Repair') #basically an update but named repair for users
        repair_act.triggered.connect(self.repair)
        wiki_act = bar.addAction('Wiki') #webbrowser link to the wiki
        wiki_act.triggered.connect(lambda: webbrowser.open_new(self.url_wiki))
        forums_act = bar.addAction('Forums') #webbrowser link to the forums
        forums_act.triggered.connect(lambda: webbrowser.open_new(self.url_forums))
        
        options_menu = bar.addMenu("Options") #submenue for uninstall and launcher flags
        flags_act = options_menu.addAction("Launch Flags") #launcher flags (-win, -scriptdebug2, ect...)
        flags_act.triggered.connect(self.flags_dialog)
        uninstall_act = options_menu.addAction('Uninstall') #uninstall
        uninstall_act.triggered.connect(self.uninstall_dialog)

        self.setFixedSize(500, 500)
        self.setWindowTitle('Age of the Ring')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))

        #background image
        oImage = QImage(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcherBG.jpg"))
        sImage = oImage.scaled(QSize(500, 500)) 
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))
        self.setPalette(palette)

        self.show()

        #look for ROTWK installation
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2ep1.exe")
            self.path_rotwk = winreg.EnumValue(key, 5)[1]
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not locate ROTWK installation. Make sure ROTWK is installed", QMessageBox.Ok, QMessageBox.Ok)

        # check if a new version is available online by comparing to the version of the tree.json, if we can't find a tree.json
        # we assume that a new version is available
        if not self.is_gr:
            if os.path.exists(os.path.join(self.path_aotr, "tree.json")):
                request = self.files_service.list(q=f"'{self.folder_id}' in parents and name = 'tree.json'", pageSize=1000, fields="nextPageToken, files(id, name, webContentLink)").execute()
                r = requests.get(request["files"][0]["webContentLink"])
                
                with open(os.path.join(self.path_aotr, "tree.json"), "r") as f:
                    version = json.load(f)["version"]
                    version_online = json.loads(r.content.decode('utf-8'))["version"]
                    self.mod_version = version

                    if version != version_online:
                        QMessageBox.information(self, "Update Available", "An update is available, click the update button to begin updating.",    QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, "Update Available", "An update is available, click the update button to begin updating.",    QMessageBox.Ok, QMessageBox.Ok)

        #make sure the file where the flags are stored exists.
        Path(self.path_flags).touch(exist_ok=True)

    def flags_dialog(self):
        #allow for users to modify, add or remove flags
        with open(self.path_flags, "r") as f:
            current_flags = f.read()

        new_flags, ok = QInputDialog.getText(self, "Flags","Additional launch flags: ", 
            QLineEdit.Normal, current_flags, flags=Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint) 
            # this removes the ? that appeared in the dialog.
        if ok:
            with open(self.path_flags, "w") as f:
                f.write(new_flags)

    def launch(self):
        #Launch game with the -mod command
        with open(self.path_flags, "r") as f:
            flags = f.read().split(" ")

        #make sure the cah fix file exists in the rotwk game folder
        cah_fix = os.path.join(self.path_rotwk, self.file_rotwk)
        if not os.path.exists(cah_fix):
            to_copy = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/cahfactions.ini")
            shutil.copyfile(to_copy, cah_fix)

        #launch the .exe used to fix the CAH problem, waiting a couple seconds, then launch the mod
        try:
            subprocess.Popen([os.path.join(self.path_aotr, "BFME2X.exe")], cwd=self.path_aotr)
            time.sleep(3)
            subprocess.Popen([os.path.join(self.path_rotwk, "lotrbfme2ep1.exe"), "-mod", f"{self.path_aotr}", *flags], cwd=self.path_aotr)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)

    def update(self):
        #wrapper to handle any errors that may occur while updating the mod
        reply = QMessageBox.information(self, "Confirmation", "Updating is a lenghty process and cannot be stopped after it is started, are you sure you wish to proceed?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            self.enabled(False)
            updated = self.file_fixer("Update")
        except Exception as e:
            self.enabled(True)
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()
        else:
            self.enabled(True)
            self.progress_bar.hide()
            if updated:
                reply = QMessageBox.information(self, "Update Successful", "Age of the Ring updated, would you like to read the changelog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    webbrowser.open(os.path.join(self.path_aotr, "AgeOfTheRing_README.rtf"))
            else:
                QMessageBox.information(self, "No Update", "No new update was available, no files have been modified.", QMessageBox.Ok, QMessageBox.Ok)

    def repair(self):
        #wrapper to handle any errors that may occur while "repairing" the mod
        reply = QMessageBox.information(self, "Confirmation", "Repairing is a lenghty process and cannot be stopped after it is started, are you sure you wish to proceed?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            self.enabled(False)
            self.file_fixer("Repair")
        except Exception as e:
            self.enabled(True)
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()
        else:
            self.enabled(True)
            self.progress_bar.hide()
            QMessageBox.information(self, "Repair Successful", "Age of the Ring has been reset to its original state", QMessageBox.Ok, QMessageBox.Ok)

    def uninstall_dialog(self):
        #wrapper to handle any errors that may occur while uninstalling the mod
        reply = QMessageBox.question(self, 'Uninstall Age of the Ring', "Are you sure you want to uninstall Age of the Ring?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.uninstall()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)

    def uninstall(self):
        #remove mode folder
        shutil.rmtree(self.path_aotr)

        #try to remove cah fix
        try:
            os.remove(os.path.join(self.path_rotwk, self.file_rotwk))
        except FileNotFoundError:
            pass
        
        #create process to remove the remains of the folder 5 seconds after we close the launcher
        folder = '{}'.format(os.path.dirname(os.path.abspath(__file__)))
        subprocess.Popen(['timeout', '5', '&', 'rmdir', '/Q', '/S', folder], shell=True, cwd=self.uninstaller)
        self.close()

    def hash_file(self, path):
        #get the md5 hash of a file for comparison during the update process
        hasher = hashlib.md5()
        with open(path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)

        return hasher.hexdigest()

    def file_fixer(self, string):
        #update method
        if self.files_service is None:
            self._get_service()

        #reset progress bar
        self.progress_bar.setWindowTitle(f'{string} Progress')
        self.progress_bar.change_text("Gathering file data...")
        self.progress_bar.change_percent(0)
        self.progress_bar.show()

        # check if update is possible by making sure that files haven't been uploaded in a while.
        folder = self.files_service.get(fileId=self.folder_id, fields="*").execute()
        modified_by = datetime.datetime.strptime(folder["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fz")
        if modified_by > (datetime.datetime.now() - datetime.timedelta(minutes=30)):
            raise ValueError(f"Cannot currently {string.lower()}, please try again later.")

        #we can only get a thousand files at a time, so we keep going until we have them all.
        request = self.files_service.list(q=f"'{self.folder_id}' in parents", pageSize=1000, fields="nextPageToken, files(id, name, webContentLink)")
        files = []
        counter = 0
        while request is not None:
            QCoreApplication.processEvents()
            result = request.execute()
            counter += 1
            self.progress_bar.change_percent((counter/20)*100)
            files.extend(result.get("files", []))
            request = self.files_service.list_next(request, result)

        #then we make sure that we have the tree.json file and save the new one to the folder
        try:
            tree = next((file for file in files if file['name'] == "tree.json"), None)
            r = requests.get(tree["webContentLink"])
        except TypeError:
            raise TypeError("Did not find tree.json, please report this bug to the discord.")

        with open(os.path.join(self.path_aotr, "tree.json"), "wb") as f:
            f.write(r.content)

        #we check every file by comparing the hash of the local file vs the hash of the file stored in the tree.json
        #we also check if the file exists at all
        self.progress_bar.change_text("Verifying file integrity...")
        tree = json.loads(r.content.decode('utf-8'))
        tree_len = len(tree["files"])
        tree_values = list(tree["files"].values())
        self.mod_version = tree["version"]
        to_download = []
        for file in tree_values:
            QCoreApplication.processEvents()
            self.progress_bar.change_percent((tree_values.index(file)/tree_len)*100)
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
            #if there are now new/changed files we just return
            self.progress_bar.hide()
            return False

        #actually download all the files that have been marked as changed or missing
        self.progress_bar.change_text("Downloading files...")
        for file in to_download:
            QCoreApplication.processEvents()
            self.progress_bar.change_percent((to_download.index(file)/len(to_download))*100)
            r = requests.get(file["link"], headers={"User-Agent": random.choice(user_agent_list)})
            os.makedirs(os.path.dirname(file["path"]), exist_ok=True)
            with open(file["path"], "wb") as f:
                f.write(r.content)

        #any file not in tree.json is removed.
        self.progress_bar.change_text("Cleanup...")
        self.progress_bar.change_percent(0)
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
            self.progress_bar.change_percent((counter%20)/20)

        self.progress_bar.hide()
        return True

    def about(self):
        self.setDisabled(True)
        text = self.about_text_full.format(mod_version=self.mod_version, launcher_version=self.launcher_version)
        self.about_window.setInformativeText(text)
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
