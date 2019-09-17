from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

import zipfile
import sys
import winreg
import os
import shutil
import win32com.client

class Installer(QWidget):
    def __init__(self):
        super().__init__()

        self.file_path = "aotr.zip"
        self.rotwk_file_name = "cahfactions.ini"
        self.launcher_name = "launcher.exe"
        self.shortcut_icon = "launcher_assets/aotr.ico"

        self.init_ui()

    def init_ui(self):
        QLabel("Select an installation directory:", self).move(25, 25)
        self.directory = QLineEdit(self)
        self.directory.move(25, 55)
        self.directory.resize(600, 30)

        self.pick_directory_btn = QPushButton("...", self)
        self.pick_directory_btn.resize(25, 25)
        self.pick_directory_btn.move(635, 60)
        self.pick_directory_btn.clicked.connect(self.pick_directory)

        self.install_btn = QPushButton("Install", self)
        self.install_btn.resize(250, 100)
        self.install_btn.move(225, 100)
        self.install_btn.clicked.connect(self.installer)
        self.install_btn.setEnabled(False)
        self.install_btn.setToolTip("Select an installation directory to unlock the button")

        self.progress_bar = QProgressBar(self)
        self.progress_bar.move(50, 150)
        self.progress_bar.resize(600, 25)
        self.progress_bar.hide()


        self.setGeometry(0, 0, 700, 250)
        self.setWindowTitle('Age of the Ring Installer')
        self.setWindowIcon(QIcon("aotr.ico"))

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

        #test_data
        # self.path_bfme2 = "C:\\Users\\Admin\\Documents\\rotwk"
        # self.path_rotwk = "C:\\Users\\Admin\\Documents\\rotwk"
            

    def pick_directory(self):
        text = str(QFileDialog.getExistingDirectory(self, f"Select installation directory"))
        if text != "":
            if text == self.path_rotwk:
                QMessageBox.critical(self, "Error", "The mod must NOT be installed in your game folder, please select another installation folder.", QMessageBox.Ok, QMessageBox.Ok)
                return

            self.directory.setText(f"{text}/aotr")
            self.install_btn.setEnabled(True)       

    def patch_check(self):
        #check that we are on BFME2 1.06
        # if os.path.isfile(f'{self.path_bfme2}\\some_file.big'):
        #     QMessageBox.warning(self, "BFME2 Version", "The installer has detected that you have 1.09 activated. Note that BFME2 must be set to 1.06 in order to play this mod.", QMessageBox.Ok, QMessageBox.Ok)

        #check that we are on ROTWK 2.02 version whatever is currently the supported version(v8 rn)
        if not os.path.isfile(f'{self.path_rotwk}\\##########202_v8.0.0.big'):
            QMessageBox.warning(self, "ROTWK Version", "The installer has detected you do not have 2.02 activated. Note that ROTWK needs to be set to 2.02 in order to play the mod. The installation will proceed but you will be unable to properly play the mod until you switch to 2.02", QMessageBox.Ok, QMessageBox.Ok)

    def installer(self):
        #2. Extract a single file in the ROTWK folder
        #3. Extract the rest of the files into the AOTR folder
        #4. Generate shortcut???
        self.install_btn.hide()
        self.progress_bar.show()
        self.patch_check()

        try:
            self.installation()
        except Exception as e:
            QMessageBox.critical(self, "Status", f"Failed to to install: {e}", QMessageBox.Ok, QMessageBox.Ok)
            self.progress_bar.hide()    
            self.install_btn.show()
        else:
            QMessageBox.information(self, "Status", "Successfully installed, enjoy the mod.", QMessageBox.Ok, QMessageBox.Ok) 
            self.close()         

    def installation(self):
        zf = zipfile.ZipFile(self.file_path)
        uncompress_size = sum((file.file_size for file in zf.infolist()))
        extracted_size = 0
        try:
            for file in zf.infolist():
                extracted_size += file.file_size
                self.progress_bar.setValue(extracted_size * 100/uncompress_size)
                zf.extract(file, self.directory.text())

            shutil.copyfile(self.rotwk_file_name, f"{self.path_rotwk}\\{self.rotwk_file_name}")
        except Exception as e:
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
        except Exception as e:
            raise        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = Installer()
    sys.exit(app.exec_())
