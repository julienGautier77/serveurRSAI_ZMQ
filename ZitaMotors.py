from PyQt6.QtWidgets import QApplication
import os
import qdarkstyle,sys
from MainTrees import MAINMOTOR

if __name__ == '__main__':
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    s = MAINMOTOR(chamber ='zita')
    s.show()
    appli.exec_()