#! /home/sallejaune/loaenv/bin/python3.12
# -*- coding: utf-8 -*-
"""
Created on 10 December 2023

@author: Julien Gautier (LOA)
#last modified 01/06/2026 zmq
"""

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit, QToolButton
from PyQt6.QtWidgets import QInputDialog, QTextEdit, QDoubleSpinBox, QCheckBox
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QDialog
from PyQt6.QtWidgets import QComboBox, QLabel,QGroupBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSlot
import sys
import time
import os
import qdarkstyle
import pathlib
from collections import deque
from datetime import datetime
import __init__
import zmq_client_RSAI
from scanMotor2 import SCAN

__version__ = __init__.__version__
__author__ = __init__. __author__


class ONEMOTORGUI(QWidget):
    """
    User interface Motor class :
    ONEMOTOGUI(IpAddress, NoMotor,nomWin,showRef,unit,jogValue )
    IpAddress : Ip adress of the RSAI RACK
    NoMotor : Axis number
    optional :
        nomWin Name of the windows
        ShowRef = True see the reference windows
        unit : 0: step 1: um 2: mm 3: ps 4: °
        jogValue : Value in unit of the jog
    database is update when closing
    use zmq_client_RSAI to connect to the server one connection for on motor
    """

    def __init__(self, IpAdress, NoMotor, nomWin='', showRef=False, unit=1, jogValue=100, parent=None):

        super(ONEMOTORGUI, self).__init__()

        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.nomWin = nomWin
        self.refShowId = showRef
        self.indexUnit = unit
        self.jogValue = jogValue
        self.etat = 'ok'
        self.etat_old = 'ok'
        self.IpAdress = IpAdress
        self.NoMotor = NoMotor
        self.Posi = [0, self.etat]
        self.MOT = [0]
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.iconPlay = self.icon + "playGreen.png"
        self.iconPlay = pathlib.Path(self.iconPlay)
        self.iconPlay = pathlib.PurePosixPath(self.iconPlay)

        self.iconMoins = self.icon + "moinsBleu.png"
        self.iconMoins = pathlib.Path(self.iconMoins)
        self.iconMoins = pathlib.PurePosixPath(self.iconMoins)

        self.iconPlus = self.icon + "plusBleu.png"
        self.iconPlus = pathlib.Path(self.iconPlus)
        self.iconPlus = pathlib.PurePosixPath(self.iconPlus)

        self.iconStop = self.icon + "close.png"
        self.iconStop = pathlib.Path(self.iconStop)
        self.iconStop = pathlib.PurePosixPath(self.iconStop)

        self.iconUpdate = self.icon + "recycle.png"
        self.iconUpdate = pathlib.Path(self.iconUpdate)
        self.iconUpdate = pathlib.PurePosixPath(self.iconUpdate)
        # log 
        self.actionLog = deque(maxlen=20)
        self.logWindow = None

        self.MOT[0] = zmq_client_RSAI.MOTORRSAI(self.IpAdress, self.NoMotor)
        time.sleep(0.05) # wait for connection

        if self.MOT[0].isconnected is True:
            self.addLog("Connexion server OK: ", f"Moteur {self.NoMotor} on rack ({self.IpAdress})")
        else:
            self.addLog("Connexion server failed: ", f"Moteur {self.NoMotor} on rack ({self.IpAdress})")
        

        self.equipementName = self.MOT[0].getEquipementName()
        
        self.stepmotor = [0, 0, 0]
        self.butePos = [0, 0, 0]
        self.buteNeg = [0, 0, 0]
        self.name = [0, 0, 0]
        
        for zzi in range(0, 1):
            self.stepmotor[zzi] = float(self.MOT[0].getStepValue()) # list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[0].getButLogPlusValue())  # list 
            self.buteNeg[zzi] = float(self.MOT[0].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[0].name)

        # initita   
        if self.indexUnit == 0:  # step
            self.unitChange = 1
            self.unitName = 'step'

        if self.indexUnit == 1:  # micron
            self.unitChange = float((self.stepmotor[0]))
            self.unitName = 'um'
        if self.indexUnit == 2:  # mm
            self.unitChange = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        if self.indexUnit == 3:  # ps  double passage : 1 microns=6fs
            self.unitChange = float(self.stepmotor[0]*0.0066666666)
            self.unitName = 'ps'
        if self.indexUnit == 4: # en degres
            self.unitChange =  self.stepmotor[0]
            self.unitName = '°'

        self.thread = PositionThread(self, mot=self.MOT[0])  # thread for displaying position should be started by startThread2
        self.thread.POS.connect(self.Position)
        # Log initial
        self.addLog("Initialisation", f"Moteur {self.NoMotor} on rack {self.equipementName}({self.IpAdress})")
        self.refreshLog()
        self.scanWidget = SCAN(MOT=self.MOT[0])  # for the scan
        self.configWidget = ConfigMotorWidget(motor=self.MOT[0], parent=self)  # Widget de configuration
        self.setup()
        self.updateFromRSAI()
        self.unit()
        self.jogStep.setValue(self.jogValue)
        self.actionButton()
        
    def updateFromRSAI(self):
        # update from the server RSAI python (pull)
        self.MOT[0].update()
        time.sleep(0.1)
        # to avoid to access to the database
        for zzi in range(0,1):
            self.stepmotor[zzi] = float((self.MOT[0].step))  # list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[0].butPlus)  # list
            self.buteNeg[zzi] = float(self.MOT[0].butMoins)
            self.name[zzi] = str(self.MOT[0].name)
            ## initialisation of the jog value 
        
        self.setWindowTitle(self.nomWin + str(self.equipementName) + ' (' + str(self.IpAdress) + ')  '+ ' [M'+ str(self.NoMotor) + ']  ' + self.name[0] )
        
        self.nom.setText(self.name[0])
        self.refValue = self.MOT[0].refValue     # en micron
        
        self.refValueStep = [] # en step 
        for ref in self.refValue:
            self.refValueStep.append(ref / self.stepmotor[0])

        self.refValueStepOld = self.refValueStep.copy()
        
        self.refName = self.MOT[0].refName
        self.refNameOld = self.refName.copy() 
        iii = 0
        for saveNameButton in self.posText:  # reference name
            saveNameButton.setText(self.refName[iii]) # print  ref name
            iii += 1
        eee = 0
        for absButton in self.absRef:
            absButton.setValue(float(self.refValueStep[eee]*self.unitChange))  # )/self.unitChange)) # save reference value
            eee += 1
        self.addLog("Update", f"Moteur {self.name[zzi]} ({self.NoMotor}) on rack {self.equipementName}({self.IpAdress}) is updated from RSAI data Base (pull)")
        
        self.addLog("Update step", f"{self.stepmotor[zzi]}")
        self.addLog("Update butee +", f"{self.butePos[zzi]}")
        self.addLog("Update butee -", f"{self.buteNeg[zzi]}")
        self.addLog("Update nameRef", f"{self.refName}")
        self.addLog("Update valueRef(step)", f"{self.refValueStep}")
        self.refreshLog()

    def updateDB(self):
        #  update the Data base
        
        i = 0
        if self.refValueStep != self.refValueStepOld:
            #  print('update ref values')
            for ref in self.refValueStep:
                ref = ref * float((self.stepmotor[0]))  # en micron
                a = self.MOT[0].setRefValue(i, int(ref))
                i += 1
        i = 0
        if self.refName != self.refNameOld:
            #  print('update ref Name')
            for ref in self.refName:
                self.MOT[0].setRefName(i, ref)
                i += 1
        if self.refValueStep != self.refValueStepOld or self.refName != self.refNameOld:
            self.addLog("Update", f"Moteur {self.NoMotor} on rack {self.equipementName}({self.IpAdress})  update the RSAI data Base (push)")
            #self.refreshLog()

    def startThread2(self):
        # start position and state thread
        self.thread.ThreadINIT()
        self.thread.start()
        time.sleep(0.01)

    def setup(self):

        vbox1 = QVBoxLayout()
        hboxTitre = QHBoxLayout()
        self.nom = QLabel()
        self.nom.setStyleSheet("font: bold 15pt;color:yellow")
        hboxTitre.addWidget(self.nom)

        self.enPosition = QLineEdit()
        self.enPosition.setMaximumWidth(180)
        self.enPosition.setStyleSheet("font: bold 10pt")
        self.enPosition.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        hboxTitre.addWidget(self.enPosition)
        self.butNegButt = QCheckBox('Log FDC-', self)
        hboxTitre.addWidget(self.butNegButt)

        self.butPosButt = QCheckBox('Log FDC+', self)
        hboxTitre.addWidget(self.butPosButt)
        vbox1.addLayout(hboxTitre)

        hbox0 = QHBoxLayout()
        self.position = QLabel('1234567')
        self.position.setMaximumWidth(300)
        self.position.setStyleSheet("font: bold 25pt" )

        self.unitBouton = QComboBox()
        self.unitBouton.addItem('Step')
        self.unitBouton.addItem('um')
        self.unitBouton.addItem('mm')
        self.unitBouton.addItem('ps')
        self.unitBouton.addItem('°')
        self.unitBouton.setMaximumWidth(100)
        self.unitBouton.setMinimumWidth(100)
        self.unitBouton.setStyleSheet("font: bold 12pt")
        self.unitBouton.setCurrentIndex(self.indexUnit)

        self.zeroButton = QPushButton('Zero')
        self.zeroButton.setToolTip('set origin')
        self.zeroButton.setMaximumWidth(50)

        hbox0.addWidget(self.position)
        hbox0.addWidget(self.unitBouton)
        hbox0.addWidget(self.zeroButton)
        vbox1.addLayout(hbox0)
        
        hboxAbs = QHBoxLayout()
        absolueLabel = QLabel('Absolue mouvement')

        self.MoveStep = QDoubleSpinBox()
        self.MoveStep.setMaximum(1000000)
        self.MoveStep.setMinimum(-1000000)

        self.absMvtButton = QToolButton()
        self.absMvtButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))

        self.absMvtButton.setMinimumHeight(50)
        self.absMvtButton.setMaximumHeight(50)
        self.absMvtButton.setMinimumWidth(50)
        self.absMvtButton.setMaximumWidth(50)

        hboxAbs.addWidget(absolueLabel)
        hboxAbs.addWidget(self.MoveStep)
        hboxAbs.addWidget(self.absMvtButton)
        vbox1.addLayout(hboxAbs)
        vbox1.addSpacing(10)
        hbox1 = QHBoxLayout()
        self.moins = QToolButton()
        self.moins.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconMoins,self.iconMoins))

        self.moins.setMinimumHeight(70)
        self.moins.setMaximumHeight(70)
        self.moins.setMinimumWidth(70)
        self.moins.setMaximumWidth(70)

        hbox1.addWidget(self.moins)

        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(1000000)
        self.jogStep.setMaximumWidth(130)
        self.jogStep.setStyleSheet("font: bold 12pt")
        self.jogStep.setValue(self.jogValue)

        hbox1.addWidget(self.jogStep)

        self.plus = QToolButton()
        self.plus.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlus,self.iconPlus))
        self.plus.setMinimumHeight(70)
        self.plus.setMaximumHeight(70)
        self.plus.setMinimumWidth(70)
        self.plus.setMaximumWidth(70)
        hbox1.addWidget(self.plus)

        vbox1.addLayout(hbox1)
        vbox1.addSpacing(10)

        hbox2 = QHBoxLayout()
        self.stopButton = QToolButton()
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop))

        self.stopButton.setMaximumHeight(70)
        self.stopButton.setMaximumWidth(70)
        self.stopButton.setMinimumHeight(70)
        self.stopButton.setMinimumWidth(70)
        hbox2.addWidget(self.stopButton)
        vbox2 = QVBoxLayout()

        self.showRef = QPushButton('Show Ref')
        self.showRef.setMaximumWidth(90)
        vbox2.addWidget(self.showRef)
        self.scan = QPushButton('Scan')
        self.scan.setMaximumWidth(90)
        vbox2.addWidget(self.scan)
        # self.presetButton = QPushButton('Preset')
        # self.presetButton.setMaximumWidth(90)
        # vbox2.addWidget(self.presetButton)
        self.configButton = QPushButton('⚙️ Config')
        self.configButton.setMaximumWidth(90)
        self.configButton.setToolTip('Configurer butées et step')
        vbox2.addWidget(self.configButton)
        # self.logButton = QPushButton('📋 Log')
        # self.logButton.setMaximumWidth(90)
        # self.logButton.setStyleSheet("font: bold 10pt; color: #4a9eff;")
        # self.logButton.setToolTip("Afficher l'historique des actions (20 dernières)")
        # vbox2.addWidget(self.logButton)

        hbox2.addLayout(vbox2)

        vbox1.addLayout(hbox2)
        vbox1.addSpacing(10)

        self.REF1 = REF1M(num=1)
        self.REF2 = REF1M(num=2)
        self.REF3 = REF1M(num=3)
        self.REF4 = REF1M(num=4)
        self.REF5 = REF1M(num=5)
        self.REF6 = REF1M(num=6)

        grid_layoutRef = QGridLayout()
        grid_layoutRef.setVerticalSpacing(4)
        grid_layoutRef.setHorizontalSpacing(4)
        grid_layoutRef.addWidget(self.REF1, 0, 0)
        grid_layoutRef.addWidget(self.REF2, 0, 1)
        grid_layoutRef.addWidget(self.REF3, 1, 0)
        grid_layoutRef.addWidget(self.REF4, 1, 1)
        grid_layoutRef.addWidget(self.REF5, 2, 0)
        grid_layoutRef.addWidget(self.REF6, 2, 1)

        self.widget6REF = QWidget()
        self.widget6REF.setLayout(grid_layoutRef)
        vbox1.addWidget(self.widget6REF)
        self.setLayout(vbox1)

        self.absRef = [self.REF1.ABSref, self.REF2.ABSref, self.REF3.ABSref, self.REF4.ABSref, self.REF5.ABSref, self.REF6.ABSref]

        self.posText = [self.REF1.posText, self.REF2.posText, self.REF3.posText, self.REF4.posText, self.REF5.posText, self.REF6.posText]
        self.POS = [self.REF1.Pos, self.REF2.Pos, self.REF3.Pos, self.REF4.Pos, self.REF5.Pos, self.REF6.Pos]
        self.Take = [self.REF1.take, self.REF2.take, self.REF3.take, self.REF4.take, self.REF5.take, self.REF6.take]
        self.jogStep.setFocus()
        self.refShow()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def focusInEvent(self, event):
        # change refresh time when window in focus or not ne fonctionne pas 
        super().focusInEvent(event)
        self.thread.positionSleep = 0.05
        # print('in focus')

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.thread.positionSleep = 1
        # print('out focus')

    def actionButton(self):
        '''
           buttons action setup
        '''
        self.unitBouton.currentIndexChanged.connect(self.unit)  # unit change
        self.absMvtButton.clicked.connect(self.MOVE)
        self.plus.clicked.connect(self.pMove)  # jog + foc
        self.plus.setAutoRepeat(True)
        self.moins.clicked.connect(self.mMove)  # jog - foc
        self.moins.setAutoRepeat(True) 
        self.scan.clicked.connect(lambda: self.open_widget(self.scanWidget))
        self.configButton.clicked.connect(lambda: self.open_widget(self.configWidget))
        self.zeroButton.clicked.connect(self.Zero)  # reset display to 0
        # self.refZeroButton.clicked.connect(self.RefMark) # todo
        self.stopButton.clicked.connect(self.StopMot)  # stop motors 
        self.showRef.clicked.connect(self.refShow)  # show references widgets
        # self.presetButton.clicked.connect(self.preset)  # set postion
        iii = 0
        for saveNameButton in self.posText:  # reference name
            saveNameButton.textChanged.connect(self.savName)
            saveNameButton.setText(self.refName[iii])  # print  ref name
            iii += 1

        for posButton in self.POS:  # button GO
            posButton.clicked.connect(self.ref)    # go to reference value
        eee = 0
        for absButton in self.absRef:
            nbRef = str(eee)
            absButton.setValue(float(self.refValueStep[eee]*self.unitChange))  # save reference value
            absButton.editingFinished.connect(self.savRef)  # sauv value
            eee += 1

        for takeButton in self.Take:
            takeButton.clicked.connect(self.take)  # take the value
        
       # self.logButton.clicked.connect(self.showLog)  # show log window
    
    def open_widget(self, fene):

        """ open new widget
        """
        if fene.isWinOpen is False:
            # New widget"
            fene.show()
            fene.isWinOpen = True
            if fene == self.scanWidget:
                fene.startTrigThread()
        else:
            # fene.activateWindow()
            fene.raise_()
            fene.showNormal()
        
    def refShow(self):
        
        if self.refShowId is True:
            # self.resize(368, 345)
            self.widget6REF.show()
            self.refShowId = False
            self.showRef.setText('Hide Ref')
            self.setFixedSize(430, 800)
        else:
            # print(self.geometry()
            self.widget6REF.hide()
            self.refShowId = True
            self.showRef.setText('Show Ref')
            self.setFixedSize(430, 380)
    
    def MOVE(self):
        '''
        absolue mouvment
        '''
        a = float(self.MoveStep.value())
        a = float(a/self.unitChange)  # changement d unite en step
        b = self.MOT[0].position()
        if a < self.buteNeg[0]:
            #  print("STOP : Butée Négative")
            self.butNegButt.setChecked(True)
            self.butNegButt.setStyleSheet('color:red')
            self.MOT[0].stopMotor()
            self.addLog("STOP", "Butée négative atteinte")
            # self.refreshLog()
        elif a > self.butePos[0]:
            #  print("STOP : Butée Positive")
            self.butPosButt.setChecked(True)
            self.butPosButt.setStyleSheet('color:red')
            self.MOT[0].stopMotor()
            self.addLog("STOP", "Butée positive atteinte")
            # self.refreshLog()
        else:
            self.MOT[0].move(a)
            self.butNegButt.setChecked(False)
            self.butNegButt.setStyleSheet("")
            self.butPosButt.setChecked(False)
            self.butPosButt.setStyleSheet("")
            self.addLog("absolue move", f"{self.MoveStep.value():.2f} "
                        f"{self.unitName}{' position avant mvt :'} {b*self.unitChange} {self.unitName}")
             #  self.refreshLog()

    def pMove(self):
        '''
        action jog + foc 
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        if b + a > self.butePos[0]:
            self.addLog("STOP", "Butée positive")
            #  self.refreshLog()
            self.MOT[0].stopMotor()
            self.butPosButt.setChecked(True)
            self.butPosButt.setStyleSheet('color:red')
        else:
            self.MOT[0].rmove(a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butPosButt.setStyleSheet("")
            self.butNegButt.setStyleSheet("")
            self.addLog("rmove", f"{'+'}{self.jogStep.value():.2f}"
                        f"{self.unitName}{' position avant mvt :'} {b*self.unitChange} {self.unitName}")
            #  self.refreshLog()

    def mMove(self):
        '''
        action jog - foc
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        if b - a < self.buteNeg[0]:
            #  ("STOP : negative switch")
            self.addLog("STOP", "Butée négative atteinte")
            #  self.refreshLog()
            self.MOT[0].stopMotor()
            self.butNegButt.setChecked(True)
            self.butNegButt.setStyleSheet('color:red')
        else:
            self.MOT[0].rmove(-a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butNegButt.setStyleSheet("")
            self.butPosButt.setStyleSheet("")
            self.addLog("rmove", f"{'-'}{self.jogStep.value():.2f} "
                        f"{self.unitName}{' position avant mvt :'} {b*self.unitChange} {self.unitName}")
            #  self.refreshLog()

    def Zero(self):  # zero
        b = self.MOT[0].position()
        self.MOT[0].setzero()
        self.addLog("Set Zero", f"{' position avant remise à zero : '} {b*self.unitChange} {self.unitName}")
        #  self.refreshLog()

    def RefMark(self): 
        """
            todo ....
        """
        # self.motorType.refMark(self.motor)

    def unit(self):
        '''
        unit change mot foc
        '''
        self.indexUnit = self.unitBouton.currentIndex()
        valueJog = self.jogStep.value()/self.unitChange 
        moveVal = self.MoveStep.value()/self.unitChange

        if self.indexUnit == 0:  #  step
            self.unitChange = 1
            self.unitName = 'step'
 
        if self.indexUnit == 1:  # micron
            self.unitChange = float(self.stepmotor[0])
            self.unitName = 'um'

        if self.indexUnit == 2:  # mm
            self.unitChange = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        if self.indexUnit == 3:  # ps  double passage : 1 microns=6fs
            self.unitChange = float(self.stepmotor[0]*0.0066666666)
            self.unitName = 'ps'
        if self.indexUnit == 4:  # en degres
            self.unitChange =  self.stepmotor[0]
            self.unitName = '°'

        if self.unitChange == 0:
            self.unitChange = 1  # avoid /0

        self.jogStep.setSuffix(" %s" % self.unitName)
        self.jogStep.setValue(valueJog*self.unitChange)
        self.MoveStep.setValue(moveVal*self.unitChange)
        self.MoveStep.setSuffix(" %s" % self.unitName)

        eee = 0
        for absButton in self.absRef:  # change the value of reference
            nbRef = eee
            absButton.setValue(float(self.refValueStep[eee] * self.unitChange))
            absButton.setSuffix(" %s" % self.unitName)
            eee += 1
        self.Position(self.Posi)

    def StopMot(self):
        '''
        stop all motors
        '''
        self.REF1.show()
        for zzi in range(0, 1):
            self.MOT[zzi].stopMotor()
            self.addLog("STOP moteur", "Arrêt du moteur demandé")
            #  self.refreshLog()

    @pyqtSlot(object)
    def Position(self, Posi):
        '''
        Position  display read from the second thread
        '''
        self.Posi = Posi
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        b = a  # value in step
        a = a * self.unitChange  # value with unit changed

        self.position.setText(str(round(a, 2)))
        self.position.setStyleSheet('font: bold 30pt;color:green')
        if self.etat != self.etat_old:
            self.etat_old = self.etat
            if self.etat == 'FDC-':
                self.enPosition.setText(self.etat)
                self.enPosition.setStyleSheet('font: bold 15pt;color:red')
            elif self.etat == 'FDC+':
                self.enPosition.setText('FDC +')
                self.enPosition.setStyleSheet('font: bold 15pt;color:red')
            elif self.etat == 'Poweroff':
                self.enPosition.setText('Power Off')
                self.enPosition.setStyleSheet('font: bold 15pt;color:red')
            elif self.etat == 'mvt':
                self.enPosition.setText('Mvt...')
                self.enPosition.setStyleSheet('font: bold 15pt;color:white')
            elif self.etat == 'notconnected':
                self.enPosition.setText('python server Not connected')
                self.enPosition.setStyleSheet('font: bold 8pt;color:red')
            elif self.etat == 'errorConnect':
                self.enPosition.setText('equip Not connected')
                self.enPosition.setStyleSheet('font: bold 8pt;color:red')

        positionConnue = 0
        precis = 5  # to show position name
        if (self.etat == 'ok' or self.etat == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue == 0:

                    if float(self.refValueStep[nbRefInt-1]) - precis < b < float(self.refValueStep[nbRefInt-1]) + precis: #self.MOT[0].getRefValue
                        self.enPosition.setText(str(self.refName[nbRefInt-1]))
                        positionConnue = 1
        if positionConnue == 0 and (self.etat == 'ok' or self.etat == '?'):
            self.enPosition.setText(' ')

    def Etat(self, etat):
        # return  motor state
        self.etat = etat

    def take(self):
        '''
        take and save the reference
        '''
        sender = QtCore.QObject.sender(self)  # take the name of  the button 

        nbRef = str(sender.objectName()[0])
        reply = QMessageBox.question(None, 'Save Position ?', "Do you want to save this position ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            tpos = float(self.MOT[0].position())
            self.refValueStep[int(nbRef)-1] = tpos
            self.absRef[int(nbRef)-1].setValue(tpos*self.unitChange)
            self.addLog("Reference value", f"{' saved value ref'} {nbRef} {':'}{self.absRef[int(nbRef)-1].value()}{self.unitName}")
            #  self.refreshLog()

    def ref(self):
        '''
        Move the motor to the reference value in step : GO button
        '''
        sender = QtCore.QObject.sender(self)
        reply = QMessageBox.question(None, 'Go to this Position ?', "Do you want to GO to this position ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nbRef = str(sender.objectName()[0])
            for i in range(0, 1):
                vref = int(self.refValueStep[int(nbRef)-1])
                if vref < self.buteNeg[i]:
                    #  print("STOP : negative switch")
                    self.butNegButt.setChecked(True)
                    self.butNegButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                elif vref > self.butePos[i]:
                    #  print("STOP : positive switch")
                    self.butPosButt.setChecked(True)
                    self.butPosButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                else:

                    self.addLog("Reference ", f"{' move to ref'} {nbRef}{':'}{self.absRef[int(nbRef)-1].value()}{self.unitName}")
                    #  self.refreshLog()
                    self.MOT[i].move(vref)
                    self.butNegButt.setChecked(False)
                    self.butNegButt.setStyleSheet("")
                    self.butPosButt.setChecked(False)
                    self.butPosButt.setStyleSheet('color:red')

    def savName(self):
        '''
        Save reference name
        '''
        sender = QtCore.QObject.sender(self)
        nbRef = sender.objectName()[0]  # PosTExt1
        vname = self.posText[int(nbRef)-1].text()
        for i in range(0, 1):
            self.refName[int(nbRef)-1] = str(vname)

    def savRef(self):
        '''
        save reference  value
        '''
        #  print('ii deb ',self.refValueStep,self.refValueStepOld)
        sender = QtCore.QObject.sender(self)
        nbRef = sender.objectName()[0]  # nom du button ABSref1
        
        vref = int(self.absRef[int(nbRef)-1].value())
        # print('iifff',self.refValueStep,self.refValueStepOld)
        
        self.refValueStep[int(nbRef)-1] = vref/self.unitChange  # on sauvegarde en step 
        # print('ii',self.refValueStep)
        # print(self.refValueStepOld)
    
    def preset(self):
        # set motor position
        val, ok = QInputDialog.getDouble(self, 'Set Potion value', 'Position value to set(%s) ' % self.unitName)
        if ok:
            
            self.addLog("Preset Position", f"{' position avant mvt :'} {self.Posi[0]} {self.unitName}")
            #  self.refreshLog()
            val = val / self.unitChange
            self.MOT[0].setPosition(int(val))
            
    def addLog(self, action, details=""):
        """Ajoute une action au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        self.actionLog.append(log_entry)
        #  print(f"[LOG] {timestamp} - {action} {details}")
    
    def showLog(self):
        """Affiche la fenêtre de log"""
        if self.logWindow is None or not self.logWindow.isVisible():
            self.logWindow = LogWindow(parent=self)
            self.logWindow.setLogs(list(self.actionLog))
            self.logWindow.show()
        else:
            self.logWindow.raise_()
            self.logWindow.activateWindow()
            #  self.refreshLog()
    
    def refreshLog(self):
        """Rafraîchit l'affichage du log"""
        if self.logWindow and self.logWindow.isVisible():
            self.logWindow.setLogs(list(self.actionLog))
    
    def clearLogs(self):
        """Efface tous les logs"""
        self.actionLog.clear()
        self.addLog("Historique effacé", "")

    def closeEvent(self, event):
        """
        When closing the window
        """
        self.fini()
        time.sleep(1)
        event.accept()

    def fini(self):
        '''
        at the end we close all the thread
        '''
        self.thread.stopThread()
        self.isWinOpen = False
        self.updateDB()

        if self.scanWidget.isWinOpen is True:
            self.scanWidget.close()
            #  print('close moto widget')
        time.sleep(0.05)
        # self.MOT[0].closeConnexion()


class REF1M(QWidget):
    '''Ref widget class
    '''
    def __init__(self, num=0, parent=None):
        super(REF1M, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.wid = QWidget()
        self.id = num
        self.vboxPos = QVBoxLayout()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.posText = QLineEdit('ref')
        self.posText.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.posText.setStyleSheet("font: bold 15pt")
        self.posText.setObjectName('%s' % self.id)
#        self.posText.setMaximumWidth(80)
        self.vboxPos.addWidget(self.posText)
        self.iconTake = self.icon + "disquette.png"
        self.iconTake = pathlib.Path(self.iconTake)
        self.iconTake = pathlib.PurePosixPath(self.iconTake)
        self.take = QToolButton()
        self.take.setObjectName('%s'% self.id)
        self.take.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconTake,self.iconTake))
        self.take.setMaximumWidth(30)
        self.take.setMinimumWidth(30)
        self.take.setMinimumHeight(30)
        self.take.setMaximumHeight(30)
        self.takeLayout = QHBoxLayout()
        self.takeLayout.addWidget(self.take)

        self.iconGo = self.icon + "go.png"
        self.iconGo = pathlib.Path(self.iconGo)
        self.iconGo = pathlib.PurePosixPath(self.iconGo)
        self.Pos = QToolButton()
        self.Pos.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconGo,self.iconGo))
        self.Pos.setMinimumHeight(30)
        self.Pos.setMaximumHeight(30)
        self.Pos.setMinimumWidth(30)
        self.Pos.setMaximumWidth(30)
        self.PosLayout = QHBoxLayout()
        self.PosLayout.addWidget(self.Pos)
        self.Pos.setObjectName('%s' % self.id)
        # ○self.Pos.setStyleSheet("background-color: rgb(85, 170, 255)")
        Labelref = QLabel('Pos :')
        Labelref.setMaximumWidth(30)
        Labelref.setStyleSheet("font: 9pt")
        self.ABSref = QDoubleSpinBox()
        self.ABSref.setMaximum(500000000)
        self.ABSref.setMinimum(-500000000)
        self.ABSref.setValue(123456)
        self.ABSref.setMaximumWidth(80)
        self.ABSref.setObjectName('%s' % self.id)
        self.ABSref.setStyleSheet("font: 9pt")

        grid_layoutPos = QGridLayout()
        grid_layoutPos.setVerticalSpacing(5)
        grid_layoutPos.setHorizontalSpacing(10)
        grid_layoutPos.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        grid_layoutPos.addLayout(self.takeLayout, 0, 0)
        grid_layoutPos.addLayout(self.PosLayout, 0, 1)
        grid_layoutPos.addWidget(Labelref, 1, 0)
        grid_layoutPos.addWidget(self.ABSref, 1, 1)

        self.vboxPos.addLayout(grid_layoutPos)
        self.wid.setStyleSheet("background-color: rgb(60, 77, 87);border-radius:10px")
        self.wid.setLayout(self.vboxPos)

        mainVert = QVBoxLayout()
        mainVert.addWidget(self.wid)
        mainVert.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainVert)


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position and state
    '''
    import time
    POS = QtCore.pyqtSignal(object)  # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mot='',):
        super(PositionThread, self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False
        self.positionSleep = 0.05
        self.etat_old = ""
        self.Posi_old = 0

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                #  print(self.positionSleep)
                Posi = (self.MOT.position())
                time.sleep(self.positionSleep)
                etat = self.MOT.etatMotor()
                try:
                    if self.Posi_old != Posi or self.etat_old != etat:  # on emet que si different
                        self.POS.emit([Posi, etat])
                        self.Posi_old = Posi
                        self.etat_old = etat

                except Exception as e:
                    print('error emit', e)

    def ThreadINIT(self):
        self.stop = False

    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        # self.terminate()


class LogWindow(QDialog):
    """
    Fenêtre de visualisation des logs
    Affiche les 20 dernières actions du moteur
    """
    
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.setWindowTitle("📋 Historique des Actions")
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Dernières actions (max 20)")
        title.setStyleSheet("font: bold 12pt; color: #4a9eff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Zone de texte pour les logs
        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        self.logText.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: 2px solid #4a9eff;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.logText)
        
        # Boutons
        buttonLayout = QHBoxLayout()
        
        self.refreshButton = QPushButton("🔄 Actualiser")
        self.refreshButton.setMaximumWidth(120)
        self.refreshButton.clicked.connect(self.refresh)
        
        self.clearButton = QPushButton("🗑️ Effacer")
        self.clearButton.setMaximumWidth(120)
        self.clearButton.clicked.connect(self.clearLogs)
        
        self.closeButton = QPushButton("✖ Fermer")
        self.closeButton.setMaximumWidth(120)
        self.closeButton.clicked.connect(self.close)
        
        buttonLayout.addWidget(self.refreshButton)
        buttonLayout.addWidget(self.clearButton)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.closeButton)
        
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
    
    def setLogs(self, logs):
        """Affiche les logs"""
        self.logText.clear()
        
        if not logs:
            self.logText.setHtml('<span style="color: #ff6b6b;">Aucune action enregistrée</span>')
            return
        
        html = ""
        for log in logs:
            timestamp = log['timestamp']
            action = log['action']
            details = log.get('details', '')
            
            # Coloration selon le type d'action
            if 'absolue move' in action.lower() or 'rmove' in action.lower():
                color = "#4a9eff"  # Bleu pour les mouvements
                icon = "→"
            elif 'stop' in action.lower():
                color = "#ff6b6b"  # Rouge pour les arrêts
                icon = "⏹"
            elif 'zero' in action.lower():
                color = "#ffd43b"  # Jaune pour zero
                icon = "⓪"
            elif 'ref' in action.lower():
                color = "#51cf66"  # Vert pour les références
                icon = "📍"
            elif 'update' in action.lower():
                color = "#51cf66"  # Vert pour les updates
                icon = "⏹"
            else:
                color = "#aaaaaa"  # Gris pour le reste
                icon = "•"
            
            html += f'<span style="color: #888;">[{timestamp}]</span> '
            html += f'<span style="color: {color}; font-weight: bold;">{icon} {action}</span>'
            
            if details:
                html += f' <span style="color: #ccc;">  {details}</span>'
            
            html += '<br>'
        
        self.logText.setHtml(html)
        
        # Scroller vers le bas (dernière action)
        scrollbar = self.logText.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def refresh(self):
        """Signal pour rafraîchir (géré par le parent)"""
        if self.parent():
            self.parent().refreshLog()
    
    def clearLogs(self):
        """Demande confirmation et efface les logs"""
        reply = QMessageBox.question(
            self, 
            'Effacer les logs ?', 
            "Voulez-vous effacer tout l'historique ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.parent():
                self.parent().clearLogs()
            self.logText.setHtml('<span style="color: #ff6b6b;">Logs effacés</span>')


class ConfigMotorWidget(QWidget):
    """Widget de configuration des butées et step - AVEC PRESET ET LOG"""
    
    def __init__(self, motor, parent=None):
        super(ConfigMotorWidget, self).__init__()
        self.motor = motor
        self.parent = parent
        self.isWinOpen = False
        
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowTitle(f"Configuration Moteur - {self.parent.name[0]}")
        self.setMinimumWidth(450)
        
        self.setup()
        self.loadCurrentValues()
        
    def setup(self):
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(12)
        mainLayout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("⚙️ Motor Configuration")
        title.setStyleSheet("font: bold 14pt; color: #4a9eff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mainLayout.addWidget(title)
        
        # Informations
        infoGroup = QGroupBox("Informations")
        infoGroup.setStyleSheet("""
            QGroupBox {
                font: bold 11pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        infoLayout = QVBoxLayout()
        
        self.motorNameLabel = QLabel(f"Motor: {self.parent.name[0]}")
        self.motorNameLabel.setStyleSheet("font: bold 11pt;")
        infoLayout.addWidget(self.motorNameLabel)
        
        self.rackLabel = QLabel(f"Rack: {self.parent.equipementName} ({self.parent.IpAdress})")
        infoLayout.addWidget(self.rackLabel)
        
        self.axisLabel = QLabel(f"Axe: {self.parent.NoMotor}")
        infoLayout.addWidget(self.axisLabel)
        
        infoGroup.setLayout(infoLayout)
        mainLayout.addWidget(infoGroup)
        
        # Step
        stepGroup = QGroupBox("Step Value")
        stepGroup.setStyleSheet("""
            QGroupBox {
                font: bold 11pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        stepLayout = QVBoxLayout()
        
        stepHelpLabel = QLabel("1 step = ? microns")
        stepHelpLabel.setStyleSheet("color: #888; font-size: 9pt;")
        stepLayout.addWidget(stepHelpLabel)
        
        stepInputLayout = QHBoxLayout()
        stepLabel = QLabel("Step (µm):")
        stepLabel.setMinimumWidth(100)
        
        self.stepSpinBox = QDoubleSpinBox()
        self.stepSpinBox.setDecimals(6)
        self.stepSpinBox.setRange(0.000001, 1000.0)
        self.stepSpinBox.setValue(1.0)
        self.stepSpinBox.setSuffix(" µm")
        self.stepSpinBox.setMinimumWidth(150)
        self.stepSpinBox.setStyleSheet("padding: 5px;")
        
        stepInputLayout.addWidget(stepLabel)
        stepInputLayout.addWidget(self.stepSpinBox)
        stepInputLayout.addStretch()
        
        stepLayout.addLayout(stepInputLayout)
        stepGroup.setLayout(stepLayout)
        mainLayout.addWidget(stepGroup)
        
        # Butées
        buteesGroup = QGroupBox("Software Limits")
        buteesGroup.setStyleSheet("""
            QGroupBox {
                font: bold 11pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        buteesLayout = QVBoxLayout()
        
        # Butée Négative
        butNegLayout = QHBoxLayout()
        butNegLabel = QLabel("Switch - (step):")
        butNegLabel.setMinimumWidth(100)
        
        self.butNegSpinBox = QDoubleSpinBox()
        self.butNegSpinBox.setDecimals(2)
        self.butNegSpinBox.setRange(-10000000, 10000000)
        self.butNegSpinBox.setValue(0)
        self.butNegSpinBox.setSuffix(" step")
        self.butNegSpinBox.setMinimumWidth(150)
        self.butNegSpinBox.setStyleSheet("padding: 5px;")
        
        butNegLayout.addWidget(butNegLabel)
        butNegLayout.addWidget(self.butNegSpinBox)
        butNegLayout.addStretch()
        buteesLayout.addLayout(butNegLayout)
        
        # Butée Positive
        butPosLayout = QHBoxLayout()
        butPosLabel = QLabel("Switch + (step):")
        butPosLabel.setMinimumWidth(100)
        
        self.butPosSpinBox = QDoubleSpinBox()
        self.butPosSpinBox.setDecimals(2)
        self.butPosSpinBox.setRange(-10000000, 10000000)
        self.butPosSpinBox.setValue(100000)
        self.butPosSpinBox.setSuffix(" step")
        self.butPosSpinBox.setMinimumWidth(150)
        self.butPosSpinBox.setStyleSheet("padding: 5px;")
        
        butPosLayout.addWidget(butPosLabel)
        butPosLayout.addWidget(self.butPosSpinBox)
        butPosLayout.addStretch()
        buteesLayout.addLayout(butPosLayout)
        
        buteesGroup.setLayout(buteesLayout)
        mainLayout.addWidget(buteesGroup)
        
        mainLayout.addStretch()
        
        # Boutons - AJOUT PRESET ET LOG
        buttonLayout = QGridLayout()
        buttonLayout.setSpacing(8)
        
        self.presetButton = QPushButton("🎯 Preset")
        self.presetButton.setMinimumHeight(35)
        self.presetButton.setStyleSheet("padding: 8px; font: 10pt;")
        self.presetButton.setToolTip("Définir une position arbitraire")
        self.presetButton.clicked.connect(self.parent.preset)
        
        self.logButton = QPushButton("📋 Historique")
        self.logButton.setMinimumHeight(35)
        self.logButton.setStyleSheet("padding: 8px; font: 10pt; color: #4a9eff;")
        self.logButton.setToolTip("Afficher l'historique des actions")
        self.logButton.clicked.connect(self.parent.showLog)
        
        self.saveButton = QPushButton("💾 Sauvegarder")
        self.saveButton.setMinimumHeight(35)
        self.saveButton.setStyleSheet("padding: 8px; font: 10pt;")
        self.saveButton.clicked.connect(self.saveConfiguration)
        
        self.cancelButton = QPushButton("❌ Annuler")
        self.cancelButton.setMinimumHeight(35)
        self.cancelButton.setStyleSheet("padding: 8px; font: 10pt;")
        self.cancelButton.clicked.connect(self.close)
        
        self.resetButton = QPushButton("🔄 Recharger")
        self.resetButton.setMinimumHeight(35)
        self.resetButton.setStyleSheet("padding: 8px; font: 10pt;")
        self.resetButton.clicked.connect(self.loadCurrentValues)
        
        buttonLayout.addWidget(self.presetButton, 0, 0)
        buttonLayout.addWidget(self.logButton, 0, 1)
        buttonLayout.addWidget(self.resetButton, 1, 0)
        buttonLayout.addWidget(self.cancelButton, 1, 1)
        buttonLayout.addWidget(self.saveButton, 2, 0, 1, 2)
        
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
    
    def loadCurrentValues(self):
        try:
            current_step = float(self.parent.stepmotor[0])
            self.stepSpinBox.setValue(current_step)
            self.butNegSpinBox.setValue(float(self.parent.buteNeg[0]))
            self.butPosSpinBox.setValue(float(self.parent.butePos[0]))
            self.parent.addLog("Config", "Valeurs actuelles chargées")
        except Exception as e:
            self.parent.addLog("ERROR Config", f"Erreur chargement: {e}")
            QMessageBox.warning(self, "Erreur", f"Erreur:\n{e}")
    
    def saveConfiguration(self):
        reply = QMessageBox.question(
            self, 
            'Sauvegarder la configuration ?',
            "⚠️ Attention! Modifier ces valeurs peut affecter le comportement du moteur.\n\n"
            "Voulez-vous vraiment sauvegarder ces paramètres ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                new_step = float(self.stepSpinBox.value())
                new_but_neg = float(self.butNegSpinBox.value())
                new_but_pos = float(self.butPosSpinBox.value())
                
                if new_but_neg >= new_but_pos:
                    QMessageBox.warning(self, "Erreur", 
                                      "La butée négative doit être inférieure à la butée positive!")
                    return
                
                if new_step <= 0:
                    QMessageBox.warning(self, "Erreur", 
                                      "Le step doit être supérieur à 0!")
                    return
                
                self.parent.stepmotor[0] = new_step
                self.parent.buteNeg[0] = new_but_neg
                self.parent.butePos[0] = new_but_pos
                self.parent.unit()
                self.motor.setStep(new_step)  
                self.motor.setButLogPlusValue(new_but_pos)
                self.motor.setButLogMoinsValue(new_but_neg)                    
                self.parent.addLog("Config", 
                    f"⚙️ Sauvegardé - Step: {new_step:.6f} µm, Butées: [{new_but_neg}, {new_but_pos}]")
                
                QMessageBox.information(self, "Succès", 
                                       "✅ Configuration sauvegardée!")
                self.close()
                
            except Exception as e:
                self.parent.addLog("ERROR Config", f"Erreur: {e}")
                QMessageBox.critical(self, "Erreur", f"Erreur:\n{e}")
    
    def closeEvent(self, event):
        self.isWinOpen = False
        event.accept()


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    mot1 = ONEMOTORGUI(IpAdress="10.0.1.30", NoMotor=12, showRef=False, unit=1, jogValue=100)
    mot1.show()
    mot1.startThread2()
    # mot2= ONEMOTORGUI(IpAdress="10.0.2.30", NoMotor = 2, showRef=False, unit=1,jogValue=100)
    # mot2.show()
    # mot2.startThread2()
    # mot3 = ONEMOTORGUI(IpAdress="10.0.2.30", NoMotor = 3, showRef=False, unit=1,jogValue=100)
    # mot3.show()
    # mot3.startThread2()
    # mot4 = ONEMOTORGUI(IpAdress="10.0.2.30", NoMotor = 4, showRef=False, unit=1,jogValue=100)
    # mot4.show()
    # mot4.startThread2()
    # mot5 = ONEMOTORGUI(IpAdress="10.0.2.30", NoMotor = 5, showRef=False, unit=1,jogValue=100)
    # mot5.show()
    # mot5.startThread2()
    appli.exec_()
