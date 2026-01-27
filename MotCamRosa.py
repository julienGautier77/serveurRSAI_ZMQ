#! /home/sallejaune/loaenv/bin/python3.12
# -*- coding: utf-8 -*-
from threeMotorGuiFB import THREEMOTORGUI
from oneMotorGuiServerRSAI import ONEMOTORGUI
from PyQt6.QtWidgets import QApplication
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget,QPushButton,QLineEdit,QToolButton,QVBoxLayout,QHBoxLayout,QLabel,QDoubleSpinBox
from PyQt6.QtCore import pyqtSlot
import sys
import pathlib,os,time
import qdarkstyle


class MotCamRosa(QWidget):

    def __init__(self):
        super(MotCamRosa, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.icon = str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setWindowTitle('Rosa Focal Spot Camera')

        self.mot = THREEMOTORGUI(IPLat="10.0.1.31", NoMotorLat=8, IPVert="10.0.1.31", NoMotorVert=12, IPFoc="10.0.1.31", NoMotorFoc=10,nomWin='Camera Tache Focale',nomTilt='Focal Spot',nomFoc='Cam Foc')
        self.mot.startThread2()
        self.motFS = ONEMOTORGUI(IpAdress="10.0.1.31", NoMotor = 5, showRef=False, unit=1,jogValue=100)
        self.thread = PositionThread(self,mot=self.motFS.MOT[0]) # thread for displaying position
        self.thread.POS.connect(self.Position)
        self.thread.ThreadINIT()
        self.thread.start()
        self.ref0 = self.motFS.refValueStep[0]
        self.ref1 = self.motFS.refValueStep[1]

        self.setup()

    def setup(self):   

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.mot)
        self.butRef0 = QPushButton('In')
        self.butRef0.clicked.connect(self.Ref0Move)
        self.butRef1 = QPushButton('Out')
        self.butRef1.clicked.connect(self.Ref1Move)
        label= QLabel('Miroir Focal Spot')
        self.positionFS=QDoubleSpinBox()
        self.positionFS.setMaximum(500000000)
        self.positionFS.setMinimum(-500000000)
        hbox0 = QHBoxLayout()
        hbox0.addWidget(label)
        hbox0.addWidget(self.positionFS)
        self.positionFS.setSuffix('um')
        vbox1.addLayout(hbox0)
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.butRef0)
        hbox1.addWidget(self.butRef1)
        vbox1.addLayout(hbox1)
        self.setLayout(vbox1)

    def Ref0Move(self):
        self.motFS.MOT[0].move(self.ref0) 
    
    def Ref1Move(self):
        self.motFS.MOT[0].move(self.ref1)#/ float((self.motFS.stepmotor[0])))   

    @pyqtSlot(object)
    def Position(self,Posi):
        ''' 
        Position  display read from the second thread
        '''
        self.Posi = Posi
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)* float((self.motFS.stepmotor[0]))
        self.positionFS.setValue((round(a,2))) 
        if self.ref0 - 100 < Pos < self.ref0 + 100 :
            self.butRef0.setStyleSheet("background-color:red")
        else : self.butRef0.setStyleSheet("background-color:gray ")

        if self.ref1 - 100 < Pos < self.ref1 + 100 :
            self.butRef1.setStyleSheet("background-color:green")
        else : self.butRef1.setStyleSheet("background-color:gray ")


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    import time 
    POS = QtCore.pyqtSignal(object) # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self,parent=None,mot='',):
        super(PositionThread,self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False
        self.positionSleep = 0.5
        self.etat_old = ""
        self.Posi_old = 0

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                
                Posi = (self.MOT.position())
                time.sleep(self.positionSleep)
                etat = self.MOT.etatMotor()
                try :
                    if self.Posi_old != Posi or self.etat_old != etat: # on emet que si different
                        self.POS.emit([Posi,etat])
                        self.Posi_old = Posi
                        self.etat_old = etat
                    
                except Exception as e :
                    print('error emit',e)
                  
    def ThreadINIT(self):
        self.stop = False   
                        
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        #self.terminate()


if __name__ =='__main__':
   
    appli = QApplication(sys.argv)
    e = MotCamRosa()
    e.show()
    appli.exec_()