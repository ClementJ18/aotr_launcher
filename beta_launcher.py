from lotrbfme2ep1 import Launcher
import sys
from PyQt5.QtWidgets import QApplication
import os
import logging
import traceback

logging.basicConfig(level=logging.DEBUG, filename= os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher.log"), filemode="w")

def password_check(launcher):
    password_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/password.txt")
    with open(password_file, "r") as f:
        password = f.read()

    request = launcher.files_service.list(q=f"'{launcher.folder_id}' in parents and name = 'password.txt'", pageSize=1000, fields="nextPageToken, files(id, name, webContentLink)").execute()
    r = requests.get(request["files"][0]["webContentLink"])

    password_online = json.loads(r.content.decode('utf-8'))["version"]

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        gui = Launcher()
        gui.folder_id = "new_id"
        app.exec_()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sam =  traceback.format_exception(exc_type, exc_value, exc_traceback)
        logging.error(sam)
