
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Graphique pour le pilotage de deux moteurs tilt
Modified on 2026/01/30
Version modernisée avec style cohérent
@author: Gautier julien loa
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QWidget, QGroupBox
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from PyQt6.QtWidgets import QComboBox, QLabel, QToolButton, QCheckBox
from PyQt6.QtCore import pyqtSlot, Qt
import qdarkstyle
import pathlib
import time
import sys
import os
import zmq_client_RSAI

import __init__

__version__ = __init__.__version__
__author__ = __init__.__author__


class TILTMOTORGUI(QWidget):
    """
    Interface modernisée pour contrôle de 2 moteurs (Lateral + Vertical)
    """

    def __init__(self, IPLat, NoMotorLat, IPVert, NoMotorVert, nomWin='', nomTilt='', 
                 unit=1, jogValue=100, background='', parent=None, showUnit=False, 
                 invLat=False, invVert=False):
        
        super(TILTMOTORGUI, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep

        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.showUnit = showUnit
        
        # Icons
        self.iconFlecheHaut = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechehaut.png"))
        self.iconFlecheBas = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechebas.png"))
        self.iconFlecheDroite = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechedroite.png"))
        self.iconFlecheGauche = pathlib.PurePosixPath(pathlib.Path(self.icon + "flechegauche.png"))
        self.iconStop = pathlib.PurePosixPath(pathlib.Path(self.icon + "close.png"))
        
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.indexUnit = unit
        self.jogValue = jogValue
        self.nomTilt = nomTilt
        
        if background != "":
            self.setStyleSheet("background-color:" + background)
        
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.version = __version__
        self.inv = [invLat, invVert]
        
        self.MOT = [0, 0]
        self.MOT[0] = zmq_client_RSAI.MOTORRSAI(IPLat, NoMotorLat)
        self.MOT[1] = zmq_client_RSAI.MOTORRSAI(IPVert, NoMotorVert)
        
        self.stepmotor = [0, 0]
        self.butePos = [0, 0]
        self.buteNeg = [0, 0]
        self.name = [0, 0]
        
        for zzi in range(0, 2):
            self.stepmotor[zzi] = float((self.MOT[zzi].getStepValue()))
            self.butePos[zzi] = float(self.MOT[zzi].getButLogPlusValue())
            self.buteNeg[zzi] = float(self.MOT[zzi].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[zzi].getName())
        
        self.unitChangeLat = self.indexUnit
        self.unitChangeVert = self.indexUnit
        self.setWindowTitle(f"{nomWin} : {IPLat} [M{NoMotorLat}]  {IPVert} [M{NoMotorVert}]")
        
        self.threadLat = PositionThread(mot=self.MOT[0])
        self.threadLat.POS.connect(self.PositionLat)
        time.sleep(0.12)
        
        self.threadVert = PositionThread(mot=self.MOT[1])
        self.threadVert.POS.connect(self.PositionVert)
        
        # Initialisation des unités
        if self.indexUnit == 0:
            self.unitChangeLat = 1
            self.unitName = 'step'
        elif self.indexUnit == 1:
            self.unitChangeLat = float((self.stepmotor[0]))
            self.unitName = 'um'
        elif self.indexUnit == 2:
            self.unitChangeLat = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        elif self.indexUnit == 3:
            self.unitChangeLat = float(self.stepmotor[0]*0.0066666666)
            self.unitName = 'ps'
        elif self.indexUnit == 4:
            self.unitChangeLat = self.stepmotor[0]
            self.unitName = '°'
        
        self.setup()
        self.unitTrans()
        self.jogStep.setValue(self.jogValue)
        self.actionButton()

    def setup(self):
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(4)
        mainLayout.setContentsMargins(8, 8, 8, 8)
        txt = f"{self.nomTilt }"

        # ========== GROUPE UNIQUE ==========
        mainGroup = QGroupBox(txt)
        mainGroup.setStyleSheet("""
            QGroupBox {
                font: bold 14pt;
                color: #4a9eff;
                margin-top: 5px;
                padding-top: 15px;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        groupLayout = QVBoxLayout()
        groupLayout.setSpacing(8)
        
        # Ligne titre avec nom en bleu + unités + butées
        hboxTitre = QHBoxLayout()
        

        self.stopButton = QToolButton()
        self.stopButton.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconStop});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconStop});background-color: gray;}}"
        )
        self.stopButton.setFixedSize(70, 50)
        self.stopButton.setToolTip('⏹ Arrêt d\'urgence')
        hboxTitre.addWidget(self.stopButton)

        if self.showUnit is True:
            self.unitTransBouton = QComboBox()
            self.unitTransBouton.setMaximumWidth(90)
            self.unitTransBouton.setMinimumWidth(90)
            self.unitTransBouton.setStyleSheet("font: bold 10pt; padding: 5px;")
            self.unitTransBouton.addItems(['Step', 'um', 'mm', 'ps'])
            self.unitTransBouton.setCurrentIndex(self.indexUnit)
            hboxTitre.addWidget(self.unitTransBouton)
        
        hboxTitre.addStretch()
        
        self.butNegButt = QCheckBox('FDC-')
        self.butNegButt.setEnabled(False)
        self.butNegButt.setStyleSheet("font: 9pt;")
        hboxTitre.addWidget(self.butNegButt)
        
        self.butPosButt = QCheckBox('FDC+')
        self.butPosButt.setEnabled(False)
        self.butPosButt.setStyleSheet("font: 9pt;")
        hboxTitre.addWidget(self.butPosButt)
        
        groupLayout.addLayout(hboxTitre)
        
        # Séparateur
        groupLayout.addSpacing(5)
        
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
        self.jogStep.setMaximum(1000000)
        self.jogStep.setDecimals(2)
        self.jogStep.setStyleSheet("font: bold 10pt; padding: 5px;")
        self.jogStep.setValue(self.jogValue)
        self.jogStep.setMaximumWidth(100)
        self.jogStep.setMinimumHeight(30)
        
        grid_layout.addWidget(self.haut, 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.bas, 2, 1, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.gauche, 1, 0, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.droite, 1, 2, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.jogStep, 1, 1, Qt.AlignmentFlag.AlignCenter)
        
        groupLayout.addLayout(grid_layout)
        
        # Séparateur
        groupLayout.addSpacing(10)
        
        # Positions et Zero en ligne sous les flèches
        positionsLayout = QHBoxLayout()
        positionsLayout.setSpacing(15)
        
        # Lateral (Horizontal)
        latLayout = QVBoxLayout()
        latLayout.setSpacing(3)
        latLabel = QLabel('Lateral')
        latLabel.setStyleSheet("font: bold 10pt; color: #888;")
        latLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.position_Lat = QLabel('0.00')
        self.position_Lat.setStyleSheet("""
            QLabel {
                font: bold 18pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 6px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)
        self.position_Lat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_Lat.setMinimumHeight(45)
        self.position_Lat.setMinimumWidth(150)
        
        self.zeroButtonLat = QPushButton('⓪ Zero')
        self.zeroButtonLat.setStyleSheet("padding: 5px; font: bold 9pt;")
        self.zeroButtonLat.setMaximumHeight(30)
        
        latLayout.addWidget(latLabel)
        latLayout.addWidget(self.position_Lat)
        latLayout.addWidget(self.zeroButtonLat)
        positionsLayout.addLayout(latLayout)
        
        # Vertical
        vertLayout = QVBoxLayout()
        vertLayout.setSpacing(3)
        vertLabel = QLabel('Vertical')
        vertLabel.setStyleSheet("font: bold 10pt; color: #888;")
        vertLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.position_Vert = QLabel('0.00')
        self.position_Vert.setStyleSheet("""
            QLabel {
                font: bold 18pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 6px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)
        self.position_Vert.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_Vert.setMinimumHeight(45)
        self.position_Vert.setMinimumWidth(150)
        
        self.zeroButtonVert = QPushButton('⓪ Zero')
        self.zeroButtonVert.setStyleSheet("padding: 5px; font: bold 9pt;")
        self.zeroButtonVert.setMaximumHeight(30)
        
        vertLayout.addWidget(vertLabel)
        vertLayout.addWidget(self.position_Vert)
        vertLayout.addWidget(self.zeroButtonVert)
        positionsLayout.addLayout(vertLayout)
        
        groupLayout.addLayout(positionsLayout)
        
        # Séparateur
        groupLayout.addSpacing(10)
        
        
        mainGroup.setLayout(groupLayout)
        mainLayout.addWidget(mainGroup)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)

    def startThread2(self):
        self.threadLat.ThreadINIT()
        self.threadLat.start()
        time.sleep(0.5)
        self.threadVert.ThreadINIT()
        self.threadVert.start()

    def actionButton(self):
        if self.showUnit is True:
            self.unitTransBouton.currentIndexChanged.connect(self.unitTrans)
        
        self.haut.clicked.connect(self.hMove)
        self.bas.clicked.connect(self.bMove)
        self.gauche.clicked.connect(self.gMove)
        self.droite.clicked.connect(self.dMove)
        
        self.zeroButtonLat.clicked.connect(self.ZeroLat)
        self.zeroButtonVert.clicked.connect(self.ZeroVert)
        
        self.stopButton.clicked.connect(self.StopMot)

    def gMove(self):
        '''Action bouton gauche'''
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeLat)
        b = self.MOT[0].position()
        
        if self.inv[0] is False:
            if b - a < self.buteNeg[0]:
                print("⚠️ STOP : Butée Négative")
                self.MOT[0].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
            else:
                self.MOT[0].rmove(-a)
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                #print(f"⬅️ Jog gauche {self.jogStep.value():.2f} {self.unitName}")
        else:
            if b + a > self.butePos[0]:
                print("⚠️ STOP : Butée Positive")
                self.MOT[0].stopMotor()
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
            else:
                self.MOT[0].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                #print(f"⬅️ Jog gauche {self.jogStep.value():.2f} {self.unitName}")

    def dMove(self):
        '''Action bouton droite'''
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeLat)
        b = self.MOT[0].position()
        
        if self.inv[0] is False:
            if b + a > self.butePos[0]:
                print("⚠️ STOP : Butée Positive")
                self.MOT[0].stopMotor()
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
            else:
                self.MOT[0].rmove(+a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                #print(f"➡️ Jog droite {self.jogStep.value():.2f} {self.unitName}")
        else:
            if b - a < self.buteNeg[0]:
                print("⚠️ STOP : Butée Négative")
                self.MOT[0].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
            else:
                self.MOT[0].rmove(-a)
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                #print(f"➡️ Jog droite {self.jogStep.value():.2f} {self.unitName}")

    def hMove(self):
        '''Action bouton haut'''
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeVert)
        b = self.MOT[1].position()
        
        if self.inv[1] is False:
            if b + a > self.butePos[1]:
                print("⚠️ STOP : Butée Positive")
                self.MOT[1].stopMotor()
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
            else:
                self.MOT[1].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                #print(f"⬆️ Jog haut {self.jogStep.value():.2f} {self.unitName}")
        else:
            if b - a < self.buteNeg[1]:
                print("⚠️ STOP : Butée Négative")
                self.MOT[1].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
            else:
                self.MOT[1].rmove(-a)
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                #print(f"⬆️ Jog haut {self.jogStep.value():.2f} {self.unitName}")

    def bMove(self):
        '''Action bouton bas'''
        a = float(self.jogStep.value())
        a = float(a / self.unitChangeVert)
        b = self.MOT[1].position()
        
        if self.inv[1] is False:
            if b - a < self.buteNeg[1]:
                print("⚠️ STOP : Butée Négative")
                self.MOT[1].stopMotor()
                self.butNegButt.setChecked(True)
                self.butNegButt.setStyleSheet('color:red')
            else:
                self.MOT[1].rmove(-a)
                self.butNegButt.setChecked(False)
                self.butNegButt.setStyleSheet('')
                #print(f"⬇️ Jog bas {self.jogStep.value():.2f} {self.unitName}")
        else:
            if b + a > self.butePos[1]:
                print("⚠️ STOP : Butée Positive")
                self.MOT[1].stopMotor()
                self.butPosButt.setChecked(True)
                self.butPosButt.setStyleSheet('color:red')
            else:
                self.MOT[1].rmove(a)
                self.butPosButt.setChecked(False)
                self.butPosButt.setStyleSheet('')
                #print(f"⬇️ Jog bas {self.jogStep.value():.2f} {self.unitName}")

    def ZeroLat(self):
        '''Reset Lateral to zero'''
        pos_avant = self.MOT[0].position() * self.unitChangeLat
        self.MOT[0].setzero()
        print(f"🔄 Lateral remis à zéro (était: {pos_avant:.2f} {self.unitName})")

    def ZeroVert(self):
        '''Reset Vertical to zero'''
        pos_avant = self.MOT[1].position() * self.unitChangeVert
        self.MOT[1].setzero()
        print(f"🔄 Vertical remis à zéro (était: {pos_avant:.2f} {self.unitName})")

    def RefMark(self):
        pass

    def unitTrans(self):
        '''Unit change'''
        if self.showUnit is True:
            self.indexUnit = self.unitTransBouton.currentIndex()
        
        valueJog = self.jogStep.value() / self.unitChangeLat
        
        if self.indexUnit == 0:
            self.unitChangeLat = 1
            self.unitChangeVert = 1
            self.unitNameTrans = 'step'
        elif self.indexUnit == 1:
            self.unitChangeLat = float((1*self.stepmotor[0]))
            self.unitChangeVert = float((1*self.stepmotor[1]))
            self.unitNameTrans = 'um'
        elif self.indexUnit == 2:
            self.unitChangeLat = float((self.stepmotor[0])/1000)
            self.unitChangeVert = float((self.stepmotor[1])/1000)
            self.unitNameTrans = 'mm'
        elif self.indexUnit == 3:
            self.unitChangeLat = float(1*self.stepmotor[0]*0.0066666666)
            self.unitChangeVert = float(1*self.stepmotor[1]*0.0066666666)
            self.unitNameTrans = 'ps'
            
        if self.unitChangeLat == 0:
            self.unitChangeLat = 1
        if self.unitChangeVert == 0:
            self.unitChangeVert = 1
        
        self.unitName = self.unitNameTrans
        self.jogStep.setSuffix(f" {self.unitNameTrans}")
        self.jogStep.setValue(valueJog * self.unitChangeLat)

    def StopMot(self):
        '''Stop all motors'''
        for zzi in range(0, 2):
            self.MOT[zzi].stopMotor()
        print("⏹ Arrêt de tous les moteurs")

    @pyqtSlot(object)
    def PositionLat(self, Posi):
        '''Position Lateral display'''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        a = a * self.unitChangeLat
        
        if self.etat == 'FDC-':
            self.position_Lat.setText('⚠️ FDC-')
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 14pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'FDC+':
            self.position_Lat.setText('⚠️ FDC+')
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 14pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'Poweroff':
            self.position_Lat.setText('❌ Power Off')
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 12pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'mvt':
            self.position_Lat.setText('Mvt...')
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 14pt;
                    color: white;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #4a9eff;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'notconnected':
            self.position_Lat.setText('❌ Non connecté')
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 9pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'errorConnect':
            self.position_Lat.setText('❌ Erreur')
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 9pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        else:
            self.position_Lat.setText(f"{round(a, 2)} {self.unitName}")
            self.position_Lat.setStyleSheet("""
                QLabel {
                    font: bold 18pt;
                    color: #00ff00;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #00ff00;
                    border-radius: 5px;
                }
            """)

    @pyqtSlot(object)
    def PositionVert(self, Posi):
        '''Position Vertical display'''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        a = a * self.unitChangeVert
        
        if self.etat == 'FDC-':
            self.position_Vert.setText('⚠️ FDC-')
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 14pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'FDC+':
            self.position_Vert.setText('⚠️ FDC+')
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 14pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'Poweroff':
            self.position_Vert.setText('❌ Power Off')
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 12pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'mvt':
            self.position_Vert.setText('Mvt...')
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 14pt;
                    color: white;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #4a9eff;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'notconnected':
            self.position_Vert.setText('❌ Non connecté')
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 9pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'errorConnect':
            self.position_Vert.setText('❌ Erreur')
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 9pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        else:
            self.position_Vert.setText(f"{round(a, 2)} {self.unitName}")
            self.position_Vert.setStyleSheet("""
                QLabel {
                    font: bold 18pt;
                    color: #00ff00;
                    background-color: #1e1e1e;
                    padding: 6px;
                    border: 2px solid #00ff00;
                    border-radius: 5px;
                }
            """)

    def closeEvent(self, event):
        """When closing the window"""
        self.fini()
        time.sleep(0.1)
        event.accept()

    def fini(self):
        '''Stop threads on close'''
        self.threadLat.stopThread()
        self.threadVert.stopThread()
        self.isWinOpen = False
        time.sleep(0.1)


class PositionThread(QtCore.QThread):
    '''Second thread to display position'''
    import time
    POS = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, mot=''):
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


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    mot5 = TILTMOTORGUI(IPLat="10.0.1.30", NoMotorLat=12, 
                        IPVert="10.0.1.30", NoMotorVert=13, 
                        nomWin='Tilt Turning', nomTilt='Tilt Control',
                        showUnit=True, invLat=True, invVert=True)
    mot5.show()
    mot5.startThread2()
    appli.exec()