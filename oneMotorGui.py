#! /home/sallejaune/loaenv/bin/python3.12
# -*- coding: utf-8 -*-
"""
Created on 21 January 2026
@author: Julien Gautier (LOA)
Interface modernisée avec style cohérent
"""

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit, QToolButton
from PyQt6.QtWidgets import QInputDialog, QTextEdit, QDoubleSpinBox, QCheckBox
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QDialog
from PyQt6.QtWidgets import QComboBox, QLabel, QGroupBox, QSizePolicy
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSlot, QSize
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
__author__ = __init__.__author__


class ONEMOTORGUI(QWidget):
    """
    User interface Motor class modernisée
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
        
        # Icons
        self.iconPlay = pathlib.PurePosixPath(pathlib.Path(self.icon + "playGreen.png"))
        self.iconMoins = pathlib.PurePosixPath(pathlib.Path(self.icon + "moinsBleu.png"))
        self.iconPlus = pathlib.PurePosixPath(pathlib.Path(self.icon + "plusBleu.png"))
        self.iconStop = pathlib.PurePosixPath(pathlib.Path(self.icon + "close.png"))
        self.iconRef = pathlib.PurePosixPath(pathlib.Path(self.icon + "ref.png"))
        # Log 
        self.actionLog = deque(maxlen=20)
        self.logWindow = None

        self.MOT[0] = zmq_client_RSAI.MOTORRSAI(self.IpAdress, self.NoMotor)
        time.sleep(0.05)

        if self.MOT[0].isconnected is True:
            self.addLog("Connexion", "✅ Serveur connecté")
        else:
            self.addLog("Connexion", "❌ Échec connexion serveur")

        self.equipementName = self.MOT[0].getEquipementName()
        
        self.stepmotor = [0, 0, 0]
        self.butePos = [0, 0, 0]
        self.buteNeg = [0, 0, 0]
        self.name = [0, 0, 0]
        
        for zzi in range(0, 1):
            self.stepmotor[zzi] = float((self.MOT[0].getStepValue()))
            self.butePos[zzi] = float(self.MOT[0].getButLogPlusValue())
            self.buteNeg[zzi] = float(self.MOT[0].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[0].name)
        # Init unités

        if self.indexUnit == 0:
            self.unitChange = 1
            self.unitName = 'step'
        elif self.indexUnit == 1:
            self.unitChange = float(self.stepmotor[0])
            self.unitName = 'um'
        elif self.indexUnit == 2:
            self.unitChange = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        elif self.indexUnit == 3:
            self.unitChange = float(self.stepmotor[0]*0.0066666666)
            self.unitName = 'ps'
        elif self.indexUnit == 4:
            self.unitChange = self.stepmotor[0]
            self.unitName = '°'

        self.thread = PositionThread(self, mot=self.MOT[0])
        self.thread.POS.connect(self.Position)
        
        self.addLog("Initialisation", f"Moteur {self.NoMotor} - {self.equipementName}")
        self.refreshLog()
        
        self.scanWidget = SCAN(MOT=self.MOT[0])
        self.configWidget = None  # Créé à la demande
        
        self.setup()
        self.updateFromRSAI()
        self.unit()
        self.jogStep.setValue(self.jogValue)
        self.actionButton()
        
    def updateFromRSAI(self):
        self.MOT[0].update()
        time.sleep(0.1)
        
        for zzi in range(0, 1):
            self.stepmotor[zzi] = float((self.MOT[0].step))
            self.butePos[zzi] = float(self.MOT[0].butPlus)
            self.buteNeg[zzi] = float(self.MOT[0].butMoins)
            self.name[zzi] = str(self.MOT[0].name)
        
        self.setWindowTitle(f"{self.name[0]} on {self.equipementName} ({self.IpAdress}) [M {self.NoMotor}] ")
        self.motorNameLabel = self.name[0]
        self.refValue = self.MOT[0].refValue
        
        self.refValueStep = []
        for ref in self.refValue:
            self.refValueStep.append(ref / self.stepmotor[0])

        self.refValueStepOld = self.refValueStep.copy()
        self.refName = self.MOT[0].refName
        self.refNameOld = self.refName.copy()
        
        iii = 0
        for saveNameButton in self.posText:
            saveNameButton.setText(self.refName[iii])
            iii += 1
        eee = 0
        for absButton in self.absRef:
            absButton.setValue(float(self.refValueStep[eee]*self.unitChange))
            eee += 1
            
        self.addLog("Update", "Données synchronisées depuis RSAI")

    def updateDB(self):
        i = 0
        if self.refValueStep != self.refValueStepOld:
            for ref in self.refValueStep:
                ref = ref * float(self.stepmotor[0])
                a = self.MOT[0].setRefValue(i, int(ref))
                i += 1
        i = 0
        if self.refName != self.refNameOld:
            for ref in self.refName:
                self.MOT[0].setRefName(i, ref)
                i += 1
        if self.refValueStep != self.refValueStepOld or self.refName != self.refNameOld:
            self.addLog("Update", "Base de données mise à jour")

    def startThread2(self):
        self.thread.ThreadINIT()
        self.thread.start()
        time.sleep(0.01)
    
    def setup(self):

        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(6)  # Réduit de 6 à 4
        mainLayout.setContentsMargins(6, 6, 6, 6)  # Réduit de 8 à 6
        
        # ========== INFORMATIONS MOTEUR ==========
        self.motorNameLabel = self.name[0]
        txt = f"{self.motorNameLabel}   on rack : {self.equipementName}"
        infoGroup = QGroupBox(txt)
        infoGroup.setStyleSheet("""
            QGroupBox {
                font: bold 14pt;
                color: #4a9eff;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        infoGroup.setMaximumHeight(95)  # Réduit de 140 à 95
        infoLayout = QVBoxLayout()
        infoLayout.setSpacing(3)
        
        # # Rack info
        # rackInfoLayout = QHBoxLayout()
        # rackLabel = QLabel(f"Rack: {self.equipementName} ({self.IpAdress})")
        # rackLabel.setStyleSheet("color: #888; font: 8pt;")  # Ajout taille
        # axisLabel = QLabel(f"Axe: {self.NoMotor}")
        # axisLabel.setStyleSheet("color: #888; font: 8pt;")  # Ajout taille
        # rackInfoLayout.addWidget(rackLabel)
        # rackInfoLayout.addStretch()
        # rackInfoLayout.addWidget(axisLabel)
        # infoLayout.addLayout(rackInfoLayout)
        
        # État
        stateLayout = QHBoxLayout()
        stateLabel = QLabel("state:")
        stateLabel.setStyleSheet("color: #888; font: 8pt;")
        self.enPosition = QLineEdit()
        self.enPosition.setReadOnly(True)
        self.enPosition.setMaximumHeight(25)  # Réduit de 30 à 25
        self.enPosition.setStyleSheet("""
            QLineEdit {
                font: bold 9pt;
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px;
            }
        """)
        self.enPosition.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.butNegButt = QCheckBox('FDC-')
        self.butNegButt.setEnabled(False)
        self.butNegButt.setStyleSheet("font: 8pt;")
        self.butPosButt = QCheckBox('FDC+')
        self.butPosButt.setEnabled(False)
        self.butPosButt.setStyleSheet("font: 8pt;")
        
        stateLayout.addWidget(stateLabel)
        stateLayout.addWidget(self.enPosition, 2)
        stateLayout.addWidget(self.butNegButt)
        stateLayout.addWidget(self.butPosButt)
        infoLayout.addLayout(stateLayout)
        
        infoGroup.setLayout(infoLayout)
        mainLayout.addWidget(infoGroup)
        
        # ========== POSITION ACTUELLE ==========
        posGroup = QGroupBox("Actual Position ")
        posGroup.setStyleSheet("""
            QGroupBox {
                font: bold 10pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        posGroup.setMaximumHeight(110)  
        
        posLayout = QHBoxLayout()
        posLayout.setSpacing(5)
        
        self.position = QLabel('0.00')
        self.position.setStyleSheet("""
            QLabel {
                font: bold 24pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 6px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)  
        self.position.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position.setMinimumHeight(70) 
        self.position.setMaximumHeight(70)
        
        unitControlLayout = QVBoxLayout()
        unitControlLayout.setSpacing(3)
    
        self.unitBouton = QComboBox()
        self.unitBouton.addItems(['Step', 'um', 'mm', 'ps', '°'])
        self.unitBouton.setCurrentIndex(self.indexUnit)
        self.unitBouton.setStyleSheet("font: 9pt; padding: 3px;")  
        self.unitBouton.setMinimumWidth(70)
        self.unitBouton.setMaximumHeight(25)
        
        self.zeroButton = QPushButton('Zero')
        self.zeroButton.setToolTip('Remettre la position à zéro')
        self.zeroButton.setStyleSheet("padding: 5px; font: 9pt;") 
        self.zeroButton.setMinimumHeight(25)  
        self.zeroButton.setMaximumHeight(25)
        
        unitControlLayout.addWidget(self.unitBouton)
        unitControlLayout.addSpacing(3)
        unitControlLayout.addWidget(self.zeroButton)
        unitControlLayout.addStretch()
        
        posLayout.addWidget(self.position, 3)
        posLayout.addLayout(unitControlLayout, 1)
        
        posGroup.setLayout(posLayout)
        mainLayout.addWidget(posGroup)
        
        # ========== MOUVEMENT ABSOLU ==========
        absGroup = QGroupBox("Absolu Movement ")
        absGroup.setStyleSheet("""
            QGroupBox {
                font: bold 10pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        absGroup.setMaximumHeight(75)  
        absLayout = QHBoxLayout()
        absLayout.setSpacing(5)
        absLayout.setContentsMargins(5, 5, 5, 10)
        
        self.MoveStep = QDoubleSpinBox()
        self.MoveStep.setMaximum(1000000)
        self.MoveStep.setMinimum(-1000000)
        self.MoveStep.setDecimals(2)
        self.MoveStep.setStyleSheet("font: 10pt; padding: 5px; min-height: 25px;")
        self.MoveStep.setMaximumHeight(28)
        
        self.absMvtButton = QToolButton()
        self.absMvtButton.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconPlay});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconPlay});background-color: gray;}}"
        )
        self.absMvtButton.setMinimumSize(40, 40)
        self.absMvtButton.setMaximumSize(40, 40)
        self.absMvtButton.setToolTip('Déplacer à la position absolue')
        
        absLayout.addWidget(self.MoveStep)
        absLayout.addWidget(self.absMvtButton)
        
        absGroup.setLayout(absLayout)
        mainLayout.addWidget(absGroup)
        
        # ========== DÉPLACEMENT RELATIF (JOG) ==========
        jogGroup = QGroupBox("Relative Movement (Jog) ")
        jogGroup.setStyleSheet("""
            QGroupBox {
                font: bold 10pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        jogGroup.setMaximumHeight(80)  # Réduit de 100 à 70
        jogLayout = QHBoxLayout()  # Changé de VBoxLayout à HBoxLayout
        jogLayout.setSpacing(5)
        jogLayout.setContentsMargins(5, 5, 5, 8)
        
        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(1000000)
        self.jogStep.setDecimals(2)
        self.jogStep.setValue(self.jogValue)
        self.jogStep.setStyleSheet("font: 10pt; padding: 5px; min-height: 25px;")
        self.jogStep.setMaximumHeight(28)
        self.jogStep.setMaximumWidth(130)
        
        self.moins = QToolButton()
        self.moins.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconMoins});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconMoins});background-color: gray;}}"
        )
        self.moins.setMinimumSize(50, 50)  
        self.moins.setMaximumSize(50, 50)
        self.moins.setAutoRepeat(True)
        self.moins.setToolTip('Déplacer dans le sens négatif')
        
        self.plus = QToolButton()
        self.plus.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconPlus});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconPlus});background-color: gray;}}"
        )
        self.plus.setMinimumSize(50, 50)
        self.plus.setMaximumSize(50, 50)
        self.plus.setAutoRepeat(True)
        self.plus.setToolTip('Déplacer dans le sens positif')
        
        jogLayout.addWidget(self.moins)
        jogLayout.addWidget(self.jogStep, 1)
        jogLayout.addWidget(self.plus)
        
        jogGroup.setLayout(jogLayout)
        mainLayout.addWidget(jogGroup)
        
        # ========== CONTRÔLES ==========
        controlGroup = QGroupBox("Controls")
        controlGroup.setStyleSheet("""
            QGroupBox {
                font: bold 10pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        controlGroup.setMaximumHeight(160)  # Réduit de 250 à 160
        controlLayout = QHBoxLayout()
         #controlLayout.setSpacing(2)
        
        # Bouton STOP
        self.stopButton = QToolButton()
        self.stopButton.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconStop});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconStop});background-color: gray;}}"
        )
    
        self.stopButton.setMinimumSize(80, 70)
        self.stopButton.setToolTip('Arrêt d\'urgence')
        
        # Boutons d'action
        buttonGrid = QGridLayout()
        buttonGrid.setSpacing(2)
        
        self.showRef = QPushButton('Ref')
        self.showRef.setIcon(QIcon(str(self.iconRef)))
        self.showRef.setIconSize(QSize(24, 24))
        self.scan = QPushButton('Scan')
        self.configButton = QPushButton('⚙️ Config')
        self.configButton.setToolTip('Configurer butées et step')
        
        buttonGrid.addWidget(self.stopButton, 0, 0, 3, 1)               
        buttonGrid.addWidget(self.showRef, 0, 1, 2, 2)
        buttonGrid.addWidget(self.scan, 2, 1, 1, 1)
        buttonGrid.addWidget(self.configButton, 2, 2, 1, 1)
        # Égaliser les hauteurs des lignes
        buttonGrid.setRowStretch(0, 1)
        buttonGrid.setRowStretch(1, 1)
        buttonGrid.setRowStretch(2, 1)

        # S'assurer que showRef peut s'étendre
        self.showRef.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        controlLayout.addLayout(buttonGrid)
        controlGroup.setLayout(controlLayout)

        mainLayout.addWidget(controlGroup)
        
        # ========== RÉFÉRENCES ==========
        self.REF1 = REF1M(num=1)
        self.REF2 = REF1M(num=2)
        self.REF3 = REF1M(num=3)
        self.REF4 = REF1M(num=4)
        self.REF5 = REF1M(num=5)
        self.REF6 = REF1M(num=6)

        refGroup = QGroupBox("Reference")
        refGroup.setStyleSheet("""
            QGroupBox {
                font: bold 10pt;
                color: #aaaaaa;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        grid_layoutRef = QGridLayout()
        grid_layoutRef.setVerticalSpacing(6)  # Réduit de 10 à 6
        grid_layoutRef.setHorizontalSpacing(6)  # Réduit de 10 à 6
        grid_layoutRef.addWidget(self.REF1, 0, 0)
        grid_layoutRef.addWidget(self.REF2, 0, 1)
        grid_layoutRef.addWidget(self.REF3, 1, 0)
        grid_layoutRef.addWidget(self.REF4, 1, 1)
        grid_layoutRef.addWidget(self.REF5, 2, 0)
        grid_layoutRef.addWidget(self.REF6, 2, 1)
        
        refGroup.setLayout(grid_layoutRef)
        self.widget6REF = refGroup
        mainLayout.addWidget(self.widget6REF)

        self.absRef = [self.REF1.ABSref, self.REF2.ABSref, self.REF3.ABSref, 
                       self.REF4.ABSref, self.REF5.ABSref, self.REF6.ABSref]
        self.posText = [self.REF1.posText, self.REF2.posText, self.REF3.posText,
                        self.REF4.posText, self.REF5.posText, self.REF6.posText]
        self.POS = [self.REF1.Pos, self.REF2.Pos, self.REF3.Pos,
                    self.REF4.Pos, self.REF5.Pos, self.REF6.Pos]
        self.Take = [self.REF1.take, self.REF2.take, self.REF3.take,
                     self.REF4.take, self.REF5.take, self.REF6.take]
        
        self.setLayout(mainLayout)
        self.jogStep.setFocus()
        self.refShow()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.thread.positionSleep = 1

    def actionButton(self):
        self.unitBouton.currentIndexChanged.connect(self.unit)
        self.absMvtButton.clicked.connect(self.MOVE)
        self.plus.clicked.connect(self.pMove)
        self.moins.clicked.connect(self.mMove)
        self.scan.clicked.connect(lambda: self.open_widget(self.scanWidget))
        self.configButton.clicked.connect(self.openConfigWidget)
        self.zeroButton.clicked.connect(self.Zero)
        self.stopButton.clicked.connect(self.StopMot)
        self.showRef.clicked.connect(self.refShow)
        #self.presetButton.clicked.connect(self.preset)
        
        iii = 0
        for saveNameButton in self.posText:
            saveNameButton.textChanged.connect(self.savName)
            iii += 1

        for posButton in self.POS:
            posButton.clicked.connect(self.ref)
            
        eee = 0
        for absButton in self.absRef:
            absButton.editingFinished.connect(self.savRef)
            eee += 1

        for takeButton in self.Take:
            takeButton.clicked.connect(self.take)
        
    def open_widget(self, fene):
        if fene.isWinOpen is False:
            fene.show()
            fene.isWinOpen = True
            if fene == self.scanWidget:
                fene.startTrigThread()
        else:
            fene.raise_()
            fene.showNormal()
    
    def openConfigWidget(self):
        """Ouvre le widget de configuration"""
        if self.configWidget is None or not self.configWidget.isVisible():
            self.configWidget = ConfigMotorWidget(motor=self.MOT[0], parent=self)
            self.configWidget.show()
            self.configWidget.isWinOpen = True
            self.addLog("Config", "Ouverture configuration")
        else:
            self.configWidget.raise_()
            self.configWidget.showNormal()
        
    def refShow(self):
        if self.refShowId is True:
            self.widget6REF.show()
            self.refShowId = False
            self.showRef.setText('Hide Ref')
            self.setFixedSize(430, 900)
        else:
            self.widget6REF.hide()
            self.refShowId = True
            self.showRef.setText('Show Ref')
            self.setFixedSize(430, 500)
    
    def MOVE(self):
        a = float(self.MoveStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        
        if a < self.buteNeg[0]:
            self.butNegButt.setChecked(True)
            self.butNegButt.setStyleSheet('color:red')
            self.MOT[0].stopMotor()
            self.addLog("STOP", "⚠️ Butée négative")
        elif a > self.butePos[0]:
            self.butPosButt.setChecked(True)
            self.butPosButt.setStyleSheet('color:red')
            self.MOT[0].stopMotor()
            self.addLog("STOP", "⚠️ Butée positive")
        else:
            self.MOT[0].move(a)
            self.butNegButt.setChecked(False)
            self.butNegButt.setStyleSheet("")
            self.butPosButt.setChecked(False)
            self.butPosButt.setStyleSheet("")
            self.addLog("Move Abs", f"→ {self.MoveStep.value():.2f} {self.unitName}")

    def pMove(self):
        a = float(self.jogStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        
        if b + a > self.butePos[0]:
            self.addLog("STOP", "⚠️ Butée positive")
            self.MOT[0].stopMotor()
            self.butPosButt.setChecked(True)
            self.butPosButt.setStyleSheet('color:red')
        else:
            self.MOT[0].rmove(a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butPosButt.setStyleSheet("")
            self.butNegButt.setStyleSheet("")
            self.addLog("Jog", f"➕ {self.jogStep.value():.2f} {self.unitName}")

    def mMove(self):
        a = float(self.jogStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        
        if b - a < self.buteNeg[0]:
            self.addLog("STOP", "⚠️ Butée négative")
            self.MOT[0].stopMotor()
            self.butNegButt.setChecked(True)
            self.butNegButt.setStyleSheet('color:red')
        else:
            self.MOT[0].rmove(-a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            self.butNegButt.setStyleSheet("")
            self.butPosButt.setStyleSheet("")
            self.addLog("Jog", f"➖ {self.jogStep.value():.2f} {self.unitName}")

    def Zero(self):
        b = self.MOT[0].position()
        self.MOT[0].setzero()
        self.addLog("Zero", f"🔄 Position remise à zéro (était: {b*self.unitChange:.2f} {self.unitName})")

    def RefMark(self): 
        pass

    def unit(self):
        self.indexUnit = self.unitBouton.currentIndex()
        valueJog = self.jogStep.value()/self.unitChange 
        moveVal = self.MoveStep.value()/self.unitChange

        if self.indexUnit == 0:
            self.unitChange = 1
            self.unitName = 'step'
        elif self.indexUnit == 1:
            self.unitChange = float((self.stepmotor[0]))
            self.unitName = 'um'
        elif self.indexUnit == 2:
            self.unitChange = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        elif self.indexUnit == 3:
            self.unitChange = float(self.stepmotor[0]*0.0066666666)
            self.unitName = 'ps'
        elif self.indexUnit == 4:
            self.unitChange = self.stepmotor[0]
            self.unitName = '°'

        if self.unitChange == 0:
            self.unitChange = 1

        self.jogStep.setSuffix(" %s" % self.unitName)
        self.jogStep.setValue(valueJog*self.unitChange)
        self.MoveStep.setValue(moveVal*self.unitChange)
        self.MoveStep.setSuffix(" %s" % self.unitName)

        eee = 0
        for absButton in self.absRef:
            absButton.setValue(float(self.refValueStep[eee] * self.unitChange))
            absButton.setSuffix(" %s" % self.unitName)
            eee += 1
        self.Position(self.Posi)

    def StopMot(self):
        for zzi in range(0, 1):
            self.MOT[zzi].stopMotor()
            self.addLog("STOP", "⏹ Arrêt moteur")

    @pyqtSlot(object)
    def Position(self, Posi):
        self.Posi = Posi
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        b = a
        a = a * self.unitChange

        self.position.setText(str(round(a, 2)) + f" {self.unitName}")
        self.position.setStyleSheet("""
            QLabel {
                font: bold 24pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 15px;
                border: 2px solid #00ff00;
                border-radius: 8px;
            }
        """)
        
        if self.etat != self.etat_old:
            self.etat_old = self.etat
            if self.etat == 'FDC-':
                self.enPosition.setText('⚠️ ' + self.etat)
                self.enPosition.setStyleSheet('font: bold 11pt; color: red; background-color: #2d2d2d; border: 1px solid red; padding: 5px;')
            elif self.etat == 'FDC+':
                self.enPosition.setText('⚠️ FDC +')
                self.enPosition.setStyleSheet('font: bold 11pt; color: red; background-color: #2d2d2d; border: 1px solid red; padding: 5px;')
            elif self.etat == 'Poweroff':
                self.enPosition.setText('❌ Power Off')
                self.enPosition.setStyleSheet('font: bold 11pt; color: red; background-color: #2d2d2d; border: 1px solid red; padding: 5px;')
            elif self.etat == 'mvt':
                self.enPosition.setText('En mouvement...')
                self.enPosition.setStyleSheet('font: bold 11pt; color: white; background-color: #2d2d2d; border: 1px solid #4a9eff; padding: 5px;')
            elif self.etat == 'notconnected':
                self.enPosition.setText('❌ Serveur non connecté')
                self.enPosition.setStyleSheet('font: bold 10pt; color: red; background-color: #2d2d2d; border: 1px solid red; padding: 5px;')
            elif self.etat == 'errorConnect':
                self.enPosition.setText('❌ Équipement non connecté')
                self.enPosition.setStyleSheet('font: bold 10pt; color: red; background-color: #2d2d2d; border: 1px solid red; padding: 5px;')
        if self.etat == 'ok' or self.etat == '?':
            print('ok')
            precis = 2
            positionConnue = 0
            for nbRefInt in range(1, 7):
                if positionConnue == 0:
                    print(self.refValueStep[nbRefInt-1],b)
                    if float(self.refValueStep[nbRefInt-1]) - precis < b < float(self.refValueStep[nbRefInt-1]) + precis:
                        self.enPosition.setText(f'📍 {self.refName[nbRefInt-1]}')
                        self.enPosition.setStyleSheet('font: bold 11pt; color: #4a9eff; background-color: #2d2d2d; border: 1px solid #4a9eff; padding: 5px;')
                        positionConnue = 1

                    else: 
                        self.enPosition.setText('✅')
                        self.enPosition.setStyleSheet('font: bold 11pt; color: #00ff00; background-color: #2d2d2d; border: 1px solid #555; padding: 5px;')


    def Etat(self, etat):
        self.etat = etat

    def take(self):
        sender = QtCore.QObject.sender(self)
        nbRef = str(sender.objectName()[0])
        reply = QMessageBox.question(None, 'Sauvegarder Position ?', 
                                     "Voulez-vous sauvegarder cette position ?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            tpos = float(self.MOT[0].position())
            self.refValueStep[int(nbRef)-1] = tpos
            self.absRef[int(nbRef)-1].setValue(tpos*self.unitChange)
            self.addLog("Référence", f"💾 Ref {nbRef} sauvegardée: {self.absRef[int(nbRef)-1].value():.2f} {self.unitName}")

    def ref(self):
        sender = QtCore.QObject.sender(self)
        reply = QMessageBox.question(None, 'Aller à cette Position ?', 
                                     "Voulez-vous aller à cette position ?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nbRef = str(sender.objectName()[0])
            for i in range(0, 1):
                vref = int(self.refValueStep[int(nbRef)-1])
                if vref < self.buteNeg[i]:
                    self.butNegButt.setChecked(True)
                    self.butNegButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                elif vref > self.butePos[i]:
                    self.butPosButt.setChecked(True)
                    self.butPosButt.setStyleSheet('color:red')
                    self.MOT[i].stopMotor()
                else:
                    self.addLog("Référence", f"📍 Déplacement vers Ref {nbRef}: {self.absRef[int(nbRef)-1].value():.2f} {self.unitName}")
                    self.MOT[i].move(vref)
                    self.butNegButt.setChecked(False)
                    self.butNegButt.setStyleSheet("")
                    self.butPosButt.setChecked(False)
                    self.butPosButt.setStyleSheet("")

    def savName(self):
        sender = QtCore.QObject.sender(self)
        nbRef = sender.objectName()[0]
        vname = self.posText[int(nbRef)-1].text()
        for i in range(0, 1):
            self.refName[int(nbRef)-1] = str(vname)

    def savRef(self):
        sender = QtCore.QObject.sender(self)
        nbRef = sender.objectName()[0]
        vref = int(self.absRef[int(nbRef)-1].value())
        self.refValueStep[int(nbRef)-1] = vref/self.unitChange
    
    def preset(self):
        val, ok = QInputDialog.getDouble(self, 'Définir Position', 
                                        f'Nouvelle position ({self.unitName}):')
        if ok:
            self.addLog("Preset", f"🎯 Position définie: {val:.2f} {self.unitName}")
            val = val / self.unitChange
            self.MOT[0].setPosition(int(val))
            
    def addLog(self, action, details=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        self.actionLog.append(log_entry)
    
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
        time.sleep(1)
        event.accept()

    def fini(self):
        self.thread.stopThread()
        self.isWinOpen = False
        self.updateDB()

        if self.scanWidget.isWinOpen is True:
            self.scanWidget.close()
        time.sleep(0.05)


class REF1M(QWidget):
    '''Widget de référence modernisé'''
    def __init__(self, num=0, parent=None):
        super(REF1M, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.id = num
        
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.setSpacing(5)
        
        # Nom de la référence
        self.posText = QLineEdit('ref')
        self.posText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.posText.setStyleSheet("font: bold 11pt; padding: 5px;")
        self.posText.setObjectName('%s' % self.id)
        mainLayout.addWidget(self.posText)
        
        # Boutons et valeur
        controlLayout = QHBoxLayout()
        
        # Bouton Take
        self.iconTake = pathlib.PurePosixPath(pathlib.Path(self.icon + "disquette.png"))
        self.take = QToolButton()
        self.take.setObjectName('%s'% self.id)
        self.take.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconTake});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconTake});background-color: gray;}}"
        )
        self.take.setFixedSize(35, 35)
        self.take.setToolTip('Sauvegarder position actuelle')
        
        # Bouton Go
        self.iconGo = pathlib.PurePosixPath(pathlib.Path(self.icon + "go.png"))
        self.Pos = QToolButton()
        self.Pos.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconGo});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconGo});background-color: gray;}}"
        )
        self.Pos.setFixedSize(35, 35)
        self.Pos.setObjectName('%s' % self.id)
        self.Pos.setToolTip('Aller à cette position')
        
        controlLayout.addWidget(self.take)
        controlLayout.addWidget(self.Pos)
        mainLayout.addLayout(controlLayout)
        
        # Valeur position
        valueLayout = QHBoxLayout()
        posLabel = QLabel('Pos:')
        posLabel.setStyleSheet("font: 9pt; color: #888;")
        
        self.ABSref = QDoubleSpinBox()
        self.ABSref.setMaximum(500000000)
        self.ABSref.setMinimum(-500000000)
        self.ABSref.setValue(0)
        self.ABSref.setObjectName('%s' % self.id)
        self.ABSref.setStyleSheet("font: 10pt; padding: 3px;")
        
        valueLayout.addWidget(posLabel)
        valueLayout.addWidget(self.ABSref)
        mainLayout.addLayout(valueLayout)
        
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
    import time
    POS = QtCore.pyqtSignal(object)
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mot=''):
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
                Posi = (self.MOT.position())
                time.sleep(self.positionSleep)
                # print(f"positiosleep {self.positionSleep}")
                etat = self.MOT.etatMotor()
                try:
                    if self.Posi_old != Posi or self.etat_old != etat:
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


class LogWindow(QDialog):
    """Fenêtre de log modernisée"""
    
    def __init__(self, parent=None):
        super(LogWindow, self).__init__(parent)
        self.setWindowTitle("📋 Historique des Actions")
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        title = QLabel("Dernières actions (max 20)")
        title.setStyleSheet("font: bold 12pt; color: #4a9eff;")
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
            elif 'config' in action.lower():
                color = "#9775fa"
                icon = "⚙️"
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
    appli.exec_()