from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QGraphicsDropShadowEffect,
    QAbstractButton, QProgressBar, QInputDialog, QDialog)
from PyQt5.QtCore import Qt, QSize, QCoreApplication, QThread
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush, QColor, QPixmap, QPainter

import gitlab
import base64

import requests
import sys
import webbrowser
import os
import subprocess
import winreg
import hashlib
import json
import logging
import traceback
import shutil
from pathlib import Path
import time

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
        if self.isEnabled():
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(50)
            shadow.setColor(QColor(255, 255, 255, 255))
            shadow.setOffset(0, 0)
            self.setGraphicsEffect(shadow)

    def leaveEvent(self, QEvent):
        #reset to normal shadow
        self.parent().generate_shadow(self)

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

        self.in_progress = False

    def change_text(self, text):
        self.label.setText(text)
        self.label.resize(self.label.sizeHint())

    def change_percent(self, value):
        self.bar.setValue(int(value))

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
            
class DownloadThread(QThread):
    def __init__(self, progress_bar, to_download, project):
        super(QThread, self).__init__(self)
        self.progress_bar = progress_bar
        self.to_download = to_download
        self.project = project
        
    def run(self):
        for file in self.to_download:
            os.makedirs(os.path.dirname(file["path"]), exist_ok=True)

            #casing is annoying, have to remove file before in case the casing of the name changes
            if os.path.exists(file["path"]):
                os.remove(file["path"])

            with open(file["path"], "wb") as file_io:
                f = self.project.files.get(file_path="source/{}".format(file["name"].lower()), ref="master")
                file_io.write(base64.b64decode(f.content))
            self.progress_bar.counter += 1
            self.progress_bar.change_percent((self.progress_bar.counter/len(self.to_download))*100)
        

#main window
class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()

        #links for the menu buttons
        self.url_support   = "https://www.moddb.com/mods/the-horse-lords-a-total-modification-for-bfme/tutorials/installing-age-of-the-ring-and-common-issues"
        self.url_discord   = "https://discord.gg/SHm3QrZ"
        self.url_wiki      = "https://aotr.wikia.com/wiki/AOTR_Wiki"
        self.url_forums    = "https://forums.revora.net/forum/2601-age-of-the-ring/"
        self.url_changelog = "https://docs.google.com/document/d/12XteHeviEyIz8jaGMTyjKVeuJUVmEYUX4jbixkJFzhU/edit"

        #text for the about menu button
        self.about_text_intro = "About Age of the Ring"
        self.about_text_full = "Age of the Ring is a fanmade, not-for-profit game modification. <br> The Battle for Middle-earth 2 - Rise of the Witch-king © 2006 Electronic Arts Inc. All Rights Reserved. All “The Lord of the Rings” related content other than content from the New Line Cinema Trilogy of “The Lord of the Rings” films © 2006 The Saul Zaentz Company d/b/a Tolkien Enterprises (”SZC”). All Rights Reserved. All content from “The Lord of the Rings” film trilogy © MMIV New Line Productions Inc. All Rights Reserved. “The Lord of the Rings” and the names of the characters, items, events and places therein are trademarks or registered trademarks of SZC under license. <br><br> The launcher was created by Eternadarm#0529. You can report bugs or see the source code <a href='https://github.com/ClementJ18/aotr_launcher'>on GitHub</a><br><br>Mod Version: {mod_version}<br>Launcher Version: {launcher_version}"

        #text for the gamerange assistant
        self.gameranger_help_intro = "Follow these instructions to get Gameranger working with the new Age of the Ring launcher"
        self.gameranger_help_full = "<ol><li>Go to Edit > Options and then the Game Tab</li><li>Scroll down to <b>Rise of the Witch-King</b></li><li>Click browse and go to this folder: <b>{path}</b></li><li>Select the file called <b>lotrbfme2ep1.exe</b></li></ol> Once you've completed this you will now be able to play AotR using Gameranger. To switch back simply repeat the procedure but instead select the <b>lotrbfme2ep1.exe</b> file located in <b>{path_rotwk}</b>"

        #handy paths to avoid having to constantly recreate them
        self.path_aotr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aotr")
        self.uninstaller = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #directory where the mod folder is
        self.path_flags = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/flags.txt")

        #name  of the rotwk file we need
        self.file_rotwk = "cahfactions.ini"
        self.launcher_version = "v1"
        self.mod_version = 'unknown'

        self.is_gr = False
        self.is_cah_fix = False

        #initialize the google drive credentials and store them into memory
        try:
            self._get_service()
        except Exception:
            self.is_gr = True
            self.project = None

        self.init_ui()

    def _get_service(self):
        #https://gitlab.com/ClementJ18/aotr
        self.gl = gitlab.Gitlab('https://gitlab.com/')
        self.project = self.gl.projects.get("16769190")

    def generate_shadow(self, button):
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

    def closeEvent(self, evnt):
        if self.progress_bar.in_progress:
            evnt.ignore()
        else:
            super(Launcher, self).closeEvent(evnt)
            
    def init_ui(self):
        #button that launches the mod
        self.launch_btn = Button("Play", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_play_button.png')), self)
        self.launch_btn.resize(177, 70)
        self.launch_btn.move(162, 111)
        self.launch_btn.clicked.connect(self.launch)
        self.generate_shadow(self.launch_btn)

        #button that updates the mod
        self.update_btn = Button("Update", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher_update_button.png")), self)
        self.update_btn.resize(177, 70)
        self.update_btn.move(162, 207)
        self.update_btn.clicked.connect(self.update)
        self.generate_shadow(self.update_btn)

        #button that opens a webbrowser to invite you to the aotr community server
        self.discord_btn = Button("Discord", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_discord_button.png')), self)
        self.discord_btn.resize(87, 34)
        self.discord_btn.move(207, 303)
        self.discord_btn.clicked.connect(lambda: webbrowser.open_new(self.url_discord))
        self.generate_shadow(self.discord_btn)

        #button that oppens a webbrowser to the moddb page for support help
        self.support_btn = Button("Support", QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_files/launcher_support_button.png')), self)
        self.support_btn.resize(87, 34)
        self.support_btn.move(207, 363)
        self.support_btn.clicked.connect(lambda: webbrowser.open_new(self.url_support))
        self.generate_shadow(self.support_btn)
        
        #about box containing disaclaimer, hidden at the start
        self.about_window = QMessageBox()
        self.about_window.setIcon(QMessageBox.Information)
        self.about_window.setTextFormat(Qt.RichText)
        self.about_window.setText(self.about_text_intro)
        self.about_window.setInformativeText(self.about_text_full)
        self.about_window.setStandardButtons(QMessageBox.Ok)
        self.about_window.setWindowTitle("About")
        self.about_window.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))
        self.about_window.buttonClicked.connect(self.about_window.close)

        self.gameranger_help = QMessageBox()
        self.gameranger_help.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.gameranger_help.setIcon(QMessageBox.Information)
        self.gameranger_help.setTextFormat(Qt.RichText)
        self.gameranger_help.setText(self.gameranger_help_intro)
        self.gameranger_help.setInformativeText(self.gameranger_help_full)
        self.gameranger_help.setStandardButtons(QMessageBox.Ok)
        self.gameranger_help.setWindowTitle("About")
        self.gameranger_help.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/aotr.ico")))
        self.gameranger_help.buttonClicked.connect(self.gameranger_help.close)

        #progress bar for update progress, hidden at the start
        self.progress_bar = ProgressBar(self)
        self.progress_bar.hide()

        #menu containing the rest of the buttons
        bar = self.menuBar()
        # bar.setStyleSheet("QMenuBar {background-color: white;}")
        about_act = bar.addAction('About') # about box
        about_act.triggered.connect(self.about)
        self.repair_act = bar.addAction('Repair') #basically an update but named repair for users
        self.repair_act.triggered.connect(self.repair)
        wiki_act = bar.addAction('Wiki') #webbrowser link to the wiki
        wiki_act.triggered.connect(lambda: webbrowser.open_new(self.url_wiki))
        forums_act = bar.addAction('Forums') #webbrowser link to the forums
        forums_act.triggered.connect(lambda: webbrowser.open_new(self.url_forums))
        
        options_menu = bar.addMenu("Options...") #submenue for uninstall and launcher flags
        flags_act = options_menu.addAction("Launch Flags") #launcher flags (-win, -scriptdebug2, ect...)
        flags_act.triggered.connect(self.flags_dialog)
        uninstall_act = options_menu.addAction('Uninstall') #uninstall
        uninstall_act.triggered.connect(self.uninstall_dialog)
        gameranger_act = options_menu.addAction("Gameranger")
        gameranger_act.triggered.connect(self.gameranger)

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
        self.path_rotwk = "GAME NOT FOUND"
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2ep1.exe")
            self.path_rotwk = winreg.EnumValue(key, 5)[1]

            #in case the user has installed a weird version of ROTWK
            if os.path.isfile(self.path_rotwk):
                self.path_rotwk = os.path.dirname(self.path_rotwk)
        except FileNotFoundError:
            QMessageBox.critical(self, "Base Error", "Could not locate ROTWK installation. Make sure ROTWK is installed", QMessageBox.Ok, QMessageBox.Ok)

        #make sure the file where the flags are stored exists.
        Path(self.path_flags).touch(exist_ok=True)

        # check if a new version is available online by comparing to the version of the tree.json, if we can't find a tree.json
        # we assume that a new version is available
        if not self.is_gr:
            if os.path.exists(os.path.join(self.path_aotr, "tree.json")):
                try:
                    file_info = self.project.files.get(file_path="tree.json", ref="master")
                    content = base64.b64decode(file_info.content)
                    version_online = json.loads(content)["version"]
                except IndexError:
                    QMessageBox.critical(self, "Base Error", "Did not find tree.json, you cannot currently update but can still play. Please report this bug to the discord.", QMessageBox.Ok, QMessageBox.Ok)
                    return

                with open(os.path.join(self.path_aotr, "tree.json"), "r") as file:
                    version = json.load(file)["version"]
                    self.mod_version = version

                    if version != version_online:
                        QMessageBox.information(self, "Update Available", "An update is available, click the update button to begin updating.",    QMessageBox.Ok, QMessageBox.Ok)
            else:
                QMessageBox.information(self, "Update Available", "An update is available, click the update button to begin updating.",    QMessageBox.Ok, QMessageBox.Ok)

        try:
            logging.basicConfig(level=logging.DEBUG, filename= os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher.log"), filemode="w")
        except:
            pass

    def flags_dialog(self):
        #allow for users to modify, add or remove flags
        with open(self.path_flags, "r") as file:
            current_flags = file.read()

        new_flags, ok = QInputDialog.getText(
            self, 
            "Flags","Additional launch flags: ", 
            QLineEdit.Normal, 
            current_flags, 
            flags=Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint # this removes the ? that appeared in the dialog.
        ) 
        
        if ok:
            with open(self.path_flags, "w") as file:
                file.write(new_flags)

    def launch(self):
        #Launch game with the -mod command
        with open(self.path_flags, "r") as file:
            flags = file.read().split(" ")

        #make sure the cah fix file exists in the rotwk game folder
        if self.is_cah_fix:
            cah_fix = os.path.join(self.path_rotwk, self.file_rotwk)
            if not os.path.exists(cah_fix):
                to_copy = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/cahfactions.ini")
                shutil.copyfile(to_copy, cah_fix)

        #launch the .exe used to fix the CAH problem, waiting a couple seconds, then launch the mod
        try:
            if self.is_cah_fix:
                subprocess.Popen([os.path.join(self.path_aotr, "BFME2X.exe")], cwd=self.path_aotr)
                time.sleep(3)

            subprocess.Popen([os.path.join(self.path_rotwk, "lotrbfme2ep1.exe"), "-mod", f"{self.path_aotr}", *flags], cwd=self.path_aotr)
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            
        if self.is_cah_fix:
            time.sleep(3)
            os.remove(cah_fix) #clean up

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
            QMessageBox.critical(self, "Update Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()
        else:
            self.enabled(True)
            self.progress_bar.hide()
            if updated:
                reply = QMessageBox.information(self, "Update Successful", "Age of the Ring updated, would you like to read the changelog?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    webbrowser.open(self.url_changelog)
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
            QMessageBox.critical(self, "Repair Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
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
                QMessageBox.critical(self, "Uninstall Error", str(e), QMessageBox.Ok, QMessageBox.Ok)

    def uninstall(self):
        #remove mode folder
        shutil.rmtree(self.path_aotr)

        #try to remove shortcut
        try:
            desktop = os.path.expanduser("~/Desktop")
            path = os.path.join(desktop, 'Age of the Ring Launcher.lnk')
            os.remove(path)
        except FileNotFoundError:
            pass

        #try to remove cah fix
        # try:
        #     os.remove(os.path.join(self.path_rotwk, self.file_rotwk))
        # except FileNotFoundError:
        #     pass
        
        QMessageBox.information(self, "Uninstallation Successful", "AOTR has been succesfully uninstalled, the launcher will exit after you press okay and then delete itself.", QMessageBox.Ok, QMessageBox.Ok)
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
        
    def chunk_list(self, size, l):
        length = len(l)
        chunk_size = (length//size) + 1
        chunks = []
        for x in range(size):
            chunks.append(l[x*chunk_size:(x+1)*chunk_size])
            
        return chunks

    def file_fixer(self, string):
        #update method
        if self.project is None:
            self._get_service()

        #reset progress bar
        self.progress_bar.setWindowTitle(f'{string} Progress')
        self.progress_bar.change_text("Gathering file data...")
        self.progress_bar.change_percent(0)
        self.progress_bar.show()

        # check if update is possible by making sure that files haven't been uploaded in a while.
        no_down = [x for x in self.project.repository_tree() if x["name"] == "nodownload"]
        if no_down:
            raise ValueError(f"Cannot currently {string.lower()} because devs are making changes, please try again later.")
        
        file_info = self.project.files.get(file_path="tree.json", ref="master")
        content = base64.b64decode(file_info.content)
        tree = json.loads(content)
        
        with open(os.path.join(self.path_aotr, "tree.json"), "wb") as file:
            file.write(content)

        #we check every file by comparing the hash of the local file vs the hash of the file stored in the tree.json
        #we also check if the file exists at all
        self.progress_bar.change_text("Verifying file integrity...")
        tree_len = len(tree["files"])
        tree_values = list(tree["files"].values())
        self.mod_version = tree["version"]
        to_download = []
        for file in tree_values:
            QCoreApplication.processEvents()
            self.progress_bar.change_percent((tree_values.index(file)/tree_len)*100)
            full_path = os.path.join(self.path_aotr, file["path"])

            if not os.path.exists(full_path):
                #download new files
                to_download.append({"name": file["path"].replace("\\", "."), "path": full_path})
                logging.debug(f"Downloaded {file['path']}")
            else:
                md5 = self.hash_file(full_path)
                if md5 != file["hash"]:
                    #update existing files
                    to_download.append({"name": file["path"].replace("\\", "."), "path": full_path})
                    logging.debug(f"Downloaded {file['path']}")
                else:
                    logging.debug(f"Did not download file {file['path']}")

        if not to_download:
            #if there are now new/changed files we just return
            self.progress_bar.hide()
            return False

        #actually download all the files that have been marked as changed or missing
        self.progress_bar.change_text("Downloading files...")
        self.progress_bar.counter = 0
        threads = 4
        chunks = self.chunk_list(threads, to_download)
        for chunk in chunks:
            thread = DownloadThread(self.progress_bar, chunk, self.project)
            thread.start()
            thread.join()

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
        text = self.about_text_full.format(mod_version=self.mod_version, launcher_version=self.launcher_version)
        self.about_window.setInformativeText(text)
        self.about_window.show()

    def gameranger(self):
        text = self.gameranger_help_full.format(path=os.path.dirname(os.path.abspath(__file__)), path_rotwk=self.path_rotwk)
        self.gameranger_help.setInformativeText(text)
        self.gameranger_help.show()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        # app.setStyle('Fusion')
        gui = Launcher()
        app.exec_()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sam = traceback.format_exception(exc_type, exc_value, exc_traceback)
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher.log"), "a+") as f:
            f.write(sam)
