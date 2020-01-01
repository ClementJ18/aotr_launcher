from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon

import zipfile
import sys
import winreg
import os
import shutil
import win32com.client
import webbrowser
import traceback
import subprocess

class Installer(QWidget):
    def __init__(self):
        super().__init__()

        self.file_path = "aotr.zip"
        self.rotwk_file_name = "cahfactions.ini"
        self.launcher_name = "launcher.exe"
        self.shortcut_icon = "launcher_files/aotr.ico"
        self.url_changelog = "https://docs.google.com/document/d/12XteHeviEyIz8jaGMTyjKVeuJUVmEYUX4jbixkJFzhU/edit"

        self.init_ui()

    def init_ui(self):
        QLabel("Select an installation directory:", self).move(25, 25)
        self.directory = QLineEdit(self)
        self.directory.move(25, 55)
        self.directory.resize(600, 30)
        self.directory.setText("C:/Program Files/Age of the Ring")

        self.pick_directory_btn = QPushButton("...", self)
        self.pick_directory_btn.resize(25, 25)
        self.pick_directory_btn.move(635, 60)
        self.pick_directory_btn.clicked.connect(self.pick_directory)

        self.install_btn = QPushButton("Install", self)
        self.install_btn.resize(250, 100)
        self.install_btn.move(225, 100)
        self.install_btn.clicked.connect(self.installer)
        self.install_btn.setToolTip("Select an installation directory to unlock the button")

        self.progress_bar = QProgressBar(self)
        self.progress_bar.move(50, 150)
        self.progress_bar.resize(600, 25)
        self.progress_bar.hide()

        self.setFixedSize(700, 250)
        self.setWindowTitle('Age of the Ring Installer')

        self.show()

        try:
            # reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            # key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2.exe")
            # self.path_bfme2 = winreg.EnumValue(key, 5)[1]

            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\lotrbfme2ep1.exe")
            self.path_rotwk = winreg.EnumValue(key, 5)[1]
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Could not detect Rise of the Witch King. Please make sure you have it installed", QMessageBox.Ok, QMessageBox.Ok)
            self.close()            

    def pick_directory(self):
        text = str(QFileDialog.getExistingDirectory(self, f"Select installation directory"))
        if text != "":
            if text == self.path_rotwk.replace("\\", "/"):
                QMessageBox.critical(self, "Error", "The mod must NOT be installed in your game folder, please select another installation folder.", QMessageBox.Ok, QMessageBox.Ok)
                return

            self.directory.setText(f"{text}/Age of the Ring")

    def installer(self):
        #2. Extract a single file in the ROTWK folder
        #3. Extract the rest of the files into the AOTR folder
        #4. Generate shortcut???
        if not os.path.isfile(f'{self.path_rotwk}\\##########202_v8.0.0.big'):
            reply = QMessageBox.warning(self, "ROTWK Version", "The installer has detected you do not have 2.02 activated, it is recommended to have 2.02 enabled when installing the mod. Note that ROTWK needs to be set to 2.02 in order to play the mod. The installation will proceed but you will be unable to properly play the mod until you switch to 2.02", QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

            if reply == QMessageBox.Cancel:
                return

        try:
            self.install_btn.hide()
            self.progress_bar.show()
            self.directory.setEnabled(False)
            self.pick_directory_btn.setEnabled(False)
            self.installation()
        except Exception as e:
            QMessageBox.critical(self, "Status", f"Failed to to install: {e}", QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()    
            self.install_btn.show()
            self.directory.setEnabled(True)
            self.pick_directory_btn.setEnabled(True)
        else:
            reply = QMessageBox.information(self, "Status", "Successfully installed, enjoy the mod. Would you like to open the launcher?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) 
            webbrowser.open(self.url_changelog)

            if reply == QMessageBox.Yes:
                subprocess.Popen([os.path.join(self.directory.text(), self.launcher_name)])
            
            self.close()

    def installation(self):
        os.makedirs(self.directory.text())
        zf = zipfile.ZipFile(self.file_path)
        uncompress_size = sum((file.file_size for file in zf.infolist()))
        extracted_size = 0
        try:
            for file in zf.infolist():
                QCoreApplication.processEvents()
                extracted_size += file.file_size
                self.progress_bar.setValue(extracted_size * 100/uncompress_size)
                zf.extract(file, self.directory.text())

            shutil.copyfile(self.rotwk_file_name, f"{self.path_rotwk}\\{self.rotwk_file_name}")
        except Exception:
            shutil.rmtree(self.directory.text())
            raise

        try:
            desktop = os.path.expanduser("~/Desktop")
            path = os.path.join(desktop, 'Age of the Ring Launcher.lnk')
            target = f"{self.directory.text()}\\{self.launcher_name}"

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.IconLocation = os.path.join(self.directory.text(), self.shortcut_icon)
            shortcut.WindowStyle = 7 # 7 - Minimized, 3 - Maximized, 1 - Normal
            shortcut.WorkingDirectory = self.directory.text()
            shortcut.save()

            #run as admin
            with open(path, "rb") as file:
                ba = bytearray(file.read())

            ba[0x15] = ba[0x15] | 0x20

            with open(path, "wb") as file:
                file.write(ba)

        except Exception:
            raise        

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        gui = Installer()
        app.exec_()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sam =  traceback.format_exception(exc_type, exc_value, exc_traceback)
        with open("error.log", "w") as f:
            f.write(sam)
