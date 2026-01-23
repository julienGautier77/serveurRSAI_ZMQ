#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface Graphique pour le pilotage de deux moteurs tilt
Controleurs possible : A2V RSAI NewFocus SmartAct ,newport, Polulu
Thread secondaire pour afficher les positions
import files : moteurRSAI.py smartactmot.py moteurNewFocus.py  moteurA2V.py newportMotors.py servo.py
memorisation de 5 positions
python 3.X PyQt6
System 64 bit (at least python MSC v.1900 32 bit (Intel)) 
@author: Gautier julien loa
Created on Tue Jan 4 10:42:10 2018
Modified on 2026/01/08
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from PyQt6.QtWidgets import QComboBox, QLabel, QToolButton, QCheckBox
from PyQt6.QtCore import pyqtSlot
import qdarkstyle
import pathlib
import time
import sys
import os
import zmq_client_RSAI

PY = sys.version_info[0]
if PY<3:
    print('wrong version of python : Python 3.X must be used')

import __init__

__version__=__init__.__version__
__author__ = __init__. __author__ 



class TILTMOTORGUI(QWidget) :
    """
    User interface Motor class : 
    MOTOGUI(str(mot1), str(motorTypeName),str(mot2), str(motorTypeName), nomWin,nomTilt,unit )
    mot0= lat  'name of the motor ' (child group of the ini file)
    mot1 =vert
    motorTypeName= Controler name  : 'RSAI' or 'A2V' or 'NewFocus' or 'SmartAct' or 'Newport' , Servo,Arduino
    nonWin= windows name
    nonTilt =windows tilt name
    unit=0 step 1 micron 2 mm 3 ps 

    fichier de config des moteurs : 'configMoteurRSAI.ini' 'configMoteurA2V.ini' 'configMoteurNewFocus.ini' 'configMoteurSmartAct.ini'
    """
  
    def __init__(self, IPLat,NoMotorLat,IPVert,NoMotorVert,nomWin='',nomTilt='',unit=1,jogValue=100,background='',parent=None,showUnit=False, invLat=False, invVert=False):
        
        super(TILTMOTORGUI, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep

        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.showUnit = showUnit
        
        self.iconFlecheHaut = self.icon + "flechehaut.png"
        self.iconFlecheHaut = pathlib.Path(self.iconFlecheHaut)
        self.iconFlecheHaut = pathlib.PurePosixPath(self.iconFlecheHaut)
        self.iconFlecheBas = self.icon + "flechebas.png"
        self.iconFlecheBas = pathlib.Path(self.iconFlecheBas)
        self.iconFlecheBas = pathlib.PurePosixPath(self.iconFlecheBas)
        self.iconFlecheDroite = self.icon + "flechedroite.png"
        self.iconFlecheDroite = pathlib.Path(self.iconFlecheDroite)
        self.iconFlecheDroite = pathlib.PurePosixPath(self.iconFlecheDroite)
        self.iconFlecheGauche = self.icon + "flechegauche.png"
        self.iconFlecheGauche = pathlib.Path(self.iconFlecheGauche)
        self.iconFlecheGauche = pathlib.PurePosixPath(self.iconFlecheGauche)
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.indexUnit = unit
        self.jogValue = jogValue
        self.nomTilt = nomTilt
        if background != "":
            self.setStyleSheet("background-color:"+background)
        
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.version = __version__
        self.inv = [invLat, invVert]  # Inversion des axes 
        self.MOT = [0, 0]
        self.MOT[0] = zmq_client_RSAI.MOTORRSAI(IPLat, NoMotorLat)
        self.MOT[1] = zmq_client_RSAI.MOTORRSAI(IPVert, NoMotorVert)
        self.stepmotor = [0, 0]
        self.butePos = [0, 0]
        self.buteNeg = [0, 0]
        self.name = [0, 0]
        
        for zzi in range(0, 2):
            self.stepmotor[zzi] = float((self.MOT[zzi].getStepValue()))  # list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[zzi].getButLogPlusValue())  # list 
            self.buteNeg[zzi] = float(self.MOT[zzi].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[0].getName())
        
        self.unitChangeLat = self.indexUnit
        self.unitChangeVert = self.indexUnit
        self.setWindowTitle(nomWin+' : '+ str(IPLat) + ' [M' + str(NoMotorLat) + ']  ' + str(IPVert) + ' [M' + str(NoMotorVert) + ']  ')
        self.threadLat = PositionThread(mot=self.MOT[0])  # thread pour afficher position Lat
        self.threadLat.POS.connect(self.PositionLat)
        time.sleep(0.12)
        
        self.threadVert = PositionThread(mot=self.MOT[1])  # thread pour afficher position Vert
        self.threadVert.POS.connect(self.PositionVert)
        
        self.setup()
        
        if self.indexUnit == 0:  #  step
            self.unitChangeLat = 1
            self.unitName = 'step'
        if self.indexUnit == 1:  # micron
            self.unitChangeLat = float(( self.stepmotor[0])) 
            self.unitName = 'um'
        if self.indexUnit == 2:  # mm 
            self.unitChangeLat = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        if self.indexUnit == 3:  # ps  double passage : 1 microns=6fs
            self.unitChangeLat = float( self.stepmotor[0]*0.0066666666) 
            self.unitName = 'ps'
        if self.indexUnit == 4:  # en degres
            self.unitChangeLat = self.stepmotor[0]
            self.unitName = '°'
        self.unitTrans()
        self.jogStep.setValue(self.jogValue)
        self.actionButton()

    def setup(self):

        vbox1 = QVBoxLayout()
        hbox1 = QHBoxLayout()
        hboxTitre = QHBoxLayout()
        self.nomTilt = QLabel(self.nomTilt)
        self.nomTilt.setStyleSheet("font: bold 20pt;color:yellow")
        hboxTitre.addWidget(self.nomTilt)
        if self.showUnit is True:
            self.unitTransBouton = QComboBox()
            self.unitTransBouton.setMaximumWidth(100)
            self.unitTransBouton.setMinimumWidth(100)
            self.unitTransBouton.setStyleSheet("font: bold 12pt")
            self.unitTransBouton.addItem('Step')
            self.unitTransBouton.addItem('um')
            self.unitTransBouton.addItem('mm')
            self.unitTransBouton.addItem('ps')
            self.unitTransBouton.setCurrentIndex(self.indexUnit)
            hboxTitre.addWidget(self.unitTransBouton)
            hboxTitre.addStretch(1)
        else:
            pass
        self.butNegButt = QCheckBox('Log FDC-', self)
        hboxTitre.addWidget(self.butNegButt)

        self.butPosButt = QCheckBox('Log FDC+', self)
        hboxTitre.addWidget(self.butPosButt)
        vbox1.addLayout(hboxTitre)
        
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(0)
        grid_layout.setHorizontalSpacing(10)
        self.haut = QToolButton()
        self.haut.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconFlecheHaut,self.iconFlecheHaut))
        self.haut.setMaximumHeight(70)
        self.haut.setMinimumWidth(70)
        self.haut.setMaximumWidth(70)
        self.haut.setMinimumHeight(70)
        
        self.bas = QToolButton()
        self.bas.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconFlecheBas,self.iconFlecheBas))
        self.bas.setMaximumHeight(70)
        self.bas.setMinimumWidth(70)
        self.bas.setMaximumWidth(70)
        self.bas.setMinimumHeight(70)
        
        self.droite = QToolButton()
        self.droite.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconFlecheDroite,self.iconFlecheDroite))
        self.droite.setMaximumHeight(70)
        self.droite.setMinimumWidth(70)
        self.droite.setMaximumWidth(70)
        self.droite.setMinimumHeight(70)
        
        self.gauche = QToolButton()
        self.gauche.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconFlecheGauche,self.iconFlecheGauche))
        
        self.gauche.setMaximumHeight(70)
        self.gauche.setMinimumWidth(70)
        self.gauche.setMaximumWidth(70)
        self.gauche.setMinimumHeight(70)
        
        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(1000000)
        self.jogStep.setStyleSheet("font: bold 12pt")
        self.jogStep.setValue(self.jogValue)
        self.jogStep.setMaximumWidth(120)
        
        center = QHBoxLayout()
        center.addWidget(self.jogStep)
        self.hautLayout = QHBoxLayout()
        self.hautLayout.addWidget(self.haut)
        self.basLayout = QHBoxLayout()
        self.basLayout.addWidget(self.bas)
        grid_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        grid_layout.addLayout(self.hautLayout, 0, 1)
        grid_layout.addLayout(self.basLayout, 2, 1)
        grid_layout.addWidget(self.gauche, 1, 0)
        grid_layout.addWidget(self.droite, 1, 2)
        grid_layout.addLayout(center, 1, 1)
        
        hbox1.addLayout(grid_layout)
        
        vbox1.addLayout(hbox1)
        
        posLAT = QLabel('Lateral :')
        posLAT.setMaximumHeight(20)
        posVERT = QLabel('Vertical :')
        posVERT.setMaximumHeight(20)

        hbox2a = QHBoxLayout()
        hbox2a.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        hbox2a.addWidget(posLAT)
        hbox2b = QHBoxLayout()
        hbox2b.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        hbox2b.addWidget(posVERT)
        hbox2c = QHBoxLayout()
        hbox2c.addLayout(hbox2a)
        hbox2c.addLayout(hbox2b)
        vbox1.addLayout(hbox2c)
        
        self.position_Lat = QLabel('pos')
        self.position_Lat.setMaximumHeight(20)
        self.position_Vert = QLabel('pos')
        self.position_Vert.setMaximumHeight(20)
        hbox3a = QHBoxLayout()
        hbox3a.addWidget(self.position_Lat)
        hbox3a.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        hbox3b = QHBoxLayout()
        hbox3b.addWidget(self.position_Vert)
        hbox3b.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        hbox3c = QHBoxLayout()
        hbox3c.addLayout(hbox3a)
        hbox3c.addLayout(hbox3b)
        vbox1.addLayout(hbox3c)
        
        hbox4 = QHBoxLayout()
        self.zeroButtonLat = QPushButton('Zero Lat')
        self.zeroButtonVert = QPushButton('Zero Vert')
        
        hbox4.addWidget(self.zeroButtonLat)
        hbox4.addWidget(self.zeroButtonVert)
        vbox1.addLayout(hbox4)
        
        self.stopButton = QPushButton('STOP')
        self.stopButton.setStyleSheet("background-color: red")
        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.stopButton)
        vbox1.addLayout(hbox5)
        self.setLayout(vbox1)       
        
    def startThread2(self):
        self.threadLat.ThreadINIT()
        self.threadLat.start()
        time.sleep(0.5)
        self.threadVert.ThreadINIT()
        self.threadVert.start()
        
    def actionButton(self):
        '''
           Definition des boutons 
        '''
        if self.showUnit is True:
            self.unitTransBouton.currentIndexChanged.connect(self.unitTrans)  # Trans unit change
        
        self.haut.clicked.connect(self.hMove) # jog haut
        self.haut.setAutoRepeat(False)
        self.bas.clicked.connect(self.bMove) # jog bas
        self.bas.setAutoRepeat(False)
        self.gauche.clicked.connect(self.gMove)
        self.gauche.setAutoRepeat(False)
        self.droite.clicked.connect(self.dMove)
        self.droite.setAutoRepeat(False)
                
        self.zeroButtonLat.clicked.connect(self.ZeroLat) # remet a zero l'affichage
        self.zeroButtonVert.clicked.connect(self.ZeroVert)
        
        #self.refZeroButton.clicked.connect(self.RefMark) # va en butée et fait un zero

        self.stopButton.clicked.connect(self.StopMot) # arret moteur
    
    def gMove(self):
        '''
        action bouton left -
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChangeLat) # en step 
        b = self.MOT[0].position()
        if self.inv[0] is False:
            if b - a < self.buteNeg[0]:
                print("STOP : Butée Negative")
                self.MOT[0].stopMotor()
            else: 
                self.MOT[0].rmove(-a) 
        else:  # inv true on fait +
            if b + a > self.butePos[0]:
                print("STOP : Butée Pos")
                self.MOT[0].stopMotor()
            else:
                self.MOT[0].rmove(a)
            
    def dMove(self):
        '''
        action bouton right +
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChangeLat)
        b = self.MOT[0].position()
        if self.inv[0] is False:
            if b + a > self.butePos[0]:
                print("STOP : Butée Positive")
                self.MOT[0].stopMotor()
            else: 
                self.MOT[0].rmove(+a) 
        else: # on fait du moins 
            if b - a < self.buteNeg[0]:
                print("STOP : Butée Negative")
                self.MOT[0].stopMotor()
            else:
                self.MOT[0].rmove(-a)
        
    def hMove(self):
        '''
        action bouton up + 
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChangeVert)
        b = self.MOT[1].position()
        if self.inv[1] is False: # +
            if b + a > self.butePos[1]:
                print("STOP : Butée Positive")
                self.MOT[1].stopMotor()
            else:
                self.MOT[1].rmove(a)
        else: # - 
            if b - a < self.buteNeg[1]:
                print("STOP : Butée Negative")
                self.MOT[1].stopMotor()
            else: 
                self.MOT[1].rmove(-a)
        
    def bMove(self):
        '''
        action bouton down 
        '''
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeVert)
        b = self.MOT[1].position()
        if self.inv[1] is False:  # -
            if b - a < self.buteNeg[1]:
                print("STOP : Butée Negative")
                self.MOT[1].stopMotor()
            else:
                self.MOT[1].rmove(-a)
        else:
            if b + a > self.butePos[1]:
                print("STOP : Butée Positive")
                self.MOT[1].stopMotor()
            else:
                self.MOT[1].rmove(a)                
        
    def ZeroLat(self):  # remet le compteur a zero 
        self.MOT[0].setzero()

    def ZeroVert(self):  # remet le compteur a zero 
        self.MOT[1].setzero()
 
    def RefMark(self):  # Va en buttée et fait un zero
        """
            a faire ....
        """
        # self.motorType.refMark(self.motor)
   
    def unitTrans(self):
        '''
         unit change mot foc
        '''
        if self.showUnit is True:
            self.indexUnit = self.unitTransBouton.currentIndex()
        
        valueJog = self.jogStep.value()/self.unitChangeLat
        if self.indexUnit == 0:  # step
            self.unitChangeLat = 1
            self.unitChangeVert = 1
            self.unitNameTrans = 'step'
        if self.indexUnit == 1:  # micron
            self.unitChangeLat = float((1*self.stepmotor[0]))  
            self.unitChangeVert = float((1*self.stepmotor[1]))  
            self.unitNameTrans = 'um'
        if self.indexUnit == 2: 
            self.unitChangeLat = float((self.stepmotor[0])/1000)
            self.unitChangeVert = float((self.stepmotor[1])/1000)
            self.unitNameTrans = 'mm'
        if self.indexUnit == 3:  #  ps  en compte le double passage : 1 microns=6fs
            self.unitChangeLat = float(1*self.stepmotor[0]*0.0066666666)  
            self.unitChangeVert = float(1*self.stepmotor[1]*0.0066666666)  
            self.unitNameTrans = 'ps'
        if self.unitChangeLat == 0:
            self.unitChangeLat = 1  # if / par 0
        if self.unitChangeVert == 0:
            self.unitChangeVert = 1  # if / 0
        
        self.jogStep.setSuffix(" %s" % self.unitNameTrans)
        self.jogStep.setValue(valueJog*self.unitChangeLat)
        
    def StopMot(self):
        '''
        stop les moteurs
        '''
        for zzi in range(0, 2):
            self.MOT[zzi].stopMotor()

    @pyqtSlot(object)
    def PositionLat(self, Posi):
        ''' 
        affichage de la position a l aide du second thread
        '''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        
        a = a * self.unitChangeLat  # valeur tenant compte du changement d'unite
        if self.etat == 'FDC-':
            self.position_Lat.setText(self.etat)
            self.position_Lat.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'FDC+':
            self.position_Lat.setText('FDC +')
            self.position_Lat.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'Poweroff':
            self.position_Lat.setText('Power Off')
            self.position_Lat.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'mvt':
            self.position_Lat.setText('Mvt...')
            self.position_Lat.setStyleSheet('font: bold 15pt;color:white')
        elif self.etat == 'notconnected':
            self.position_Lat.setText('python server Not connected')
            self.position_Lat.setStyleSheet('font: bold 8pt;color:red')
        elif self.etat == 'errorConnect':
            self.position_Lat.setText('equip Not connected')
            self.position_Lat.setStyleSheet('font: bold 8pt;color:red')
        else:
            self.position_Lat.setText(str(round(a, 2)))  

    @pyqtSlot(object) 
    def PositionVert(self, Posi): 
        ''' 
        affichage de la position a l aide du second thread
        '''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        a = a * self.unitChangeVert  # valeur tenant compte du changement d'unite
        if self.etat == 'FDC-':
            self.position_Vert.setText(self.etat)
            self.position_Vert.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'FDC+':
            self.position_Vert.setText('FDC +')
            self.position_Vert.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'Poweroff':
            self.position_Vert.setText('Power Off')
            self.position_Vert.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'mvt':
            self.position_Vert.setText('Mvt...')
            self.position_Vert.setStyleSheet('font: bold 15pt;color:white')
        elif self.etat == 'notconnected':
            self.position_Vert.setText('python server Not connected')
            self.position_Vert.setStyleSheet('font: bold 8pt;color:red')
        elif self.etat == 'errorConnect':
            self.position_Vert.setText('equip Not connected')
            self.position_Vert.setStyleSheet('font: bold 8pt;color:red')
        else:
            self.position_Vert.setText(str(round(a,2))) 
        
    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.fini()
        time.sleep(0.1)
        event.accept()

    def fini(self): 
        '''
        a la fermeture de la fenetre on arrete le thread secondaire
        '''
        self.threadLat.stopThread()
        self.threadVert.stopThread()
        self.isWinOpen = False
        time.sleep(0.1)    


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    import time 
    POS = QtCore.pyqtSignal(object)  # signal of the second thread to main thread  to display motors position
    
    def __init__(self, parent=None, mot='',):
        super(PositionThread, self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                
                Posi = (self.MOT.position())
                time.sleep(0.05)
                
                try:
                    etat = self.MOT.etatMotor()
                    # print(etat)
                    time.sleep(0.05)
                    self.POS.emit([Posi, etat])
                    time.sleep(0.01)
                except Exception as e:
                    print('error emit', e)
                  
    def ThreadINIT(self):
        self.stop = False
                        
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        # self.terminate()
       

if __name__ == '__main__':
   
    appli = QApplication(sys.argv)
    mot5 = TILTMOTORGUI( IPLat="10.0.1.30", NoMotorLat=12, IPVert="10.0.1.30", NoMotorVert=13, nomWin='Tilt Turning Haut', background='',invLat=True,invVert=True)
    mot5.show()
    mot5.startThread2()
    appli.exec_()
