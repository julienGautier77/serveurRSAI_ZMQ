#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 15 December 2023

@author: Julien Gautier (LOA)
modified 01/08/2026
"""
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit, QToolButton
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QPushButton, QGridLayout, QDoubleSpinBox
from PyQt6.QtWidgets import QComboBox, QLabel, QCheckBox, QDialog, QTextEdit
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
import TirGui
from oneMotorGuiServerRSAI import ONEMOTORGUI

__version__ = __init__.__version__
__author__ = __init__. __author__


class THREEMOTORGUI(QWidget):
    """
    User interface Motor class : 
    MOTOGUI(str(mot1), str(motorTypeName),str(mot2), str(motorTypeName), nomWin,nomTilt,nomFoc,showRef,unit,unitFoc )
    mot0= lat  'name of the motor ' (child group of the ini file)
    mot1 =vert
    mot 2 =foc
    nonWin= windows name
    nonTilt =windows tilt name
    nomFoc= windows Focus name
    showRef True or False to show refWidget 
    unit= initial Unit of the two fisrt motors :
        0=sterp
        1=Micros
        2=mm
        3=ps
        4=degres
        unitFoc= unit of the third motors

    motorTypeName= Controler name  : 'RSAI' or 'A2V' or 'NewFocus' or 'SmartAct' or 'Newport' , Servo, Arduino

    fichier de config des moteurs : 'configMoteurRSAI.ini' 'configMoteurA2V.ini' 'configMoteurNewFocus.ini' 'configMoteurSmartAct.ini'


    """

    def __init__(self, IPLat, NoMotorLat, IPVert, NoMotorVert, IPFoc, NoMotorFoc, nomWin='', nomTilt='', nomFoc='', showRef=False, unit=1, unitFoc=1, jogValue=100, jogValueFoc=100, parent=None,invLat=False, invVert=False):

        super(THREEMOTORGUI, self).__init__()

        p = pathlib.Path(__file__)
        sepa = os.sep
        self.etat = 'ok'
        self.etatFoc_old = 'ok'
        self.etatVert_old = 'ok'
        self.etatLat_old = 'ok'
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.nomWin = nomWin
        self.iconPlay = self.icon+"playGreen.png"
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

        self.iconFlecheHaut = self.icon + "flechehaut.png"
        self.iconFlecheHaut = pathlib.Path(self.iconFlecheHaut)
        self.iconFlecheHaut = pathlib.PurePosixPath(self.iconFlecheHaut)

        self.iconFlecheBas = self.icon + "flechebas.png"
        self.iconFlecheBas = pathlib.Path(self.iconFlecheBas)
        self.iconFlecheBas = pathlib.PurePosixPath(self.iconFlecheBas)

        self.iconFlecheDroite = self.icon+"flechedroite.png"
        self.iconFlecheDroite = pathlib.Path(self.iconFlecheDroite)
        self.iconFlecheDroite = pathlib.PurePosixPath(self.iconFlecheDroite)

        self.iconFlecheGauche = self.icon+"flechegauche.png"
        self.iconFlecheGauche = pathlib.Path(self.iconFlecheGauche)
        self.iconFlecheGauche = pathlib.PurePosixPath(self.iconFlecheGauche)

        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.version = __version__

        self.nomTilt = nomTilt
        self.etatLat = 'ok'
        self.etatVert = 'ok'
        self.etatFoc = 'ok'
        self.configPath = str(p.parent)+sepa+"fichiersConfig"+sepa
        self.isWinOpen = False
       
        self.refShowId = showRef
        self.indexUnit = unit
        self.indexUnitFoc = unitFoc
        self.jogValue = jogValue
        self.jogValueFoc = jogValueFoc

        self.tir = TirGui.TIRGUI()

        self.LatWidget = ONEMOTORGUI(IPLat, NoMotorLat, nomWin='Control One Motor : ', showRef=False, unit=1)
        self.VertWidget = ONEMOTORGUI(IPVert, NoMotorVert, nomWin='Control One Motor : ', showRef=False, unit=1)
        self.FocWidget = ONEMOTORGUI(IPFoc, NoMotorFoc, nomWin='Control One Motor : ', showRef=False, unit=1)
        # log 
        self.actionLog = deque(maxlen=30)
        self.logWindow = None
        # Log initial
        self.addLog("Initialisation", f"Moteur {IPLat}:{NoMotorLat}")
        self.addLog("Initialisation", f"Moteur {IPVert}:{NoMotorVert}")
        self.addLog("Initialisation", f"Moteur {IPFoc}:{NoMotorFoc}")

        # self.refreshLog()
        
        self.inv = [invLat, invVert]  # Inversion des axes 
        # self.setWindowOpacity(0.95)
        self.MOT = [0, 0, 0]
        self.MOT[0] = self.LatWidget.MOT[0]
        self.MOT[1] = self.VertWidget.MOT[0]
        self.MOT[2] = self.FocWidget.MOT[0]

        self.stepmotor = [0, 0, 0]
        self.butePos = [0, 0, 0]
        self.buteNeg = [0, 0, 0]
        self.name = [0, 0, 0]
        
        for zzi in range(0, 3):
            self.stepmotor[zzi] = float((self.MOT[zzi].getStepValue()))   #  list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[zzi].getButLogPlusValue())   #  list 
            self.buteNeg[zzi] = float(self.MOT[zzi].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[0].getName())
        
        self.setWindowTitle(nomWin+'                     V.'+str(self.version))  # +' : '+ self.name[0])
       
        self.threadLat = PositionThread(self, mot=self.MOT[0])  # thread for displaying position Lat
        self.threadLat.POS.connect(self.PositionLat)
        time.sleep(0.121)
        self.threadVert = PositionThread(self, mot=self.MOT[1]) # thread for displaying  position Vert
        self.threadVert.POS.connect(self.PositionVert)
        time.sleep(0.153)
        self.threadFoc = PositionThread(self, mot=self.MOT[2])  # thread for displaying  position Foc
        self.threadFoc.POS.connect(self.PositionFoc)

        
        # # initialisation of the jog value 
        if self.indexUnitFoc == 0: #  step
            self.unitChangeFoc = 1
            self.unitNameFoc = 'step'
            
        if self.indexUnitFoc == 1:  # micron
            self.unitChangeFoc = float(self.stepmotor[2])
            self.unitNameFoc = 'um'
        if self.indexUnitFoc == 2: #  mm 
            self.unitChangeFoc = float(self.stepmotor[2]/1000)
            self.unitNameFoc = 'mm'
        if self.indexUnitFoc == 3:  #  ps  double passage : 1 microns=6fs
            self.unitChangeFoc = float(self.stepmotor[2]*0.0066666666) 
            self.unitNameFoc = 'ps'
        if self.indexUnitFoc == 4:  #  en degres
            self.unitChangeFoc = self.stepmotor[2]
            self.unitNameFoc = '°'

        if self.indexUnit == 0: # step
            self.unitChangeLat = 1
            self.unitChangeVert = 1
            self.unitNameTrans = 'step'
        if self.indexUnit == 1:  # micron
            self.unitChangeLat = float(self.stepmotor[0]) 
            self.unitChangeVert = float(self.stepmotor[1]) 
            self.unitNameTrans = 'um'
        if self.indexUnit == 2:
            self.unitChangeLat = float(self.stepmotor[0]/1000)
            self.unitChangeVert = float(self.stepmotor[1]/1000)
            self.unitNameTrans = 'mm'
        if self.indexUnit == 3:  #  ps  en compte le double passage : 1 microns=6fs
            self.unitChangeLat = float(self.stepmotor[0]*0.0066666666)  
            self.unitChangeVert = float(self.stepmotor[1]*0.0066666666)  
            self.unitNameTrans = 'ps'
        if self.unitChangeLat == 0:
            self.unitChangeLat = 1  # if / par 0
        if self.unitChangeVert == 0:
            self.unitChangeVert = 1  # if / 0

        self.setup()
        self.updateFromRSAI()
        self.unitFoc()
        self.unitTrans()
        self.jogStep.setValue(self.jogValue)
        self.jogStep_2.setValue(self.jogValueFoc)
        self.actionButton()

    def updateFromRSAI(self):
        # update from DB
        # to avoid to access to the database 
        for zzi in range(0, 2):
            # print('update')
            self.MOT[zzi].update()
            time.sleep(0.1)
            self.stepmotor[zzi] = float((self.MOT[zzi].getStepValue()))  # list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[zzi].getButLogPlusValue())  # list 
            self.buteNeg[zzi] = float(self.MOT[zzi].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[zzi].getName())
            
        self.setWindowTitle(self.nomWin)
        
        self.refValueLat = self.MOT[0].refValue
        self.refValueLatStep = [] # en step 
        for ref in self.refValueLat:
            self.refValueLatStep.append(ref /self.stepmotor [0])
        self.refValueLatStepOld = self.refValueLatStep.copy()
        self.refNameLat = self.MOT[0].refName
        self.refValueVert = self.MOT[1].refValue
        self.refValueVertStep = [] # en step 
        for ref in self.refValueVert:
            self.refValueVertStep.append(ref * self.stepmotor[1])
        self.refValueVertStepOld = self.refValueVertStep.copy()
        self.refNameVert = self.MOT[1].refName
        self.refValueFoc = self.MOT[2].refValue
        self.refValueFocStep = []  # en step 
        for ref in self.refValueFoc:
            self.refValueFocStep.append(ref /self.stepmotor[2])
        self.refValueFocStepOld = self.refValueFocStep.copy()

        self.refNameFoc = self.MOT[0].refName

        self.refNameLatOld = self.refNameLat.copy()
        self.refNameVertOld = self.refNameVert.copy()
        self.refNameFocOld = self.refNameFoc.copy()

        # update ref Name (ref name = ref La) and position ref value
        iii = 0
        for saveNameButton in self.posText: # reference name
            saveNameButton.textChanged.connect(self.savName)
            saveNameButton.setText(self.refNameLat[iii]) # print  ref name
            iii += 1
        eee = 0 
        for absButton in self.absLatRef:
            absButton.setValue(float(self.refValueLatStep[eee]* self.unitChangeLat))  # save reference lat  value
            eee += 1
        eee = 0    
        for absButton in self.absVertRef: 
            absButton.setValue(float(self.refValueVertStep[eee]*self.unitChangeVert))  # save reference vert value 
        eee = 0    
        for absButton in self.absFocRef: 
            absButton.setValue(float(self.refValueFocStep[eee]*self.unitChangeFoc))  # save reference foc value
            eee += 1

    def updateDB(self):
        #  update ref name and ref position to the Data base
        i = 0
        if (self.refNameLatOld != self.refNameLat):
            for ref in self.refNameLat:
                self.MOT[0].setRefName(i, ref)
                i += 1
        i = 0
        if (self.refNameVertOld != self.refNameVert):
            for ref in self.refNameVert:
                self.MOT[1].setRefName(i, ref)
                i += 1
        i = 0
        if (self.refNameFocOld != self.refNameFoc):
            for ref in self.refNameFoc:
                self.MOT[2].setRefName(i, ref)
                i += 1
        i = 0
        # print('update',self.refValueLatStep,self.refValueLatStepOld)      
        if self.refValueLatStep != self.refValueLatStepOld:
            for ref in self.refValueLatStep:
                ref = ref * float((self.stepmotor[0]))  # en micron
                a = self.MOT[0].setRefValue(i, int(ref))
                i += 1
        i = 0
        if self.refValueVertStep != self.refValueVertStepOld:  
            for ref in self.refValueVertStep: 
                ref = ref * float((self.stepmotor[1]))  # en micron
                a = self.MOT[1].setRefValue(i, int(ref))
                i += 1
        i = 0
        if self.refValueFocStep != self.refValueFocStepOld:
            for ref in self.refValueFocStep:
                ref = ref * float((self.stepmotor[2]))  # en micron
                a = self.MOT[2].setRefValue(i, int(ref))
                i += 1

    def startThread2(self):
        self.threadVert.ThreadINIT()
        self.threadVert.start()
        time.sleep(0.12)
        self.threadFoc.ThreadINIT()
        self.threadFoc.start()
        time.sleep(0.13)
        self.threadLat.ThreadINIT()
        self.threadLat.start()

    def setup(self):

        vbox1 = QVBoxLayout() 
        hboxTitre = QHBoxLayout()
        self.nomTilt = QLabel(self.nomTilt)
        self.nomTilt.setStyleSheet("font: bold 20pt;color:yellow")
        hboxTitre.addWidget(self.nomTilt)

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
        self.butNegButt = QCheckBox('But Neg', self)
        hboxTitre.addWidget(self.butNegButt)

        self.butPosButt = QCheckBox('But Pos', self)
        hboxTitre.addWidget(self.butPosButt)
        vbox1.addLayout(hboxTitre)

        hShoot = QHBoxLayout()

        self.updateButton = QToolButton()
        self.updateButton.setToolTip( "update from DB")
        self.updateButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconUpdate,self.iconUpdate))
        hShoot.addWidget(self.updateButton)
        vbox1.addLayout(hShoot)
        
        hLatBox = QHBoxLayout()
        hbox1 = QHBoxLayout()
        
        self.posLat = QPushButton('Lateral:')
        self.posLat.setStyleSheet("font: 12pt")
        self.posLat.setMaximumHeight(40)
        self.position_Lat = QLabel('12345667')
        self.position_Lat.setStyleSheet('font: bold 30pt;color:green')
        self.position_Lat.setMaximumHeight(40)
        self.enPosition_Lat = QLineEdit('?')
        self.enPosition_Lat.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.enPosition_Lat.setMaximumWidth(70)
        self.enPosition_Lat.setStyleSheet("font: bold 10pt")
        self.zeroButtonLat = QPushButton('Zero')
        self.zeroButtonLat.setMaximumWidth(30)
        self.zeroButtonLat.setMinimumWidth(30)
        hLatBox.addWidget(self.posLat)
        hLatBox.addWidget(self.position_Lat)
        hLatBox.addWidget(self.enPosition_Lat)
        hLatBox.addWidget(self.zeroButtonLat)
        hLatBox.addSpacing(25)

        hVertBox = QHBoxLayout()
        self.posVert = QPushButton('Vertical:')
        self.posVert.setStyleSheet("font: 12pt")
        self.posVert.setMaximumHeight(30)
        self.position_Vert = QLabel('1234556')
        self.position_Vert.setStyleSheet('font: bold 30pt;color:green')
        self.position_Vert.setMaximumHeight(40)
        self.enPosition_Vert = QLineEdit('?')
        self.enPosition_Vert.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.enPosition_Vert.setMaximumWidth(70)
        self.enPosition_Vert.setStyleSheet("font: bold 10pt")
        self.zeroButtonVert = QPushButton('Zero')
        self.zeroButtonVert.setMaximumWidth(30)
        self.zeroButtonVert.setMinimumWidth(30)

        hVertBox.addWidget(self.posVert)
        hVertBox.addWidget(self.position_Vert)
        hVertBox.addWidget(self.enPosition_Vert)
        hVertBox.addWidget(self.zeroButtonVert)
        hVertBox.addSpacing(25)

        vboxLatVert = QVBoxLayout() 
        vboxLatVert.addLayout(hLatBox)
        vboxLatVert.addLayout(hVertBox)

        hbox1.addLayout(vboxLatVert)

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

        self.gauche = QToolButton()
        self.gauche.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconFlecheGauche,self.iconFlecheGauche))
        self.gauche.setMaximumHeight(70)
        self.gauche.setMinimumWidth(70)
        self.gauche.setMaximumWidth(70)
        self.gauche.setMinimumHeight(70)
        self.droite = QToolButton()

        self.droite.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconFlecheDroite,self.iconFlecheDroite))
        self.droite.setMaximumHeight(70)
        self.droite.setMinimumWidth(70)
        self.droite.setMaximumWidth(70)
        self.droite.setMinimumHeight(70)

        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(10000)
        self.jogStep.setStyleSheet("font: bold 12pt")
        self.jogStep.setValue(100)
        self.jogStep.setMaximumWidth(120)
        self.jogStep.setValue(55)
        self.unitChangeLat = 1
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
        vbox1.addSpacing(10)

        hboxFoc = QHBoxLayout()
        self.posFoc = QPushButton('Foc:')
        self.posFoc.setMaximumHeight(30)
        self.posFoc.setStyleSheet("font: bold 12pt")
        self.position_Foc = QLabel('1234567')
        self.position_Foc.setStyleSheet('font: bold 30pt;color:green')
        self.position_Foc.setMaximumHeight(40)
        self.unitFocBouton = QComboBox()
        self.unitFocBouton.addItem('Step')
        self.unitFocBouton.addItem('um')
        self.unitFocBouton.addItem('mm')
        self.unitFocBouton.addItem('ps')
        self.unitFocBouton.setMinimumWidth(80)
        self.unitFocBouton.setStyleSheet("font: bold 12pt")
        self.unitFocBouton.setCurrentIndex(self.indexUnitFoc)

        self.enPosition_Foc = QLineEdit()
        self.enPosition_Foc.setMaximumWidth(60)
        self.enPosition_Foc.setStyleSheet("font: bold 10pt")
        self.enPosition_Foc.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.zeroButtonFoc = QPushButton('Zero')
        self.zeroButtonFoc.setMaximumWidth(30)
        self.zeroButtonFoc.setMinimumWidth(30)

        hboxFoc.addWidget(self.posFoc)

        hboxFoc.addWidget(self.position_Foc)
        hboxFoc.addWidget(self.unitFocBouton)
        hboxFoc.addWidget(self.enPosition_Foc)
        hboxFoc.addWidget(self.zeroButtonFoc)
        hboxFoc.addSpacing(25)

        self.moins = QToolButton()
        self.moins.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconMoins,self.iconMoins))
        self.moins.setMaximumWidth(70)
        self.moins.setMinimumHeight(70)
        hboxFoc.addWidget(self.moins)

        self.jogStep_2 = QDoubleSpinBox()
        self.jogStep_2.setMaximum(10000)
        self.jogStep_2.setStyleSheet("font: bold 12pt")
        self.jogStep_2.setValue(self.jogValueFoc)

        hboxFoc.addWidget(self.jogStep_2)

        self.plus = QToolButton()
        self.plus.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlus,self.iconPlus))

        self.plus.setMaximumWidth(70)
        self.plus.setMinimumHeight(70)

        hboxFoc.addWidget(self.plus)

        vbox1.addLayout(hboxFoc)
        vbox1.addSpacing(20)

        self.stopButton = QPushButton('STOP')
        self.stopButton.setStyleSheet("background-color: red")
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.stopButton)
        self.showRef = QPushButton('Show Ref')
        self.showRef.setMaximumWidth(70)
        hbox3.addWidget(self.showRef)
        
        self.logButton = QPushButton('📋 Log')
        self.logButton.setMaximumWidth(90)
        self.logButton.setStyleSheet("font: bold 10pt; color: #4a9eff;")
        self.logButton.setToolTip("Afficher l'historique des actions (30 dernières)")
        hbox3.addWidget(self.logButton)
        vbox1.addLayout(hbox3)

        self.REF1 = REF3M(num=1)
        self.REF2 = REF3M(num=2)
        self.REF3 = REF3M(num=3)
        self.REF4 = REF3M(num=4)
        self.REF5 = REF3M(num=5)
        self.REF6 = REF3M(num=6)

        grid_layoutRef = QGridLayout()
        grid_layoutRef.setVerticalSpacing(4)
        grid_layoutRef.setHorizontalSpacing(4)
        grid_layoutRef.addWidget(self.REF1, 0, 0)
        grid_layoutRef.addWidget(self.REF2, 0, 1)
        grid_layoutRef.addWidget(self.REF3, 0, 2)
        grid_layoutRef.addWidget(self.REF4, 1, 0)
        grid_layoutRef.addWidget(self.REF5, 1, 1)
        grid_layoutRef.addWidget(self.REF6, 1, 2)
       
        self.widget6REF = QWidget()
        self.widget6REF.setLayout(grid_layoutRef)
        vbox1.addWidget(self.widget6REF)
        self.setLayout(vbox1)
        self.absLatRef = [self.REF1.ABSLatref, self.REF2.ABSLatref, self.REF3.ABSLatref, self.REF4.ABSLatref, self.REF5.ABSLatref, self.REF6.ABSLatref]
        self.absVertRef = [self.REF1.ABSVertref, self.REF2.ABSVertref, self.REF3.ABSVertref, self.REF4.ABSVertref, self.REF5.ABSVertref, self.REF6.ABSVertref]
        self.absFocRef = [self.REF1.ABSFocref, self.REF2.ABSFocref, self.REF3.ABSFocref, self.REF4.ABSFocref, self.REF5.ABSFocref, self.REF6.ABSFocref]  # pour memoriser les positions
        self.posText = [self.REF1.posText, self.REF2.posText, self.REF3.posText, self.REF4.posText, self.REF5.posText, self.REF6.posText]
        self.POS = [self.REF1.Pos, self.REF2.Pos, self.REF3.Pos, self.REF4.Pos, self.REF5.Pos, self.REF6.Pos]
        self.Take = [self.REF1.take, self.REF2.take, self.REF3.take, self.REF4.take, self.REF5.take, self.REF6.take]
        self.jogStep_2.setFocus()
        self.refShow()

    def focusInEvent(self, event):
        # change refresh time when window in focus or not
        super().focusInEvent(event)
        self.thread.positionSleep = 0.05

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.thread.positionSleep = 1

    def actionButton(self):
        '''
           buttons action setup 
        '''
        self.unitFocBouton.currentIndexChanged.connect(self.unitFoc)  # Foc unit change
        self.unitTransBouton.currentIndexChanged.connect(self.unitTrans)  # Trans unit change
        
        self.haut.clicked.connect(self.hMove)  # jog up
        self.haut.setAutoRepeat(False)
        self.bas.clicked.connect(self.bMove)  # jog down
        self.bas.setAutoRepeat(False)
        self.gauche.clicked.connect(self.gMove)
        self.gauche.setAutoRepeat(False)
        self.droite.clicked.connect(self.dMove)
        self.droite.setAutoRepeat(False)

        self.plus.clicked.connect(self.pMove)  # jog + foc
        self.plus.setAutoRepeat(False)
        self.moins.clicked.connect(self.mMove)  # jog - fo
        self.moins.setAutoRepeat(False) 

        self.zeroButtonFoc.clicked.connect(self.ZeroFoc)  # reset display to 0
        self.zeroButtonLat.clicked.connect(self.ZeroLat)
        self.zeroButtonVert.clicked.connect(self.ZeroVert)

        self.stopButton.clicked.connect(self.StopMot)
        self.showRef.clicked.connect(self.refShow)

        self.posVert.clicked.connect(lambda: self.open_widget(self.VertWidget))
        self.posLat.clicked.connect(lambda: self.open_widget(self.LatWidget))
        self.posFoc.clicked.connect(lambda: self.open_widget(self.FocWidget))

        iii = 0
        for saveNameButton in self.posText:  # reference name
            saveNameButton.textChanged.connect(self.savName)
            saveNameButton.setText(self.refNameLat[iii])  # print  ref name
            iii += 1   
        for posButton in self.POS: # button GO
            posButton.clicked.connect(self.ref)    # go to reference value
        eee = 0
        for absButton in self.absLatRef: 
            absButton.setValue(float(self.refValueLatStep[eee]*self.unitChangeLat))  # save reference lat  value
            absButton.editingFinished.connect(self.savRefLat) # sauv value
            eee += 1
        eee = 0     
        for absButton in self.absVertRef: 
            absButton.setValue(float(self.refValueVertStep[eee]*self.unitChangeVert))  # save reference vert value 
            absButton.editingFinished.connect(self.savRefVert) # save  value
            eee += 1
        eee = 0    
        for absButton in self.absFocRef: 
            absButton.setValue(float(self.refValueFocStep[eee]*self.unitChangeFoc))  # save reference foc value
            absButton.editingFinished.connect(self.savRefFoc) #
            eee += 1
            
        for takeButton in self.Take:
            takeButton.clicked.connect(self.take)
            # take the value 
        
        self.updateButton.clicked.connect(self.update)
        self.logButton.clicked.connect(self.showLog)  # show log window

    def open_widget(self, fene):
        
        """ open new widget
        """
        if fene.isWinOpen is False:
            # New widget"
            fene.show()
            fene.startThread2()
            fene.isWinOpen = True
        else:
            # fene.activateWindow()
            fene.raise_()
            fene.showNormal()  
            
    def refShow(self):
        
        if self.refShowId is True:
            # print(self.geometry())
            # self.resize(368, 345)
            self.widget6REF.show()
            self.refShowId = False
            self.showRef.setText('Hide Ref')
            self.setFixedSize(750, 800)
            
        else:
            # print(self.geometry())
            self.widget6REF.hide()
            self.refShowId = True

            self.showRef.setText('Show Ref')
            self.setFixedSize(750, 450)
            #self.updateGeometry()      
    
    def pMove(self):
        '''
        action jog + foc
        '''
        a = float(self.jogStep_2.value())
        a = float(a/self.unitChangeFoc)
        b = self.MOT[2].position()

        if b+a > self.butePos[2] :
            print("STOP : Positive switch")
            self.MOT[2].stopMotor()
            self.butPosButt.setChecked(True)
            self.butPosButt.setStyleSheet('color:red')
        else:
            self.MOT[2].rmove(a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butNegButt.setStyleSheet("")
            self.butPosButt.setStyleSheet("")
            self.addLog("rmove", f"{self.MOT[2].name}{' +'}{a:.2f} "
                        f"{self.unitNameFoc}{' position avant mvt :'} {self.PosFoc} {self.unitNameFoc}")
            # self.refreshLog()

    def mMove(self): 
        '''
        action jog - foc
        '''
        a = float(self.jogStep_2.value())
        a = float(a/self.unitChangeFoc)
        b = self.MOT[2].position()
        if b - a < self.buteNeg[2]:
            print("STOP : Negative switch")
            self.MOT[2].stopMotor()
            self.butNegButt.setChecked(True)
            self.butNegButt.setStyleSheet('color:red')
        else:
            self.MOT[2].rmove(-a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butNegButt.setStyleSheet('')
            self.butNegButt.setStyleSheet('')
            self.addLog("rmove", f"{self.MOT[2].name}{' -'}{a:.2f} "
                        f"{self.unitNameFoc}{' position avant mvt :'} {self.PosFoc} {self.unitNameFoc}")
            # self.refreshLog()

    def gMove(self):
        '''
        action bouton left -
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChangeLat)
        b = self.MOT[0].position()
        if self.inv[0] is False:
            if b - a < self.buteNeg[0]:
                print("STOP : Butée Negative")
                self.MOT[0].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
            else: 
                self.MOT[0].rmove(-a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('') 
        else:  # inv true on fait +
            if b + a > self.butePos[0]:
                print("STOP : Butée Pos")
                self.MOT[0].stopMotor()
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
            else:
                self.MOT[0].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('') 
                self.addLog("rmove", f"{self.MOT[0].name}{' -'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosLat} {self.unitNameTrans}")
                # self.refreshLog()
      
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
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.MOT[0].stopMotor()
            else: 
                self.MOT[0].rmove(+a) 
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("rmove", f"{self.MOT[0].name}{' +'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosLat} {self.unitNameTrans}")
                # self.refreshLog()
        else: # on fait du moins 
            if b - a < self.buteNeg[0]:
                print("STOP : Butée Negative")
                self.MOT[0].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
            else:
                self.MOT[0].rmove(-a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('') 
                self.addLog("rmove", f"{self.MOT[0].name}{' -'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosLat} {self.unitNameTrans}")
                # self.refreshLog()

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
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
            else:
                self.MOT[1].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('') 
                self.addLog("rmove", f"{self.MOT[1].name}{' +'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosVert} {self.unitNameTrans}")
                # self.refreshLog()
        else: # - 
            if b - a < self.buteNeg[1]:
                print("STOP : Butée Negative")
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
            else: 
                self.MOT[1].rmove(-a)
                self.butNegButt.setChecked(False)
                self.butPosButt.setChecked(False) 
                self.butNegButt.setStyleSheet('')
                self.butPosButt.setStyleSheet('')
                self.addLog("rmove", f"{self.MOT[1].name}{' -'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosVert} {self.unitNameTrans}")
                # self.refreshLog()

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
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
            else:
                self.MOT[1].rmove(-a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("rmove", f"{self.MOT[1].name}{' -'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosVert} {self.unitNameTrans}")
                # self.refreshLog() 
        else:
            if b + a > self.butePos[1]:
                print("STOP : Butée Positive")
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
            else:
                self.MOT[1].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('') 
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('') 
                self.addLog("rmove", f"{self.MOT[1].name}{' +'}{a:.2f} "
                        f"{self.unitNameTrans}{' position avant mvt :'} {self.PosVert} {self.unitNameTrans}")
                #  self.refreshLog()
        
    def ZeroLat(self):  # zero
        self.MOT[0].setzero()
        self.addLog("Set Zero", f"{self.MOT[0].name}{' position avant remise à zero : '} {self.PosLat} {self.unitTrans}")
        #  self.refreshLog()

    def ZeroVert(self):  # zero
        self.MOT[1].setzero()
        self.addLog("Set Zero", f"{self.MOT[1].name}{' position avant remise à zero : '} {self.PosVert} {self.unitTrans}")
        #  self.refreshLog()

    def ZeroFoc(self):  # zero
        self.MOT[2].setzero()
        self.addLog("Set Zero", f"{self.MOT[2].name}{' position avant remise à zero : '} {self.PosFoc} {self.unitFoc}")
        #  self.refreshLog()

    def RefMark(self):
        """
            todo ....
        """
        # self.motorType.refMark(self.motor)
   
    def unitFoc(self):
        '''
        unit change mot foc
        '''
        self.indexUnitFoc = self.unitFocBouton.currentIndex()
        valueJog_2 = self.jogStep_2.value() / self.unitChangeFoc
        
        if self.indexUnitFoc == 0:  # step
            self.unitChangeFoc = 1
            self.unitNameFoc = 'step'
        if self.indexUnitFoc == 1:  # micron
            self.unitChangeFoc = float(self.stepmotor[2])  
            self.unitNameFoc = 'um'
        if self.indexUnitFoc == 2:  # mm 
            self.unitChangeFoc = float(self.stepmotor[2]/1000)
            self.unitNameFoc = 'mm'
        if self.indexUnitFoc == 3:  # ps  double passage : 1 microns=6fs
            self.unitChangeFoc = float(self.stepmotor[2]*0.0066666666)
            self.unitNameFoc = 'ps'
        if self.unitChangeFoc == 0:
            self.unitChangeFoc = 1  # avoid 0

        self.jogStep_2.setValue(valueJog_2*self.unitChangeFoc)
        self.jogStep_2.setSuffix(" %s" % self.unitNameFoc)
        eee = 0
        for absButton in self.absFocRef: 
            nbRef = eee
            absButton.setValue(float(self.refValueFocStep[nbRef])*self.unitChangeFoc)  # save reference foc value
            absButton.setSuffix(" %s" % self.unitNameFoc)
            eee += 1
        
    def unitTrans(self):
        '''
         unit change mot foc
        '''
        valueJog = self.jogStep.value()/self.unitChangeLat
        self.indexUnit = self.unitTransBouton.currentIndex()
        if self.indexUnit == 0:  # step
            self.unitChangeLat = 1
            self.unitChangeVert = 1
            self.unitNameTrans = 'step'
        if self.indexUnit == 1:  # micron
            self.unitChangeLat = float(self.stepmotor[0])
            self.unitChangeVert = float(self.stepmotor[1])
            self.unitNameTrans = 'um'
        if self.indexUnit == 2:
            self.unitChangeLat = float(self.stepmotor[0]/1000)
            self.unitChangeVert = float(self.stepmotor[1]/1000)
            self.unitNameTrans = 'mm'
        if self.indexUnit == 3:  # ps  en compte le double passage : 1 microns=6fs
            self.unitChangeLat = float(self.stepmotor[0]*0.0066666666)  
            self.unitChangeVert = float(self.stepmotor[1]*0.0066666666)  
            self.unitNameTrans = 'ps'
        if self.unitChangeLat == 0:
            self.unitChangeLat = 1  # if / par 0
        if self.unitChangeVert == 0:
            self.unitChangeVert = 1  # if / 0

        self.jogStep.setValue(valueJog*self.unitChangeLat)
        self.jogStep.setSuffix(" %s" % self.unitNameTrans)

        eee = 0
        for absButton in self.absLatRef:
            nbRef = eee
            absButton.setValue(float(self.refValueLatStep[nbRef])*self.unitChangeLat)  # save reference lat  value
            absButton.setSuffix(" %s" % self.unitNameTrans)
            eee += 1
        eee = 0
        for absButton in self.absVertRef:
            nbRef = eee
            absButton.setValue(float(self.refValueVert[nbRef])*self.unitChangeVert) #save reference vert value 
            absButton.setSuffix(" %s" % self.unitNameTrans)
            eee += 1

    def StopMot(self):
        '''
        stop all motors
        '''
        for zzi in range(0, 3):
            self.MOT[zzi].stopMotor()
            self.addLog("STOP moteur", f"{self.MOT[zzi].name} Arrêt du moteur demandé")
            #  self.refreshLog()

    def EtatLat(self, etat):
        self.etatLat = etat

    def EtatVert(self, etat):
        #  print(etat)
        self.etatVert = etat

    def EtatFoc(self, etat):
        self.etatFoc = etat

    @pyqtSlot(object)
    def PositionLat(self, Posi):
        ''' 
        Position Lat  display with the second thread
        '''

        self.PosLat = Posi[0]
        self.etatLat = str(Posi[1])
        a = float(self.PosLat)
        b = a  # value in step
        a = a * self.unitChangeLat  # value with unit changed
        self.position_Lat.setText(str(round(a, 2)))
        self.position_Lat.setStyleSheet('font: bold 30pt;color:green')

        if self.etatLat_old != self.etatLat:
            self.etatLat_old = self.etatLat
            if self.etatLat == 'FDC-':
                self.enPosition_Lat.setText('FDC -')
                self.enPosition_Lat.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatLat == 'FDC+':
                self.enPosition_Lat.setText('FDC +')
                self.enPosition_Lat.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatLat == 'Poweroff':
                self.enPosition_Lat.setText('Power Off')
                self.enPosition_Lat.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatLat == 'mvt':
                self.enPosition_Lat.setText('Mvt')
                self.enPosition_Lat.setStyleSheet('font: bold 12pt;color:white')
            elif self.etat == 'notconnected':
                self.enPosition_Lat.setText('python server Not connected')
                self.enPosition_Lat.setStyleSheet('font: bold 8pt;color:red')
            elif self.etat == 'errorConnect':
                self.enPosition_Lat.setText('equip Not connected')
                self.enPosition_Lat.setStyleSheet('font: bold 8pt;color:red')

        positionConnue_Lat = 0 
        precis = 5
        if (self.etatLat == 'ok' or self.etatLat == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue_Lat == 0:
                    
                    if float(self.refValueLatStep[nbRefInt-1]) - precis < b < float(self.refValueLatStep[nbRefInt-1]) + precis:
                        self.enPosition_Lat.setText(str(self.refNameLat[nbRefInt-1]))
                        positionConnue_Lat = 1

        if positionConnue_Lat == 0 and (self.etatLat == 'ok' or self.etatLat == '?'):
            self.enPosition_Lat.setText('')
    
    @pyqtSlot(object)        
    def PositionVert(self, Posi):
        ''' 
        Position Vert  displayed with the second thread
        '''
        self.PosVert = Posi[0]
        self.etatVert = str(Posi[1])
        a = float(self.PosVert)
        b = a #  value in step 
        a = a * self.unitChangeVert  # value  with unit changed
        self.position_Vert.setText(str(round(a, 2)))
        self.position_Vert.setStyleSheet('font: bold 30pt;color:green')
        if self.etatVert != self.etatVert_old:
            self.etatVert_old = self.etatVert
            if self.etatVert == 'FDC-':
                self.enPosition_Vert.setText('FDC -')
                self.enPosition_Vert.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatVert == 'FDC+':
                self.enPosition_Vert.setText('FDC +')
                self.position_Vert.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatVert == 'Poweroff':
                self.enPosition_Vert.setText('Power Off')
                self.enPosition_Vert.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatVert == 'mvt':
                self.enPosition_Vert.setText('Mvt')
                self.enPosition_Vert.setStyleSheet('font: bold 12pt;color:white')
            elif self.etat == 'notconnected':
                self.enPosition_Vert.setText('python server Not connected')
                self.enPosition_Vert.setStyleSheet('font: bold 8pt;color:red')
            elif self.etat == 'errorConnect':
                self.enPosition_Vert.setText('equip Not connected')
                self.enPosition_Vert.setStyleSheet('font: bold 8pt;color:red')   
            
        positionConnue_Vert = 0
        precis = 5
        if (self.etatVert == 'ok' or self.etatVert == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue_Vert == 0:
                    if float(self.refValueVertStep[nbRefInt-1]) - precis < b < float(self.refValueVertStep[nbRefInt-1]) + precis:
                        self.enPosition_Vert.setText(str(self.refNameVert[nbRefInt-1]))
                        positionConnue_Vert = 1
        if positionConnue_Vert == 0 and (self.etatVert == 'ok' or self.etatVert == '?'):
            self.enPosition_Vert.setText(' ')

    @pyqtSlot(object)     
    def PositionFoc(self, Posi):
        '''
        Position Foc  displayed with the second thread
        '''
        self.PosFoc = Posi[0]
        self.etatFoc = str(Posi[1])
        a = float(self.PosFoc)
        b = a  #  value in step
        a = a * self.unitChangeFoc
        self.position_Foc.setText(str(round(a, 2))) 
        self.position_Foc.setStyleSheet('font: bold 30pt;color:green')
        if self.etatFoc != self.etatFoc_old:
            self.etatFoc_old = self.etatFoc
            if self.etatFoc == 'FDC-':
                self.enPosition_Foc.setText('FDC -')
                self.enPosition_Foc.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatFoc == 'FDC+':
                self.enPosition_Foc.setText('FDC +')
                self.enPosition_Foc.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatFoc == 'Poweroff':
                self.enPosition_Foc.setText('Power Off')
                self.enPosition_Foc.setStyleSheet('font: bold 12pt;color:red')
            elif self.etatFoc == 'mvt':
                self.enPosition_Foc.setText('Mvt')
                self.enPosition_Foc.setStyleSheet('font: bold 12pt;color:white')
            elif self.etat == 'notconnected':
                self.enPosition_Foc.setText('python server Not connected')
                self.enPosition_Foc.setStyleSheet('font: bold 8pt;color:red')
            elif self.etat == 'errorConnect':
                self.enPosition_Foc.setText('equip Not connected')
                self.enPosition_Foc.setStyleSheet('font: bold 8pt;color:red')

        positionConnue_Foc = 0
        precis = 5
        if (self.etatFoc == 'ok' or self.etatFoc == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue_Foc == 0:
                    if float(self.refValueFocStep[nbRefInt-1]) - precis < b < float(self.refValueFocStep[nbRefInt-1]) + precis: #self.MOT[0].getRefValue
                        self.enPosition_Foc.setText(str(self.refNameFoc[nbRefInt-1]))
                        positionConnue_Foc = 1   
        if positionConnue_Foc == 0 and (self.etatFoc == 'ok' or self.etatFoc == '?'):
            self.enPosition_Foc.setText(' ')

    def take(self):
        '''
        take and save the reference
        '''
        sender = QtCore.QObject.sender(self)  # take the name of  the button 
        #  print ('sender name',sender)
        reply = QMessageBox.question(None, 'Save Position ?', "Do you want to save this position ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            tposLat = self.MOT[0].position()
            nbRef = str(sender.objectName()[0])
            #  print('ref',nbRef)
            self.refValueLatStep[int(nbRef)-1] = tposLat
            self.absLatRef[int(nbRef)-1].setValue(tposLat*self.unitChangeLat)
            print("Position Lat saved", self.refValueLat)
            self.addLog("Reference value", f" saved value ref Lat {nbRef} : {self.absLatRef[int(nbRef)-1].value()}{self.unitNameTrans}")
            
            tposVert = self.MOT[1].position()
            self.refValueVertStep[int(nbRef)-1] = tposVert
            self.absVertRef[int(nbRef)-1].setValue(tposVert*self.unitChangeVert)
            print("Position Vert saved")
            self.addLog("Reference value", f" saved value ref Vert  {nbRef} : {self.absVertRef[int(nbRef)-1].value()}{self.unitNameTrans}")
            tposFoc = self.MOT[2].position()
            print('tposFoc', tposFoc)
            self.refValueFocStep[int(nbRef)-1] = tposFoc
            self.absFocRef[int(nbRef)-1].setValue(tposFoc*self.unitChangeFoc)
            self.addLog("Reference value", f"  saved value ref Foc' {nbRef} : {self.absVertRef[int(nbRef)-1].value()}{self.unitNameFoc}")
            print("Position Foc saved")
            #  self.refreshLog()

    def ref(self):
        '''
        Move the motor to the reference value in step : GO button
        Fait bouger le moteur a la valeur de reference en step : bouton Go 
        '''
        sender = QtCore.QObject.sender(self)
        reply = QMessageBox.question(None, 'Go to this Position ?', "Do you want to GO to this position ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nbRef = int(sender.objectName()[0])
            vref = []
            vref.append(int(self.refValueLatStep[nbRef-1]))
            vref.append(int(self.refValueVertStep[nbRef-1]))
            vref.append(int(self.refValueFocStep[nbRef-1]))
            #  print('vref mov',vref)
            for i in range(0, 3):
                #  print(i)
                
                if vref[i] < self.buteNeg[i]:
                    print("STOP : negative switch")
                    self.butNegButt.setChecked(True)
                    self.butNegButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()

                elif vref[i] > self.butePos[i]:
                    print("STOP : positive switch")
                    self.butPosButt.setChecked(True)
                    self.butPosButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                else:
                    time.sleep(0.2)
                    self.MOT[i].move(vref[i])
                    self.addLog("Reference ", f" move to ref {nbRef} : {vref[i]} {self.unitNameTrans if i < 2 else self.unitNameFoc}")
                    #  self.refreshLog()
                    time.sleep(1)
                    self.butNegButt.setChecked(False)
                    self.butPosButt.setChecked(False) 
                    self.butNegButt.setStyleSheet('')
                    self.butPosButt.setStyleSheet('')

    def savName(self):
        '''
        Save reference name
        '''
        sender = QtCore.QObject.sender(self)
        #  print('sender',sender.objectName())
        nbRef = int(sender.objectName()[0])  # PosTExt1
        vname = self.posText[int(nbRef)-1].text()
        
        self.refNameLat[nbRef-1] = str(vname)
        self.refNameVert[nbRef-1] = str(vname)
        self.refNameFoc[nbRef-1] = str(vname)

    def savRefLat(self):
        '''
        save reference lat value
        '''
        sender = QtCore.QObject.sender(self)
        nbRefLat = sender.objectName()[0]  #  nom du button ABSref1
        vrefLat = int(self.absLatRef[int(nbRefLat)-1].value())
        self.refValueLatStep[int(nbRefLat)-1] = vrefLat/self.unitChangeLat  # on sauvegarde en step dans la base donnee 

    def savRefVert(self):
        '''
        save reference Vert value
        '''
        sender = QtCore.QObject.sender(self)
        nbRefVert = sender.objectName()[0] 
        vrefVert = int(self.absVertRef[int(nbRefVert)-1].value())
        self.refValueVertStep[int(nbRefVert)-1] = vrefVert/self.unitChangeVert # on sauvegarde en step dans la base donnee 

    def savRefFoc(self):
        '''
        save reference Foc value
        '''
        sender = QtCore.QObject.sender(self)
        nbRefFoc = sender.objectName()[0] 
        vrefFoc = int(self.absFocRef[int(nbRefFoc)-1].value())
        self.refValueFocStep[int(nbRefFoc)-1] = vrefFoc/self.unitChangeFoc  # on sauvegarde en step dans la base donnee 

    def ShootAct(self):
        self.tir.TirAct()

    def addLog(self, action, details=""):
        """Ajoute une action au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        self.actionLog.append(log_entry)
        print(f"[LOG] {timestamp}   {action} {details}")
    
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
        time.sleep(0.1)
        event.accept()

    def fini(self):
        '''
        a the end we close all the thread
        '''
        self.threadLat.stopThread()
        self.threadVert.stopThread()
        self.threadFoc.stopThread()
        self.isWinOpen = False
        time.sleep(0.1)
        
        self.updateDB()
        time.sleep(0.2)


class REF3M(QWidget):
    
    def __init__(self, num=0, parent=None):
        QtCore.QObject.__init__(self)
        super(REF3M, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.id = num
        
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        
        self.wid =  QWidget()
        self.vboxPos = QVBoxLayout()
        self.posText = QLineEdit('ref')
        self.posText.setStyleSheet("font: bold 15pt")
        self.posText.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.posText.setObjectName('%s' % self.id)
        self.vboxPos.addWidget(self.posText)
        self.iconTake = self.icon+"disquette.png"
        self.iconTake = pathlib.Path(self.iconTake)
        self.iconTake = pathlib.PurePosixPath(self.iconTake)
        self.take = QToolButton()
        self.take.setObjectName('%s' % self.id)
        self.take.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconTake,self.iconTake))
        self.take.setMaximumWidth(30)
        self.take.setMinimumWidth(30)
        self.take.setMinimumHeight(30)
        self.take.setMaximumHeight(30)
        self.takeLayout = QHBoxLayout()
        self.takeLayout.addWidget(self.take)
        self.iconGo = self.icon+"go.png"
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
        
        LabeLatref = QLabel('Lat:')
        self.ABSLatref = QDoubleSpinBox()
        self.ABSLatref.setObjectName('%s' % self.id)
        self.ABSLatref.setMaximum(5000000000)
        self.ABSLatref.setMinimum(-5000000000)
        
        LabelVertref = QLabel('Vert:')
        self.ABSVertref = QDoubleSpinBox()
        self.ABSVertref.setObjectName('%s' % self.id)
        self.ABSVertref.setMaximum(5000000000)
        self.ABSVertref.setMinimum(-5000000000)
        
        LabelFocref = QLabel('Foc:')
        self.ABSFocref = QDoubleSpinBox()
        self.ABSFocref.setObjectName('%s' % self.id)
        self.ABSFocref.setMaximum(5000000000)
        self.ABSFocref.setMinimum(-5000000000)
        
        grid_layoutPos = QGridLayout()
        grid_layoutPos.setVerticalSpacing(5)
        grid_layoutPos.setHorizontalSpacing(10)
        grid_layoutPos.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        grid_layoutPos.addLayout(self.takeLayout, 0, 0)
        grid_layoutPos.addLayout(self.PosLayout, 0, 1)
        grid_layoutPos.addWidget(LabeLatref, 1, 0)
        grid_layoutPos.addWidget(self.ABSLatref, 1, 1)
        grid_layoutPos.addWidget(LabelVertref, 2, 0)
        grid_layoutPos.addWidget(self.ABSVertref, 2, 1)
        grid_layoutPos.addWidget(LabelFocref, 3, 0)
        grid_layoutPos.addWidget(self.ABSFocref, 3, 1)
        self.vboxPos.addLayout(grid_layoutPos)

        self.wid.setStyleSheet("background-color: rgb(60, 77, 87)")
        self.wid.setLayout(self.vboxPos)

        mainVert = QVBoxLayout()
        mainVert.addWidget(self.wid)
        mainVert.setContentsMargins(0, 0, 0, 0)
        self.setLayout(mainVert)


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    import time 
    POS = QtCore.pyqtSignal(object)  # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mot=''):
        super(PositionThread, self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False
        self.etat_old = ""
        self.Posi_old = 0
        self.positionSleep = 0.05

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                Posi = (self.MOT.position())
                time.sleep(self.positionSleep)
                # try :
                time.sleep(0.01)
                etat = self.MOT.etatMotor()
                # time.sleep(0.1)
                if self.Posi_old != Posi or self.etat_old != etat:  #  on emet que si different
                    self.POS.emit([Posi, etat])

    def ThreadINIT(self):
        self.stop = False
   
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        # self.terminate()


class LogWindow(QDialog):
    """
    Fenêtre de visualisation des logs
    Affiche les 30 dernières actions du moteur
    """
    
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.setWindowTitle("📋 Historique des Actions")
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Titre
        title = QLabel("Dernières actions (max 30)")
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
            else:
                color = "#aaaaaa"  # Gris pour le reste
                icon = "•"
            
            html += f'<span style="color: #888;">[{timestamp}]</span> '
            html += f'<span style="color: {color}; font-weight: bold;">{icon} {action}</span>'
            
            if details:
                html += f' <span style="color: #ccc;">- {details}</span>'
            
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


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    mot = THREEMOTORGUI(IPVert='10.0.1.30', NoMotorVert=12, IPLat='10.0.1.30', NoMotorLat=13, IPFoc='10.0.1.30', NoMotorFoc=14, nomWin = 'JET rosa', invLat=True, invVert=True)
    mot.show()
    mot.startThread2()
    appli.exec_()
