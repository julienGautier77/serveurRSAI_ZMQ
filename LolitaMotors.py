from PyQt6.QtWidgets import QApplication
import os
import qdarkstyle,sys
from MainTrees import MAINMOTOR

if __name__ == '__main__':
    appli = QApplication(sys.argv)
    
    s = MAINMOTOR(chamber ='lolita')
    s.show()
    appli.exec_()