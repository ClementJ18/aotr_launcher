from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, 
    QSplitter, QStyleFactory, QApplication, QMessageBox, QLabel, 
    QComboBox, QLineEdit, QPushButton, QCheckBox, QSlider, QLCDNumber,
    QPlainTextEdit, QMenuBar, QMainWindow, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

import os
import sys
import json
import shutil
import hashlib

class Patcher(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        QLabel("Select an directory to flatten:", self).move(25, 30)
        self.directory = QLineEdit(self)
        self.directory.resize(600, 30)
        self.directory.move(25, 55)

        self.pick_directory_btn = QPushButton("...", self)
        self.pick_directory_btn.resize(25, 25)
        self.pick_directory_btn.move(635, 60)
        self.pick_directory_btn.clicked.connect(self.pick_directory)

        QLabel("Select an optional tree.json:", self).move(25, 90)
        self.tree = QLineEdit(self)
        self.tree.resize(600, 30)
        self.tree.move(25, 115)

        self.pick_tree_btn = QPushButton("...", self)
        self.pick_tree_btn.resize(25, 25)
        self.pick_tree_btn.move(635, 120)
        self.pick_tree_btn.clicked.connect(self.pick_tree)

        self.flatten_btn = QPushButton("Flatten", self)
        self.flatten_btn.resize(250, 100)
        self.flatten_btn.move(225, 175)
        self.flatten_btn.clicked.connect(self.flatten)
        self.flatten_btn.setEnabled(False)
        self.flatten_btn.setToolTip("Select an directory to flatten to unlock the button")

        self.setGeometry(0, 0, 700, 300)
        self.setWindowTitle('Patch Maker')
        self.setWindowIcon(QIcon("aotr.ico"))

        self.show()

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
        reply = QMessageBox.warning(self, "Warning", "This will create a a flattened copy of this directory. Are you sure you wish to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            with open(self.tree.text(), "r") as f:
                    old_tree = json.load(f)
        except FileNotFoundError:
            try:
                with open(os.path.join(self.directory.text(), "tree.json"), "r") as f:
                    old_tree = json.load(f)
            except FileNotFoundError:
                old_tree = []

        tree = []
        new_dir = os.path.join(self.directory.text(), '..', 'patch') 
        try:
            os.mkdir(new_dir)
        except FileExistsError as e:
            QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok, QMessageBox.Ok)
            return


        for path, _, files in os.walk(self.directory.text()):
            for name in files:
                file_path = os.path.join(path, name)
                md5 = self.hash_file(file_path)
                try:
                    old_md5 = next((file for file in old_tree if file['name'] == name), None)["hash"]
                except TypeError:
                    old_md5 = ""

                tree.append({"name": name, "path": file_path.replace(f"{self.directory.text()}\\", ''), "hash": md5})
                if md5 != old_md5:
                    try:
                        shutil.copy(os.path.join(path, name), os.path.join(new_dir, name))
                    except shutil.Error:
                        pass

        with open(os.path.join(new_dir, "tree.json"), "w+") as f:
            json.dump(tree, f)

        # for directory in os.listdir(self.directory.text()):
        #     file_path = os.path.join(self.directory.text(), directory)
        #     if os.path.isdir(file_path):
        #         shutil.rmtree(file_path)

        QMessageBox.information(self, "Done", "Finished flattening")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = Patcher()
    sys.exit(app.exec_())