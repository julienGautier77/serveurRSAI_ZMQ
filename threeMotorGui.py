#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 15 December 2023
Modified on 30 January 2026

@author: Julien Gautier (LOA)
Interface modernisée avec style cohérent (3 moteurs)
"""
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit, QToolButton
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QPushButton, QGridLayout, QDoubleSpinBox
from PyQt6.QtWidgets import QComboBox, QLabel, QCheckBox, QDialog, QTextEdit, QGroupBox
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
from oneMotorGui import ONEMOTORGUI

__version__ = __init__.__version__
__author__ = __init__.__author__


class THREEMOTORGUI(QWidget):
    """
    Interface modernisée pour contrôle de 3 moteurs
    """

    def __init__(self, IPLat, NoMotorLat, IPVert, NoMotorVert, IPFoc, NoMotorFoc, 
                 nomWin='', nomTilt='', nomFoc='', showRef=False, unit=1, unitFoc=1, 
                 jogValue=100, jogValueFoc=100, parent=None, invLat=False, invVert=False):

        super(THREEMOTORGUI, self).__init__()

        p = pathlib.Path(__file__)
        sepa = os.sep
        self.etat = 'ok'
        self.etatFoc_old = 'ok'
        self.etatVert_old = 'ok'
        self.etatLat_old = 'ok'
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.nomWin = nomWin
        
        # Icons
        self.iconPlay = pathlib.PurePosixPath(pathlib.Path(self.icon + "playGreen.png"))
        self.iconMoins = pathlib.PurePosixPath(pathlib.Path(self.icon + "moinsBleu.png"))
        self.iconPlus = pathlib.PurePosixPath(pathlib.Path(self.icon + "plusBleu.png"))
        self.iconStop = pathlib.PurePosixPath(pathlib.Path(self.icon + "close.png"))
        self.iconUpdate = pathlib.PurePosixPath(pathlib.Path(self.icon + "recycle.png"))
        self.iconFlecheHaut = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechehaut.png"))
        self.iconFlecheBas = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechebas.png"))
        self.iconFlecheDroite = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechedroite.png"))
        self.iconFlecheGauche = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechegauche.png"))
        self.iconRef = pathlib.PurePosixPath(pathlib.Path(self.icon + "ref.png"))

        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.version = __version__

        self.nomTilt = nomTilt
        self.etatLat = 'ok'
        self.etatVert = 'ok'
        self.etatFoc = 'ok'
        self._positionLatStep = 0
        self._positionVertStep = 0
        self._positionFocStep =0

        self.configPath = str(p.parent) + sepa + "fichiersConfig"+sepa
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
        
        # Log
        self.actionLog = deque(maxlen=30)
        self.logWindow = None
        
        # Log initial
        self.addLog("Initialisation", f"✅ Moteur {IPLat}:{NoMotorLat}")
        self.addLog("Initialisation", f"✅ Moteur {IPVert}:{NoMotorVert}")
        self.addLog("Initialisation", f"✅ Moteur {IPFoc}:{NoMotorFoc}")

        self.inv = [invLat, invVert]
        self.MOT = [0, 0, 0]
        self.MOT[0] = self.LatWidget.MOT[0]
        self.MOT[1] = self.VertWidget.MOT[0]
        self.MOT[2] = self.FocWidget.MOT[0]

        self.stepmotor = [0, 0, 0]
        self.butePos = [0, 0, 0]
        self.buteNeg = [0, 0, 0]
        self.name = [0, 0, 0]
        
        for zzi in range(0, 3):
            self.stepmotor[zzi] = float((self.MOT[zzi].getStepValue()))
            self.butePos[zzi] = float(self.MOT[zzi].getButLogPlusValue())
            self.buteNeg[zzi] = float(self.MOT[zzi].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[0].getName())
        
        self.setWindowTitle(nomWin + '  V.' + str(self.version))
       
        self.threadLat = PositionThread(self, mot=self.MOT[0])
        self.threadLat.POS.connect(self.PositionLat)
        time.sleep(0.01)
        self.threadVert = PositionThread(self, mot=self.MOT[1])
        self.threadVert.POS.connect(self.PositionVert)
        time.sleep(0.01)
        self.threadFoc = PositionThread(self, mot=self.MOT[2])
        self.threadFoc.POS.connect(self.PositionFoc)

        self.threadEtatLat = EtatThread(self, mot=self.MOT[0])
        self.threadEtatLat.ETAT.connect(self.EtatLat)
        time.sleep(0.01)
        self.threadEtatVert = EtatThread(self, mot=self.MOT[1])
        self.threadEtatVert.ETAT.connect(self.EtatVert)
        time.sleep(0.01)
        self.threadEtatFoc = EtatThread(self, mot=self.MOT[2])
        self.threadEtatFoc.ETAT.connect(self.EtatFoc)

        # Initialisation des unités
        if self.indexUnitFoc == 0:
            self.unitChangeFoc = 1
            self.unitNameFoc = 'step'
        elif self.indexUnitFoc == 1:
            self.unitChangeFoc = float(self.stepmotor[2])
            self.unitNameFoc = 'um'
        elif self.indexUnitFoc == 2:
            self.unitChangeFoc = float(self.stepmotor[2]/1000)
            self.unitNameFoc = 'mm'
        elif self.indexUnitFoc == 3:
            self.unitChangeFoc = float(self.stepmotor[2]*0.0066666666)
            self.unitNameFoc = 'ps'
        elif self.indexUnitFoc == 4:
            self.unitChangeFoc = self.stepmotor[2]
            self.unitNameFoc = '°'

        if self.indexUnit == 0:
            self.unitChangeLat = 1
            self.unitChangeVert = 1
            self.unitNameTrans = 'step'
        elif self.indexUnit == 1:
            self.unitChangeLat = float(self.stepmotor[0])
            self.unitChangeVert = float(self.stepmotor[1])
            self.unitNameTrans = 'um'
        elif self.indexUnit == 2:
            self.unitChangeLat = float(self.stepmotor[0]/1000)
            self.unitChangeVert = float(self.stepmotor[1]/1000)
            self.unitNameTrans = 'mm'
        elif self.indexUnit == 3:
            self.unitChangeLat = float(self.stepmotor[0]*0.0066666666)
            self.unitChangeVert = float(self.stepmotor[1]*0.0066666666)
            self.unitNameTrans = 'ps'
            
        if self.unitChangeLat == 0:
            self.unitChangeLat = 1
        if self.unitChangeVert == 0:
            self.unitChangeVert = 1

        self.setup()
        self.updateFromRSAI()
        self.unitFoc()
        self.unitTrans()
        self.jogStep.setValue(self.jogValue)
        self.jogStep_2.setValue(self.jogValueFoc)
        self.actionButton()

    def updateFromRSAI(self):
        for zzi in range(0, 3):
            self.MOT[zzi].update()
            time.sleep(0.1)
            self.stepmotor[zzi] = float((self.MOT[zzi].getStepValue()))
            self.butePos[zzi] = float(self.MOT[zzi].getButLogPlusValue())
            self.buteNeg[zzi] = float(self.MOT[zzi].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[zzi].getName())
            
        self.setWindowTitle(self.nomWin)
        
        self.refValueLat = self.MOT[0].refValue
        self.refValueLatStep = []
        for ref in self.refValueLat:
            self.refValueLatStep.append(ref / self.stepmotor[0])
        self.refValueLatStepOld = self.refValueLatStep.copy()
        self.refNameLat = self.MOT[0].refName
        
        self.refValueVert = self.MOT[1].refValue
        self.refValueVertStep = []
        for ref in self.refValueVert:
            self.refValueVertStep.append(ref / self.stepmotor[1])
        self.refValueVertStepOld = self.refValueVertStep.copy()
        self.refNameVert = self.MOT[1].refName
        
        self.refValueFoc = self.MOT[2].refValue
        self.refValueFocStep = []
        for ref in self.refValueFoc:
            self.refValueFocStep.append(ref / self.stepmotor[2])
        self.refValueFocStepOld = self.refValueFocStep.copy()
        self.refNameFoc = self.MOT[2].refName

        self.refNameLatOld = self.refNameLat.copy()
        self.refNameVertOld = self.refNameVert.copy()
        self.refNameFocOld = self.refNameFoc.copy()

        iii = 0
        for saveNameButton in self.posText:
            saveNameButton.textChanged.connect(self.savName)
            saveNameButton.setText(self.refNameLat[iii])
            iii += 1
        eee = 0
        for absButton in self.absLatRef:
            absButton.setValue(float(self.refValueLatStep[eee] * self.unitChangeLat))
            eee += 1
        eee = 0
        for absButton in self.absVertRef:
            absButton.setValue(float(self.refValueVertStep[eee] * self.unitChangeVert))
            eee += 1
        eee = 0
        for absButton in self.absFocRef:
            absButton.setValue(float(self.refValueFocStep[eee] * self.unitChangeFoc))
            eee += 1
        
        self.addLog("Update", "✅ Données synchronisées depuis RSAI")

    def updateDB(self):
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
        
        if self.refValueLatStep != self.refValueLatStepOld:
            for ref in self.refValueLatStep:
                ref = ref * float((self.stepmotor[0]))
                self.MOT[0].setRefValue(i, int(ref))
                i += 1
        i = 0
        if self.refValueVertStep != self.refValueVertStepOld:
            for ref in self.refValueVertStep:
                ref = ref * float((self.stepmotor[1]))
                self.MOT[1].setRefValue(i, int(ref))
                i += 1
        i = 0
        if self.refValueFocStep != self.refValueFocStepOld:
            for ref in self.refValueFocStep:
                ref = ref * float((self.stepmotor[2]))
                self.MOT[2].setRefValue(i, int(ref))
                i += 1
        
        self.addLog("Update", "💾 Base de données mise à jour")

    def startThread2(self):
        self.threadVert.ThreadINIT()
        self.threadVert.start()
        time.sleep(0.01)
        self.threadFoc.ThreadINIT()
        self.threadFoc.start()
        time.sleep(0.01)
        self.threadLat.ThreadINIT()
        self.threadLat.start()
        time.sleep(0.01)
        self.threadEtatVert.ThreadINIT()
        self.threadEtatVert.start()
        time.sleep(0.01)
        self.threadEtatFoc.ThreadINIT()
        self.threadEtatFoc.start()
        time.sleep(0.01)
        self.threadEtatLat.ThreadINIT()
        self.threadEtatLat.start()

    def setup(self):
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(5)
        mainLayout.setContentsMargins(10, 5, 5, 5)
        
        
        # ========== MOTEURS LATÉRAL ET VERTICAL ==========
        motorsGroup = QGroupBox(f"  {self.nomTilt} Control")
        motorsGroup.setStyleSheet("""
            QGroupBox {
                font: bold 20pt;
                color: #4a9eff;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 20px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        motorsGroup.setMaximumHeight(260)
        
        motorsMainLayout = QVBoxLayout()
        motorsMainLayout.setSpacing(5)
        
        # Ligne unité et butées
        unitButeeLayout = QHBoxLayout()
        unitLabel = QLabel("Unit:")
        unitLabel.setStyleSheet("font: 10pt; color: #888;")
        unitButeeLayout.addWidget(unitLabel)
        
        self.unitTransBouton = QComboBox()
        self.unitTransBouton.setMaximumWidth(90)
        self.unitTransBouton.setMinimumWidth(90)
        self.unitTransBouton.setStyleSheet("font: bold 10pt; padding: 5px;")
        self.unitTransBouton.addItems(['Step', 'um', 'mm', 'ps'])
        self.unitTransBouton.setCurrentIndex(self.indexUnit)
        unitButeeLayout.addWidget(self.unitTransBouton)
        
        unitButeeLayout.addStretch()
        
        buteeLabel = QLabel("Limits:")
        buteeLabel.setStyleSheet("font: 10pt; color: #888;")
        unitButeeLayout.addWidget(buteeLabel)
        
        self.butNegButt = QCheckBox('FDC-')
        self.butNegButt.setEnabled(False)
        self.butNegButt.setStyleSheet("font: 9pt;")
        unitButeeLayout.addWidget(self.butNegButt)
        
        self.butPosButt = QCheckBox('FDC+')
        self.butPosButt.setEnabled(False)
        self.butPosButt.setStyleSheet("font: 9pt;")
        unitButeeLayout.addWidget(self.butPosButt)
        
        motorsMainLayout.addLayout(unitButeeLayout)
        
        motorsLayout = QHBoxLayout()
        motorsLayout.setSpacing(10)
        
        # Positions Lat/Vert
        positionsLayout = QVBoxLayout()
        positionsLayout.setSpacing(8)
        
        # Latéral
        hLatBox = QHBoxLayout()
        self.posLat = QPushButton('Lateral')
        self.posLat.setStyleSheet("font: bold 12pt; padding: 5px;")
        self.posLat.setMaximumHeight(40)
        self.posLat.setMaximumWidth(90)
        
        self.position_Lat = QLabel('0.00')
        self.position_Lat.setStyleSheet("""
            QLabel {
                font: bold 24pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 8px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)
        self.position_Lat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_Lat.setMinimumHeight(60)
        
        self.enPosition_Lat = QLineEdit()
        self.enPosition_Lat.setReadOnly(True)
        self.enPosition_Lat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enPosition_Lat.setMaximumWidth(100)
        self.enPosition_Lat.setStyleSheet("""
            QLineEdit {
                font: bold 9pt;
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        
        self.zeroButtonLat = QPushButton('⓪')
        self.zeroButtonLat.setMaximumWidth(35)
        self.zeroButtonLat.setToolTip('Remettre à zéro')
        self.zeroButtonLat.setStyleSheet("padding: 5px; font: bold 12pt;")
        
        hLatBox.addWidget(self.posLat)
        hLatBox.addWidget(self.position_Lat, 2)
        hLatBox.addWidget(self.enPosition_Lat)
        hLatBox.addWidget(self.zeroButtonLat)
        positionsLayout.addLayout(hLatBox)
        
        # Vertical
        hVertBox = QHBoxLayout()
        self.posVert = QPushButton('Vertical')
        self.posVert.setStyleSheet("font: bold 12pt; padding: 5px;")
        self.posVert.setMaximumHeight(40)
        self.posVert.setMaximumWidth(90)
        
        self.position_Vert = QLabel('0.00')
        self.position_Vert.setStyleSheet("""
            QLabel {
                font: bold 24pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 8px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)
        self.position_Vert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_Vert.setMinimumHeight(60)
        
        self.enPosition_Vert = QLineEdit()
        self.enPosition_Vert.setReadOnly(True)
        self.enPosition_Vert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.enPosition_Vert.setMaximumWidth(100)
        self.enPosition_Vert.setStyleSheet("""
            QLineEdit {
                font: bold 9pt;
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        
        self.zeroButtonVert = QPushButton('⓪')
        self.zeroButtonVert.setMaximumWidth(35)
        self.zeroButtonVert.setToolTip('Remettre à zéro')
        self.zeroButtonVert.setStyleSheet("padding: 5px; font: bold 12pt;")
        
        hVertBox.addWidget(self.posVert)
        hVertBox.addWidget(self.position_Vert, 2)
        hVertBox.addWidget(self.enPosition_Vert)
        hVertBox.addWidget(self.zeroButtonVert)
        positionsLayout.addLayout(hVertBox)
        
        motorsLayout.addLayout(positionsLayout, 3)
        
        # Contrôles directionnels
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(5)
        grid_layout.setHorizontalSpacing(5)
        
        self.haut = QToolButton()
        self.haut.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconFlecheHaut});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconFlecheHaut});background-color: gray;}}"
        )
        self.haut.setFixedSize(60, 60)
        self.haut.setAutoRepeat(False)
        
        self.bas = QToolButton()
        self.bas.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconFlecheBas});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconFlecheBas});background-color: gray;}}"
        )
        self.bas.setFixedSize(60, 60)
        self.bas.setAutoRepeat(False)
        
        self.gauche = QToolButton()
        self.gauche.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconFlecheGauche});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconFlecheGauche});background-color: gray;}}"
        )
        self.gauche.setFixedSize(60, 60)
        self.gauche.setAutoRepeat(False)
        
        self.droite = QToolButton()
        self.droite.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconFlecheDroite});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconFlecheDroite});background-color: gray;}}"
        )
        self.droite.setFixedSize(60, 60)
        self.droite.setAutoRepeat(False)
        
        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(200000)
        self.jogStep.setDecimals(2)
        self.jogStep.setStyleSheet("font: bold 10pt; padding: 5px;")
        self.jogStep.setValue(100)
        self.jogStep.setMaximumWidth(110)
        self.jogStep.setMinimumHeight(30)
        
        grid_layout.addWidget(self.haut, 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.bas, 2, 1, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.gauche, 1, 0, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.droite, 1, 2, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.jogStep, 1, 1, Qt.AlignmentFlag.AlignCenter)
        
        motorsLayout.addLayout(grid_layout, 2)
        motorsMainLayout.addLayout(motorsLayout)
        motorsGroup.setLayout(motorsMainLayout)
        mainLayout.addWidget(motorsGroup)
        
        # ========== MOTEUR FOCUS ==========
        focusGroup = QGroupBox("Focus Control")
        focusGroup.setStyleSheet("""
            QGroupBox {
                font: bold 11pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        focusGroup.setMaximumHeight(100)
        
        focusLayout = QHBoxLayout()
        focusLayout.setSpacing(8)
        
        # Position Focus
        hboxFoc = QHBoxLayout()
        self.posFoc = QPushButton('Focus')
        self.posFoc.setMaximumHeight(30)
        self.posFoc.setMaximumWidth(70)
        self.posFoc.setStyleSheet("font: bold 10pt; padding: 5px;")
        
        self.position_Foc = QLabel('0.00')
        self.position_Foc.setStyleSheet("""
            QLabel {
                font: bold 24pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 8px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)
        self.position_Foc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_Foc.setMinimumHeight(60)
        
        self.unitFocBouton = QComboBox()
        self.unitFocBouton.addItems(['Step', 'um', 'mm', 'ps'])
        self.unitFocBouton.setMinimumWidth(80)
        self.unitFocBouton.setStyleSheet("font: bold 9pt; padding: 5px;")
        self.unitFocBouton.setCurrentIndex(self.indexUnitFoc)
        
        self.enPosition_Foc = QLineEdit()
        self.enPosition_Foc.setReadOnly(True)
        self.enPosition_Foc.setMaximumWidth(100)
        self.enPosition_Foc.setStyleSheet("""
            QLineEdit {
                font: bold 9pt;
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.enPosition_Foc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.zeroButtonFoc = QPushButton('⓪')
        self.zeroButtonFoc.setMaximumWidth(35)
        self.zeroButtonFoc.setToolTip('Remettre à zéro')
        self.zeroButtonFoc.setStyleSheet("padding: 5px; font: bold 12pt;")
        
        hboxFoc.addWidget(self.posFoc)
        hboxFoc.addWidget(self.position_Foc, 2)
        hboxFoc.addWidget(self.unitFocBouton)
        hboxFoc.addWidget(self.enPosition_Foc)
        hboxFoc.addWidget(self.zeroButtonFoc)
        focusLayout.addLayout(hboxFoc)
        
        # Contrôles Jog Focus
        jogFocLayout = QHBoxLayout()
        
        self.moins = QToolButton()
        self.moins.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconMoins});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconMoins});background-color: gray;}}"
        )
        self.moins.setFixedSize(60, 60)
        self.moins.setAutoRepeat(True)
        
        self.jogStep_2 = QDoubleSpinBox()
        self.jogStep_2.setMaximum(200000)
        self.jogStep_2.setDecimals(2)
        self.jogStep_2.setStyleSheet("font: bold 10pt; padding: 5px;")
        self.jogStep_2.setValue(self.jogValueFoc)
        self.jogStep_2.setMinimumHeight(30)
        self.jogStep_2.setMaximumWidth(130)

        self.plus = QToolButton()
        self.plus.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconPlus});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconPlus});background-color: gray;}}"
        )
        self.plus.setFixedSize(60, 60)
        self.plus.setAutoRepeat(True)
        
        jogFocLayout.addWidget(self.moins)
        jogFocLayout.addWidget(self.jogStep_2, 1)
        jogFocLayout.addWidget(self.plus)
        focusLayout.addLayout(jogFocLayout)
        
        focusGroup.setLayout(focusLayout)
        mainLayout.addWidget(focusGroup)
        
        # ========== CONTRÔLES ==========
        controlGroup = QGroupBox("Controls")
        controlGroup.setStyleSheet("""
            QGroupBox {
                font: bold 11pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        controlGroup.setMaximumHeight(100)
        
        hbox3 = QHBoxLayout()
        hbox3.setSpacing(8)
        
        self.stopButton = QToolButton()
        self.stopButton.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconStop});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconStop});background-color: gray;}}"
        )
        self.stopButton.setFixedSize(70, 60)
        self.stopButton.setToolTip('⏹ Arrêt d\'urgence')
        hbox3.addWidget(self.stopButton)
        
        self.showRef = QPushButton('Ref')
        self.showRef.setIcon(QIcon(str(self.iconRef)))
        self.showRef.setIconSize(QSize(24, 24))
        self.showRef.setMinimumHeight(60)
        self.showRef.setStyleSheet("font: bold 10pt; padding: 8px;")
        hbox3.addWidget(self.showRef)
        
        self.logButton = QPushButton('📋 Log')
        self.logButton.setMinimumHeight(60)
        self.logButton.setStyleSheet("font: bold 10pt; color: #4a9eff; padding: 8px;")
        self.logButton.setToolTip("Afficher l'historique des actions")
        hbox3.addWidget(self.logButton)
        
        controlGroup.setLayout(hbox3)
        mainLayout.addWidget(controlGroup)
        
        # ========== RÉFÉRENCES ==========
        self.REF1 = REF3M(num=1)
        self.REF2 = REF3M(num=2)
        self.REF3 = REF3M(num=3)
        self.REF4 = REF3M(num=4)
        self.REF5 = REF3M(num=5)
        self.REF6 = REF3M(num=6)

        refGroup = QGroupBox("Reference Positions")
        refGroup.setStyleSheet("""
            QGroupBox {
                font: bold 11pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        grid_layoutRef = QGridLayout()
        grid_layoutRef.setVerticalSpacing(8)
        grid_layoutRef.setHorizontalSpacing(8)
        grid_layoutRef.addWidget(self.REF1, 0, 0)
        grid_layoutRef.addWidget(self.REF2, 0, 1)
        grid_layoutRef.addWidget(self.REF3, 0, 2)
        grid_layoutRef.addWidget(self.REF4, 1, 0)
        grid_layoutRef.addWidget(self.REF5, 1, 1)
        grid_layoutRef.addWidget(self.REF6, 1, 2)
        
        refGroup.setLayout(grid_layoutRef)
        self.widget6REF = refGroup
        mainLayout.addWidget(self.widget6REF)
        
        self.setLayout(mainLayout)
        
        self.absLatRef = [self.REF1.ABSLatref, self.REF2.ABSLatref, self.REF3.ABSLatref, 
                         self.REF4.ABSLatref, self.REF5.ABSLatref, self.REF6.ABSLatref]
        self.absVertRef = [self.REF1.ABSVertref, self.REF2.ABSVertref, self.REF3.ABSVertref, 
                          self.REF4.ABSVertref, self.REF5.ABSVertref, self.REF6.ABSVertref]
        self.absFocRef = [self.REF1.ABSFocref, self.REF2.ABSFocref, self.REF3.ABSFocref, 
                         self.REF4.ABSFocref, self.REF5.ABSFocref, self.REF6.ABSFocref]
        self.posText = [self.REF1.posText, self.REF2.posText, self.REF3.posText, 
                       self.REF4.posText, self.REF5.posText, self.REF6.posText]
        self.POS = [self.REF1.Pos, self.REF2.Pos, self.REF3.Pos, 
                   self.REF4.Pos, self.REF5.Pos, self.REF6.Pos]
        self.Take = [self.REF1.take, self.REF2.take, self.REF3.take, 
                    self.REF4.take, self.REF5.take, self.REF6.take]
        
        self.jogStep_2.setFocus()
        self.refShow()

    # def focusInEvent(self, event):
    #     super().focusInEvent(event)
    #     self.threadLat.positionSleep = 0.05
    #     self.threadVert.positionSleep = 0.05
    #     self.threadFoc.positionSleep = 0.05

    # def focusOutEvent(self, event):
    #     super().focusOutEvent(event)
    #     self.threadLat.positionSleep = 1
    #     self.threadVert.positionSleep = 1
    #     self.threadFoc.positionSleep = 1

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self.threadLat.setPositionSleep(0.05)
                self.threadVert.setPositionSleep(0.05)
                self.threadFoc.setPositionSleep(0.05)
                # print('window active')
            else:
                self.threadLat.setPositionSleep(1)
                self.threadVert.setPositionSleep(1)
                self.threadFoc.setPositionSleep(1)
                # print('window inactive')

    def hideEvent(self, event):
        super().hideEvent(event)
        self.threadLat.setPositionSleep(10)
        self.threadVert.setPositionSleep(10)
        self.threadFoc.setPositionSleep(10)

    def showEvent(self, event):
        super().showEvent(event)
        if self.isActiveWindow():
            self.threadLat.setPositionSleep(0.05)
            self.threadVert.setPositionSleep(0.05)
            self.threadFoc.setPositionSleep(0.05)
        else:
            self.threadLat.setPositionSleep(1) 
            self.threadVert.setPositionSleep(1)
            self.threadFoc.setPositionSleep(1)

    def actionButton(self):
        self.unitFocBouton.currentIndexChanged.connect(self.unitFoc)
        self.unitTransBouton.currentIndexChanged.connect(self.unitTrans)
        
        self.haut.clicked.connect(self.hMove)
        self.bas.clicked.connect(self.bMove)
        self.gauche.clicked.connect(self.gMove)
        self.droite.clicked.connect(self.dMove)
        
        self.plus.clicked.connect(self.pMove)
        self.moins.clicked.connect(self.mMove)
        
        self.zeroButtonFoc.clicked.connect(self.ZeroFoc)
        self.zeroButtonLat.clicked.connect(self.ZeroLat)
        self.zeroButtonVert.clicked.connect(self.ZeroVert)
        
        self.stopButton.clicked.connect(self.StopMot)
        self.showRef.clicked.connect(self.refShow)
        
        self.posVert.clicked.connect(lambda: self.open_widget(self.VertWidget))
        self.posLat.clicked.connect(lambda: self.open_widget(self.LatWidget))
        self.posFoc.clicked.connect(lambda: self.open_widget(self.FocWidget))
        
        iii = 0
        for saveNameButton in self.posText:
            saveNameButton.textChanged.connect(self.savName)
            saveNameButton.setText(self.refNameLat[iii])
            iii += 1
            
        for posButton in self.POS:
            posButton.clicked.connect(self.ref)
            
        eee = 0
        for absButton in self.absLatRef:
            absButton.setValue(float(self.refValueLatStep[eee] * self.unitChangeLat))
            absButton.editingFinished.connect(self.savRefLat)
            eee += 1
        eee = 0
        for absButton in self.absVertRef:
            absButton.setValue(float(self.refValueVertStep[eee] * self.unitChangeVert))
            absButton.editingFinished.connect(self.savRefVert)
            eee += 1
        eee = 0
        for absButton in self.absFocRef:
            absButton.setValue(float(self.refValueFocStep[eee] * self.unitChangeFoc))
            absButton.editingFinished.connect(self.savRefFoc)
            eee += 1
            
        for takeButton in self.Take:
            takeButton.clicked.connect(self.take)
        
       
        self.logButton.clicked.connect(self.showLog)

    def open_widget(self, fene):
        if fene.isWinOpen is False:
            fene.show()
            fene.startThread2()
            fene.isWinOpen = True
        else:
            fene.raise_()
            fene.showNormal()

    def update(self):
        """Mise à jour manuelle depuis RSAI"""
        self.updateFromRSAI()
        self.addLog("Update", "🔄 Mise à jour manuelle effectuée")

    def refShow(self):
        if self.refShowId is True:
            self.widget6REF.show()
            self.refShowId = False
            self.showRef.setText('Hide Ref')
            self.setFixedSize(850, 950)
        else:
            self.widget6REF.hide()
            self.refShowId = True
            self.showRef.setText('Show Ref')
            self.setFixedSize(850, 600)

    def pMove(self):
        a = float(self.jogStep_2.value())
        a = float(a / self.unitChangeFoc)
        b = self.MOT[2].position()
        
        if b + a > self.butePos[2]:
            self.MOT[2].stopMotor()
            self.butPosButt.setChecked(True)
            self.butPosButt.setStyleSheet('color:red')
            self.addLog("STOP", "⚠️ Butée positive Focus")
        else:
            self.MOT[2].rmove(a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butNegButt.setStyleSheet("")
            self.butPosButt.setStyleSheet("")
            self.addLog("Jog Focus", f"➕ {self.jogStep_2.value():.2f} {self.unitNameFoc}")

    def mMove(self):
        a = float(self.jogStep_2.value())
        a = float(a / self.unitChangeFoc)
        b = self.MOT[2].position()
        
        if b - a < self.buteNeg[2]:
            self.MOT[2].stopMotor()
            self.butNegButt.setChecked(True)
            self.butNegButt.setStyleSheet('color:red')
            self.addLog("STOP", "⚠️ Butée négative Focus")
        else:
            self.MOT[2].rmove(-a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butNegButt.setStyleSheet('')
            self.butPosButt.setStyleSheet('')
            self.addLog("Jog Focus", f"➖ {self.jogStep_2.value():.2f} {self.unitNameFoc}")

    def gMove(self):
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeLat)
        b = self.MOT[0].position()
        
        if self.inv[0] is False:
            if b - a < self.buteNeg[0]:
                self.MOT[0].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
                self.addLog("STOP", "⚠️ Butée négative Latéral")
            else:
                self.MOT[0].rmove(-a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Lat", f"⬅️ {self.jogStep.value():.2f} {self.unitNameTrans}")
        else:
            if b + a > self.butePos[0]:
                self.MOT[0].stopMotor()
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.addLog("STOP", "⚠️ Butée positive Latéral")
            else:
                self.MOT[0].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Lat", f"⬅️ {self.jogStep.value():.2f} {self.unitNameTrans}")

    def dMove(self):
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeLat)
        b = self.MOT[0].position()
        
        if self.inv[0] is False:
            if b + a > self.butePos[0]:
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.MOT[0].stopMotor()
                self.addLog("STOP", "⚠️ Butée positive Latéral")
            else:
                self.MOT[0].rmove(+a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Lat", f"➡️ {self.jogStep.value():.2f} {self.unitNameTrans}")
        else:
            if b - a < self.buteNeg[0]:
                self.MOT[0].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
                self.addLog("STOP", "⚠️ Butée négative Latéral")
            else:
                self.MOT[0].rmove(-a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Lat", f"➡️ {self.jogStep.value():.2f} {self.unitNameTrans}")

    def hMove(self):
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeVert)
        b = self.MOT[1].position()
        
        if self.inv[1] is False:
            if b + a > self.butePos[1]:
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
                self.addLog("STOP", "⚠️ Butée positive Vertical")
            else:
                self.MOT[1].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Vert", f"⬆️ {self.jogStep.value():.2f} {self.unitNameTrans}")
        else:
            if b - a < self.buteNeg[1]:
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
                self.addLog("STOP", "⚠️ Butée négative Vertical")
            else:
                self.MOT[1].rmove(-a)
                self.butNegButt.setChecked(False)
                self.butPosButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.butPosButt.setStyleSheet('')
                self.addLog("Jog Vert", f"⬆️ {self.jogStep.value():.2f} {self.unitNameTrans}")

    def bMove(self):
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeVert)
        b = self.MOT[1].position()
        
        if self.inv[1] is False:
            if b - a < self.buteNeg[1]:
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
                self.addLog("STOP", "⚠️ Butée négative Vertical")
            else:
                self.MOT[1].rmove(-a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Vert", f"⬇️ {self.jogStep.value():.2f} {self.unitNameTrans}")
        else:
            if b + a > self.butePos[1]:
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
                self.MOT[1].stopMotor()
                self.addLog("STOP", "⚠️ Butée positive Vertical")
            else:
                self.MOT[1].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                self.addLog("Jog Vert", f"⬇️ {self.jogStep.value():.2f} {self.unitNameTrans}")

    def ZeroLat(self):
        b = self.MOT[0].position()
        self.MOT[0].setzero()
        self.addLog("Zero Lat", f"🔄 Position remise à zéro (était: {b*self.unitChangeLat:.2f} {self.unitNameTrans})")

    def ZeroVert(self):
        b = self.MOT[1].position()
        self.MOT[1].setzero()
        self.addLog("Zero Vert", f"🔄 Position remise à zéro (était: {b*self.unitChangeVert:.2f} {self.unitNameTrans})")

    def ZeroFoc(self):
        b = self.MOT[2].position()
        self.MOT[2].setzero()
        self.addLog("Zero Foc", f"🔄 Position remise à zéro (était: {b*self.unitChangeFoc:.2f} {self.unitNameFoc})")

    def RefMark(self):
        pass

    def unitFoc(self):
        self.indexUnitFoc = self.unitFocBouton.currentIndex()
        valueJog_2 = self.jogStep_2.value() / self.unitChangeFoc
        
        if self.indexUnitFoc == 0:
            self.unitChangeFoc = 1
            self.unitNameFoc = 'step'
        elif self.indexUnitFoc == 1:
            self.unitChangeFoc = float(self.stepmotor[2])
            self.unitNameFoc = 'um'
        elif self.indexUnitFoc == 2:
            self.unitChangeFoc = float(self.stepmotor[2] / 1000)
            self.unitNameFoc = 'mm'
        elif self.indexUnitFoc == 3:
            self.unitChangeFoc = float(self.stepmotor[2] * 0.0066666666)
            self.unitNameFoc = 'ps'
            
        if self.unitChangeFoc == 0:
            self.unitChangeFoc = 1
        
        self.jogStep_2.setValue(valueJog_2 * self.unitChangeFoc)
        self.jogStep_2.setSuffix(" %s" % self.unitNameFoc)
        
        eee = 0
        for absButton in self.absFocRef:
            absButton.setValue(float(self.refValueFocStep[eee]) * self.unitChangeFoc)
            absButton.setSuffix(" %s" % self.unitNameFoc)
            eee += 1

    def unitTrans(self):
        valueJog = self.jogStep.value() / self.unitChangeLat
        self.indexUnit = self.unitTransBouton.currentIndex()
        
        if self.indexUnit == 0:
            self.unitChangeLat = 1
            self.unitChangeVert = 1
            self.unitNameTrans = 'step'
        elif self.indexUnit == 1:
            self.unitChangeLat = float(self.stepmotor[0])
            self.unitChangeVert = float(self.stepmotor[1])
            self.unitNameTrans = 'um'
        elif self.indexUnit == 2:
            self.unitChangeLat = float(self.stepmotor[0] / 1000)
            self.unitChangeVert = float(self.stepmotor[1] / 1000)
            self.unitNameTrans = 'mm'
        elif self.indexUnit == 3:
            self.unitChangeLat = float(self.stepmotor[0] * 0.0066666666)
            self.unitChangeVert = float(self.stepmotor[1] * 0.0066666666)
            self.unitNameTrans = 'ps'
            
        if self.unitChangeLat == 0:
            self.unitChangeLat = 1
        if self.unitChangeVert == 0:
            self.unitChangeVert = 1
        
        self.jogStep.setValue(valueJog * self.unitChangeLat)
        self.jogStep.setSuffix(" %s" % self.unitNameTrans)
        
        eee = 0
        for absButton in self.absLatRef:
            absButton.setValue(float(self.refValueLatStep[eee]) * self.unitChangeLat)
            absButton.setSuffix(" %s" % self.unitNameTrans)
            eee += 1
        eee = 0
        for absButton in self.absVertRef:
            absButton.setValue(float(self.refValueVertStep[eee]) * self.unitChangeVert)
            absButton.setSuffix(" %s" % self.unitNameTrans)
            eee += 1
        # self.PositionLat(self.PosEtatLat)
        # self.PositionVert(self.PosEtatVert)

    def StopMot(self):
        for zzi in range(0, 3):
            self.MOT[zzi].stopMotor()
        self.addLog("STOP", "⏹ Arrêt de tous les moteurs")

    @pyqtSlot(float)
    def PositionLat(self, Posi):
        
        a = float(Posi)
        self._positionLatStep = a
        b = a
        a = a * self.unitChangeLat
        
        self.position_Lat.setText(f"{round(a, 2)} {self.unitNameTrans}")
    
    def EtatLat(self,etat):
        self.etatLat = etat
        if self.etatLat_old != self.etatLat:
            self.etatLat_old = self.etatLat
            if self.etatLat == 'FDC-':
                self.enPosition_Lat.setText('⚠️ FDC-')
                self.enPosition_Lat.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatLat == 'FDC+':
                self.enPosition_Lat.setText('⚠️ FDC+')
                self.enPosition_Lat.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatLat == 'Poweroff':
                self.enPosition_Lat.setText('❌ Power Off')
                self.enPosition_Lat.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatLat == 'mvt':
                self.enPosition_Lat.setText('En mouvement...')
                self.enPosition_Lat.setStyleSheet('font: bold 9pt; color: white; background-color: #2d2d2d; border: 1px solid #4a9eff;')
            elif self.etat == 'notconnected':
                self.enPosition_Lat.setText('❌ Non connecté')
                self.enPosition_Lat.setStyleSheet('font: bold 8pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etat == 'errorConnect':
                self.enPosition_Lat.setText('❌ Erreur connexion')
                self.enPosition_Lat.setStyleSheet('font: bold 8pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
        
        positionConnue_Lat = 0
        precis = 5
        if (self.etatLat == 'ok' or self.etatLat == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue_Lat == 0:
                    if float(self.refValueLatStep[nbRefInt-1]) - precis < self._positionLatStep< float(self.refValueLatStep[nbRefInt-1]) + precis:
                        self.enPosition_Lat.setText(f'📍 {self.refNameLat[nbRefInt-1]}')
                        self.enPosition_Lat.setStyleSheet('font: bold 9pt; color: #4a9eff; background-color: #2d2d2d; border: 1px solid #4a9eff;')
                        positionConnue_Lat = 1
        
        if positionConnue_Lat == 0 and (self.etatLat == 'ok' or self.etatLat == '?'):
            self.enPosition_Lat.setText('✅')
            self.enPosition_Lat.setStyleSheet('font: bold 9pt; color: #00ff00; background-color: #2d2d2d; border: 1px solid #555;')

    @pyqtSlot(float)
    def PositionVert(self, Posi):
        a = float(Posi)
        self._positionVertStep = a
        b = a
        a = a * self.unitChangeVert
        self.position_Vert.setText(f"{round(a, 2)} {self.unitNameTrans}")

    def EtatVert(self,etat):
        self.etatVert= etat   
        if self.etatVert != self.etatVert_old:
            self.etatVert_old = self.etatVert
            if self.etatVert == 'FDC-':
                self.enPosition_Vert.setText('⚠️ FDC-')
                self.enPosition_Vert.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatVert == 'FDC+':
                self.enPosition_Vert.setText('⚠️ FDC+')
                self.enPosition_Vert.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatVert == 'Poweroff':
                self.enPosition_Vert.setText('❌ Power Off')
                self.enPosition_Vert.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatVert == 'mvt':
                self.enPosition_Vert.setText('En mouvement...')
                self.enPosition_Vert.setStyleSheet('font: bold 9pt; color: white; background-color: #2d2d2d; border: 1px solid #4a9eff;')
            elif self.etat == 'notconnected':
                self.enPosition_Vert.setText('❌ Non connecté')
                self.enPosition_Vert.setStyleSheet('font: bold 8pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etat == 'errorConnect':
                self.enPosition_Vert.setText('❌ Erreur connexion')
                self.enPosition_Vert.setStyleSheet('font: bold 8pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
        
        positionConnue_Vert = 0
        precis = 5
        if (self.etatVert == 'ok' or self.etatVert == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue_Vert == 0:
                    if float(self.refValueVertStep[nbRefInt-1]) - precis < self._positionVertStep < float(self.refValueVertStep[nbRefInt-1]) + precis:
                        self.enPosition_Vert.setText(f'📍 {self.refNameVert[nbRefInt-1]}')
                        self.enPosition_Vert.setStyleSheet('font: bold 9pt; color: #4a9eff; background-color: #2d2d2d; border: 1px solid #4a9eff;')
                        positionConnue_Vert = 1
        
        if positionConnue_Vert == 0 and (self.etatVert == 'ok' or self.etatVert == '?'):
            self.enPosition_Vert.setText('✅')
            self.enPosition_Vert.setStyleSheet('font: bold 9pt; color: #00ff00; background-color: #2d2d2d; border: 1px solid #555;')

    @pyqtSlot(float)
    def PositionFoc(self, Posi):
        a = float(Posi)
        self._positionFocStep = a
        a = a * self.unitChangeFoc
        
        self.position_Foc.setText(f"{round(a, 2)} {self.unitNameFoc}")

    def EtatFoc(self,etat):  
        self.etatFoc = etat
        if self.etatFoc != self.etatFoc_old:
            self.etatFoc_old = self.etatFoc
            if self.etatFoc == 'FDC-':
                self.enPosition_Foc.setText('⚠️ FDC-')
                self.enPosition_Foc.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatFoc == 'FDC+':
                self.enPosition_Foc.setText('⚠️ FDC+')
                self.enPosition_Foc.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatFoc == 'Poweroff':
                self.enPosition_Foc.setText('❌ Power Off')
                self.enPosition_Foc.setStyleSheet('font: bold 9pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etatFoc == 'mvt':
                self.enPosition_Foc.setText('En mouvement...')
                self.enPosition_Foc.setStyleSheet('font: bold 9pt; color: white; background-color: #2d2d2d; border: 1px solid #4a9eff;')
            elif self.etat == 'notconnected':
                self.enPosition_Foc.setText('❌ Non connecté')
                self.enPosition_Foc.setStyleSheet('font: bold 8pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
            elif self.etat == 'errorConnect':
                self.enPosition_Foc.setText('❌ Erreur connexion')
                self.enPosition_Foc.setStyleSheet('font: bold 8pt; color: red; background-color: #2d2d2d; border: 1px solid red;')
        
        positionConnue_Foc = 0
        precis = 5
        if (self.etatFoc == 'ok' or self.etatFoc == '?'):
            for nbRefInt in range(1, 7):
                if positionConnue_Foc == 0:
                    if float(self.refValueFocStep[nbRefInt-1]) - precis < self._positionFocStep < float(self.refValueFocStep[nbRefInt-1]) + precis:
                        self.enPosition_Foc.setText(f'📍 {self.refNameFoc[nbRefInt-1]}')
                        self.enPosition_Foc.setStyleSheet('font: bold 9pt; color: #4a9eff; background-color: #2d2d2d; border: 1px solid #4a9eff;')
                        positionConnue_Foc = 1
        
        if positionConnue_Foc == 0 and (self.etatFoc == 'ok' or self.etatFoc == '?'):
            self.enPosition_Foc.setText('✅')
            self.enPosition_Foc.setStyleSheet('font: bold 9pt; color: #00ff00; background-color: #2d2d2d; border: 1px solid #555;')

    def take(self):
        sender = QtCore.QObject.sender(self)
        reply = QMessageBox.question(None, 'Sauvegarder Position ?', 
                                     "Voulez-vous sauvegarder cette position ?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            tposLat = self.MOT[0].position()
            nbRef = str(sender.objectName()[0])
            self.refValueLatStep[int(nbRef)-1] = tposLat
            self.absLatRef[int(nbRef)-1].setValue(tposLat * self.unitChangeLat)
            self.addLog("Référence", f"💾 Ref {nbRef} Lat sauvegardée: {self.absLatRef[int(nbRef)-1].value():.2f} {self.unitNameTrans}")
            
            tposVert = self.MOT[1].position()
            self.refValueVertStep[int(nbRef)-1] = tposVert
            self.absVertRef[int(nbRef)-1].setValue(tposVert * self.unitChangeVert)
            self.addLog("Référence", f"💾 Ref {nbRef} Vert sauvegardée: {self.absVertRef[int(nbRef)-1].value():.2f} {self.unitNameTrans}")
            
            tposFoc = self.MOT[2].position()
            self.refValueFocStep[int(nbRef)-1] = tposFoc
            self.absFocRef[int(nbRef)-1].setValue(tposFoc * self.unitChangeFoc)
            self.addLog("Référence", f"💾 Ref {nbRef} Foc sauvegardée: {self.absFocRef[int(nbRef)-1].value():.2f} {self.unitNameFoc}")

    def ref(self):
        sender = QtCore.QObject.sender(self)
        reply = QMessageBox.question(None, 'Aller à cette Position ?', 
                                     "Voulez-vous aller à cette position ?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nbRef = int(sender.objectName()[0])
            vref = []
            vref.append(int(self.refValueLatStep[nbRef-1]))
            vref.append(int(self.refValueVertStep[nbRef-1]))
            vref.append(int(self.refValueFocStep[nbRef-1]))
            
            for i in range(0, 3):
                if vref[i] < self.buteNeg[i]:
                    self.butNegButt.setChecked(True)
                    self.butNegButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                    self.addLog("STOP", f"⚠️ Butée négative moteur {i}")
                elif vref[i] > self.butePos[i]:
                    self.butPosButt.setChecked(True)
                    self.butPosButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                    self.addLog("STOP", f"⚠️ Butée positive moteur {i}")
                else:
                    time.sleep(0.2)
                    self.MOT[i].move(vref[i])
                    unit = self.unitNameTrans if i < 2 else self.unitNameFoc
                    self.addLog("Référence", f"📍 Déplacement vers Ref {nbRef} (moteur {i}): {vref[i]} {unit}")
                    time.sleep(1)
                    self.butNegButt.setChecked(False)
                    self.butPosButt.setChecked(False)
                    self.butNegButt.setStyleSheet('')
                    self.butPosButt.setStyleSheet('')

    def savName(self):
        sender = QtCore.QObject.sender(self)
        nbRef = int(sender.objectName()[0])
        vname = self.posText[int(nbRef)-1].text()
        
        self.refNameLat[nbRef-1] = str(vname)
        self.refNameVert[nbRef-1] = str(vname)
        self.refNameFoc[nbRef-1] = str(vname)

    def savRefLat(self):
        sender = QtCore.QObject.sender(self)
        nbRefLat = sender.objectName()[0]
        vrefLat = int(self.absLatRef[int(nbRefLat)-1].value())
        self.refValueLatStep[int(nbRefLat)-1] = vrefLat / self.unitChangeLat

    def savRefVert(self):
        sender = QtCore.QObject.sender(self)
        nbRefVert = sender.objectName()[0]
        vrefVert = int(self.absVertRef[int(nbRefVert)-1].value())
        self.refValueVertStep[int(nbRefVert)-1] = vrefVert / self.unitChangeVert

    def savRefFoc(self):
        sender = QtCore.QObject.sender(self)
        nbRefFoc = sender.objectName()[0]
        vrefFoc = int(self.absFocRef[int(nbRefFoc)-1].value())
        self.refValueFocStep[int(nbRefFoc)-1] = vrefFoc / self.unitChangeFoc

    def ShootAct(self):
        self.tir.TirAct()

    def addLog(self, action, details=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        self.actionLog.append(log_entry)
        # print(f"[LOG] {timestamp} {action} {details}")

    def showLog(self):
        if self.logWindow is None or not self.logWindow.isVisible():
            self.logWindow = LogWindow(parent=self)
            self.logWindow.setLogs(list(self.actionLog))
            self.logWindow.show()
        else:
            self.logWindow.raise_()
            self.logWindow.activateWindow()

    def refreshLog(self):
        if self.logWindow and self.logWindow.isVisible():
            self.logWindow.setLogs(list(self.actionLog))

    def clearLogs(self):
        self.actionLog.clear()
        self.addLog("Historique", "🗑️ Effacé")

    def closeEvent(self, event):
        self.fini()
        
        event.accept()

    def fini(self):
        self.threadLat.stopThread()
        self.threadLat.wait(1000)
        self.threadVert.stopThread()
        self.threadVert.wait(1000)
        self.threadFoc.stopThread()
        self.threadFoc.wait(1000)

        self.threadEtatLat.stopThread()
        self.threadEtatVert.stopThread()
        self.threadEtatFoc.stopThread()
        self.isWinOpen = False
        #time.sleep(0.1)
        self.updateDB()
        #time.sleep(0.2)


class REF3M(QWidget):
    '''Widget de référence pour 3 moteurs - Modernisé'''
    
    def __init__(self, num=0, parent=None):
        super(REF3M, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.id = num
        
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.setSpacing(5)
        
        # Nom
        self.posText = QLineEdit('ref')
        self.posText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.posText.setStyleSheet("font: bold 11pt; padding: 5px;")
        self.posText.setObjectName('%s' % self.id)
        mainLayout.addWidget(self.posText)
        
        # Boutons
        controlLayout = QHBoxLayout()
        
        self.iconTake = pathlib.PurePosixPath(pathlib.Path(self.icon + "disquette.png"))
        self.take = QToolButton()
        self.take.setObjectName('%s' % self.id)
        self.take.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconTake});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconTake});background-color: gray;}}"
        )
        self.take.setFixedSize(30, 30)
        self.take.setToolTip('💾 Sauvegarder position actuelle')
        
        self.iconGo = pathlib.PurePosixPath(pathlib.Path(self.icon + "go.png"))
        self.Pos = QToolButton()
        self.Pos.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconGo});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconGo});background-color: gray;}}"
        )
        self.Pos.setFixedSize(30, 30)
        self.Pos.setObjectName('%s' % self.id)
        self.Pos.setToolTip('📍 Aller à cette position')
        
        controlLayout.addWidget(self.take)
        controlLayout.addWidget(self.Pos)
        mainLayout.addLayout(controlLayout)
        
        # Valeurs
        grid_layoutPos = QGridLayout()
        grid_layoutPos.setVerticalSpacing(3)
        grid_layoutPos.setHorizontalSpacing(5)
        
        LabeLatref = QLabel('Lat:')
        LabeLatref.setStyleSheet("font: 9pt; color: #888;")
        self.ABSLatref = QDoubleSpinBox()
        self.ABSLatref.setObjectName('%s' % self.id)
        self.ABSLatref.setMaximum(5000000000)
        self.ABSLatref.setMinimum(-5000000000)
        self.ABSLatref.setStyleSheet("font: 9pt; padding: 3px;")
        
        LabelVertref = QLabel('Vert:')
        LabelVertref.setStyleSheet("font: 9pt; color: #888;")
        self.ABSVertref = QDoubleSpinBox()
        self.ABSVertref.setObjectName('%s' % self.id)
        self.ABSVertref.setMaximum(5000000000)
        self.ABSVertref.setMinimum(-5000000000)
        self.ABSVertref.setStyleSheet("font: 9pt; padding: 3px;")
        
        LabelFocref = QLabel('Foc:')
        LabelFocref.setStyleSheet("font: 9pt; color: #888;")
        self.ABSFocref = QDoubleSpinBox()
        self.ABSFocref.setObjectName('%s' % self.id)
        self.ABSFocref.setMaximum(5000000000)
        self.ABSFocref.setMinimum(-5000000000)
        self.ABSFocref.setStyleSheet("font: 9pt; padding: 3px;")
        
        grid_layoutPos.addWidget(LabeLatref, 0, 0)
        grid_layoutPos.addWidget(self.ABSLatref, 0, 1)
        grid_layoutPos.addWidget(LabelVertref, 1, 0)
        grid_layoutPos.addWidget(self.ABSVertref, 1, 1)
        grid_layoutPos.addWidget(LabelFocref, 2, 0)
        grid_layoutPos.addWidget(self.ABSFocref, 2, 1)
        
        mainLayout.addLayout(grid_layoutPos)
        
        # Container avec bordure
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgb(45, 52, 54);
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        container.setLayout(mainLayout)
        
        finalLayout = QVBoxLayout()
        finalLayout.setContentsMargins(0, 0, 0, 0)
        finalLayout.addWidget(container)
        self.setLayout(finalLayout)


class PositionThread(QtCore.QThread):
    '''Thread pour afficher position et état'''
    POS = QtCore.pyqtSignal(float)

    def __init__(self, parent=None, mot=''):
        super(PositionThread, self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False
        self.positionSleep = 0.05
        self.etat_old = ""
        self.Posi_old = 0
    def GetPositionSleep(self):
        return self.positionSleep
    
    def setPositionSleep(self, value):
        self.positionSleep = value

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                Posi = (self.MOT.position())
                positionSleepVa = self.GetPositionSleep()
                time.sleep(positionSleepVa)
                try:
                    if self.Posi_old != Posi :
                        self.POS.emit(Posi)
                        self.Posi_old = Posi
                except Exception as e:
                    print('error emit', e)

    def ThreadINIT(self):
        self.stop = False

    def stopThread(self):
        self.stop = True
        # time.sleep(0.1)


class EtatThread(QtCore.QThread):
    '''Thread pour afficher état'''
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mot=''):
        super(EtatThread, self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False
        self.etatSleep = 0.5
        self.etat_old = ""
        self.Posi_old = 0

    def run(self):
        while self.stop is False:
            time.sleep(self.etatSleep)
            etat = self.MOT.etatMotor()
            try:
                if self.etat_old != etat:
                        self.ETAT.emit(etat)
                        self.etat_old = etat
            except Exception as e:
                print('error etat emit', e)

    def ThreadINIT(self):
        self.stop = False

    def stopThread(self):
        self.stop = True
        # time.sleep(0.1)

class LogWindow(QDialog):
    """Fenêtre de log modernisée"""
    
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.setWindowTitle("📋 Historique des Actions")
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        title = QLabel("Dernières actions (max 30)")
        title.setStyleSheet("font: bold 14pt; color: #4a9eff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
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
        self.logText.clear()
        
        if not logs:
            self.logText.setHtml('<span style="color: #ff6b6b;">Aucune action enregistrée</span>')
            return
        
        html = ""
        for log in logs:
            timestamp = log['timestamp']
            action = log['action']
            details = log.get('details', '')
            
            if 'move' in action.lower() or 'jog' in action.lower():
                color = "#4a9eff"
                icon = "→"
            elif 'stop' in action.lower():
                color = "#ff6b6b"
                icon = "⏹"
            elif 'zero' in action.lower():
                color = "#ffd43b"
                icon = "⓪"
            elif 'ref' in action.lower() or 'référence' in action.lower():
                color = "#51cf66"
                icon = "📍"
            elif 'update' in action.lower():
                color = "#9775fa"
                icon = "🔄"
            else:
                color = "#aaaaaa"
                icon = "•"
            
            html += f'<span style="color: #888;">[{timestamp}]</span> '
            html += f'<span style="color: {color}; font-weight: bold;">{icon} {action}</span>'
            
            if details:
                html += f' <span style="color: #ccc;">{details}</span>'
            
            html += '<br>'
        
        self.logText.setHtml(html)
        scrollbar = self.logText.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def refresh(self):
        if self.parent():
            self.parent().refreshLog()
    
    def clearLogs(self):
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
    mot = THREEMOTORGUI(IPVert='10.0.1.30', NoMotorVert=12, 
                        IPLat='10.0.1.30', NoMotorLat=13, 
                        IPFoc='10.0.1.30', NoMotorFoc=14, 
                        nomWin='JET rosa', 
                        nomTilt='Jet Rosa',
                        invLat=True, invVert=True)
    mot.show()
    mot.startThread2()
    appli.exec()