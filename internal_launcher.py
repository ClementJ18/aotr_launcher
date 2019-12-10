from lotrbfme2ep1 import Launcher
import sys
from PyQt5.QtWidgets import QApplication
import os
import logging
import traceback

logging.basicConfig(level=logging.DEBUG, filename= os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_files/launcher.log"), filemode="w")

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        gui = Launcher()
        gui.path_aotr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aotr")

        #remove update
        gui.update_btn.hide()
        menu = gui.menuBar()
        menu.removeAction(gui.repair_act)

        app.exec_()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        sam =  traceback.format_exception(exc_type, exc_value, exc_traceback)
        logging.error(sam)
