from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QTextCursor

import os
import sys
import json
import shutil
import hashlib

class FlattenLog(QMainWindow):
    def __init__(self, parent=None):
        super(FlattenLog, self).__init__(parent)
        self.debug = False
        self.init_ui()

    def init_ui(self):
        self.b = QPlainTextEdit(self)
        self.b.setReadOnly(True)
        self.b.move(50, 50)
        self.b.resize(400, 400)   

        self.setFixedSize(500, 500)
        self.setWindowTitle('Flatten Log')

    def write(self, text):
        if self.debug:
            self.b.insertPlainText(text)
            self.b.moveCursor(QTextCursor.End)

class Patcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.help_text_full = """The Patch Maker contains three major areas, the patch directory selection, the tree.json selection and the flatten button. Once you've filled out everything and you click the "Flatten" button the patch maker will create a "patch" folder next to the folder you've selected and using the tree.json you have provided will find all the files that have been modified since the last patch and copy them to that folder. The tree.json selection is optional but very useful, it will compare the files with the tree.json file you provide to figure out which files have been changed since the last patch so that you only have to upload the change files instead of the entire directory all over again. If you do not have a tree.json do not worry, the patch maker is perfectly capable of generating one on its own, just leave the area blank and the patch maker will generate a new tree.json. Steps to use the patch maker:<ol><li>Select the AOTR directory containing all the files for the next update.</li><li>Optionally, select the tree.json that was generated during the making of the previous patch.</li><li>Click flatten.<ul><li>If you have selected a valid tree.json then the patch maker will move over all the files that have been edited since the time that the selected tree.json was created</li><li>If you have not selected a tree.json, the patch maker will copy over everyfile that in the selected directory.</ul></ol>"""
        self.init_ui()

    def init_ui(self):
        label = QLabel("Select an directory to flatten:", self)
        label.move(25, 55)
        label.adjustSize()

        self.directory = QLineEdit(self)
        self.directory.resize(600, 30)
        self.directory.move(25, 80)

        self.pick_directory_btn = QPushButton("...", self)
        self.pick_directory_btn.resize(25, 25)
        self.pick_directory_btn.move(635, 85)
        self.pick_directory_btn.clicked.connect(self.pick_directory)

        label = QLabel("Select an optional tree.json:", self)
        label.move(25, 115)
        label.adjustSize()

        self.tree = QLineEdit(self)
        self.tree.resize(600, 30)
        self.tree.move(25, 140)

        self.pick_tree_btn = QPushButton("...", self)
        self.pick_tree_btn.resize(25, 25)
        self.pick_tree_btn.move(635, 145)
        self.pick_tree_btn.clicked.connect(self.pick_tree)

        self.flatten_btn = QPushButton("Flatten", self)
        self.flatten_btn.resize(250, 100)
        self.flatten_btn.move(225, 200)
        self.flatten_btn.clicked.connect(self.flatten_handler)
        self.flatten_btn.setEnabled(False)
        self.flatten_btn.setToolTip("Select an directory to flatten to unlock the button")

        self.about_window = QMessageBox()
        self.about_window.setIcon(QMessageBox.Information)
        self.about_window.setText("About the AOTR Patch Maker")
        self.about_window.setInformativeText("The Patch Maker is a tool which \"flattens\" the Age of the Ring directory and prepares it for upload so that the launcher can work out which files to download more easily.")
        self.about_window.setStandardButtons(QMessageBox.Ok)
        self.about_window.setWindowTitle("About")
        self.about_window.buttonClicked.connect(self.about_window.close)

        self.help_window = QMessageBox()
        self.help_window.setIcon(QMessageBox.Information)
        self.help_window.setText("How to use the Patch Maker")
        self.help_window.setInformativeText(self.help_text_full)
        self.help_window.setStandardButtons(QMessageBox.Ok)
        self.help_window.setWindowTitle("About")
        self.help_window.buttonClicked.connect(self.help_window.close)

        self.debug = QCheckBox("Debug?", self)
        self.debug.move(80, 230)

        bar = self.menuBar()
        bar.setStyleSheet("QMenuBar {background-color: white;}")
        about_act = bar.addAction('About')
        about_act.triggered.connect(self.about_window.show)
        help_act = bar.addAction('Help')
        help_act.triggered.connect(self.help_window.show)

        self.log = FlattenLog(self)

        self.setFixedSize(700, 350)
        self.setWindowTitle('Patch Maker')

        self.show()

    def flatten_handler(self):
        try:
            self.flatten_btn.setEnabled(False)
            self.log.debug = self.debug.isChecked()
            reply = QMessageBox.warning(self, "Warning", "This will create a a flattened copy of this directory. Are you sure you wish to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.No:
                return
            
            if self.debug.isChecked():
                self.log.b.clear()
                self.log.show()
        
            self.flatten()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
        else:
            self.flatten_btn.setEnabled(True)
            QMessageBox.information(self, "Done", "Finished flattening")

    def pick_directory(self):
        text = str(QFileDialog.getExistingDirectory(self, f"Select flatten directory"))
        if text != "":
            self.directory.setText(text)
            self.flatten_btn.setEnabled(True)  

    def pick_tree(self):
        text = str(QFileDialog.getOpenFileName(self, f"Select tree file")[0])
        self.tree.setText(text)

    def hash_file(self, path):
        hasher = hashlib.md5()
        with open(path, 'rb') as afile:
            buf = afile.read()
            hasher.update(buf)

        return hasher.hexdigest()

    def flatten(self):
        QCoreApplication.processEvents()
        try:
            with open(self.tree.text(), "r") as f:
                old_tree = json.load(f)
        except FileNotFoundError:
            self.log.write("tree.json not specified, generating blank one\n")
            old_tree = []

        tree = {}
        new_dir = os.path.join(self.directory.text(), '..', 'release') 
        try:
            self.log.write("Creating release directory one level up\n")
            os.mkdir(new_dir)
        except FileExistsError as e:
            QMessageBox.critical(self, " Dir Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            return

        for path, _, files in os.walk(self.directory.text()):
            for name in files:
                QCoreApplication.processEvents()
                if name in ["desktop.ini"]:
                    continue

                file_path = os.path.join(path, name)
                subdir_path = file_path.replace(f"{self.directory.text()}\\", '')
                md5 = self.hash_file(file_path)
                try:
                    old_md5 = old_tree[subdir_path]["hash"]
                except KeyError:
                    old_md5 = ""

                tree[subdir_path] = {"name": name, "path": subdir_path, "hash": md5}
                self.log.write(f"{file_path}: Old '{old_md5}' vs '{md5}' New\n")
                if md5 != old_md5:
                    try:
                        new_path = os.path.join(new_dir, subdir_path.replace("\\", "."))
                        shutil.copy(file_path, new_path)
                        self.log.write(f"Successfully moved {file_path} to {new_path}\n")
                    except shutil.Error:
                        QMessageBox.critical(self, "shutil Error", f"{str(e)}\n{name}")

        with open(os.path.join(new_dir, "tree.json"), "w+") as f:
            json.dump(tree, f)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = Patcher()
    sys.exit(app.exec_())
