#! /home/sallejaune/loaenv/bin/python3.12
# -*- coding: utf-8 -*-
"""
Created on Sat 18 10 2024
Modified on 30 January 2026
@author: juliengautier
Version modernisée avec style cohérent
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget, QGroupBox
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QPushButton, QDoubleSpinBox, QToolButton
from PyQt6.QtWidgets import QComboBox, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import sys
import time
import os
import qdarkstyle
import pathlib
import zmq_client_RSAI


class ONEMOTOR(QWidget):

    def __init__(self, IpAdress, NoMotor, nomWin='', unit=2, jogValue=1):

        super(ONEMOTOR, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.IpAdress = IpAdress
        self.NoMotor = NoMotor
        self.nomWin = nomWin
        self.isWinOpen = False
        self.indexUnit = unit
        self.jogValue = jogValue
        
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        # Icons
        self.iconMoins = pathlib.PurePosixPath(pathlib.Path(self.icon + "moinsBleu.png"))
        self.iconPlus = pathlib.PurePosixPath(pathlib.Path(self.icon + "plusBleu.png"))
        self.iconStop = pathlib.PurePosixPath(pathlib.Path(self.icon + "close.png"))
        
        self.MOT = zmq_client_RSAI.MOTORRSAI(self.IpAdress, self.NoMotor)
        self.name = str(self.MOT.getName())
        self.equipementName = str(self.MOT.getEquipementName())
        self.setWindowTitle(f"{self.nomWin}{self.equipementName} ({self.IpAdress}) [M{self.NoMotor}] {self.name}")
        
        self.stepmotor = float((self.MOT.getStepValue()))
        self.butePos = float(self.MOT.getButLogPlusValue())
        self.buteNeg = float(self.MOT.getButLogMoinsValue())

        self.thread2 = PositionThread(mot=self.MOT, parent=self)
        self.thread2.POS.connect(self.Position)

        # Initialisation des unités
        if self.indexUnit == 0:
            self.unitChange = 1
            self.unitName = 'step'
        elif self.indexUnit == 1:
            self.unitChange = float((1/self.stepmotor))
            self.unitName = 'um'
        elif self.indexUnit == 2:
            self.unitChange = float((1000*(1/self.stepmotor)))
            self.unitName = 'mm'
        elif self.indexUnit == 3:
            self.unitChange = float(1/self.stepmotor/0.0066666666)
            self.unitName = 'ps'
        elif self.indexUnit == 4:
            self.unitChange = 1 * float(1/self.stepmotor)
            self.unitName = '°'

        self.setup()
        self.actionButton()
        self.unit()

    def startThread2(self):
        self.thread2.ThreadINIT()
        self.thread2.start()

    def setup(self):
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(6)
        mainLayout.setContentsMargins(8, 8, 8, 8)
        
        txt = f"{self.name }   on rack : {self.equipementName}"
        
        
        # ========== POSITION ==========
        mainGroup= QGroupBox(txt)
        mainGroup.setStyleSheet("""
            QGroupBox {
                font: bold 14pt;
                color: #4a9eff;
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
        mainGroup.setMaximumHeight(180)
        
        groupLayout = QVBoxLayout()
        groupLayout.setSpacing(10)
        
        # Première ligne : Position + Unité + Zero
        posLayout = QHBoxLayout()
        posLayout.setSpacing(8)
        
        self.position = QLabel('0.00')
        self.position.setStyleSheet("""
            QLabel {
                font: bold 28pt;
                color: #00ff00;
                background-color: #1e1e1e;
                padding: 10px;
                border: 2px solid #00ff00;
                border-radius: 5px;
            }
        """)
        self.position.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position.setMinimumHeight(70)
        
        unitControlLayout = QVBoxLayout()
        unitControlLayout.setSpacing(5)
        
        self.unitButton = QComboBox()
        self.unitButton.addItems(['Step', 'um', 'mm', 'ps', '°'])
        self.unitButton.setCurrentIndex(self.indexUnit)
        self.unitButton.setMinimumWidth(80)
        self.unitButton.setMaximumWidth(80)
        self.unitButton.setMaximumHeight(50)
        self.unitButton.setStyleSheet("font: bold 10pt; padding: 5px;")
        
        self.zeroButton = QPushButton('⓪ Zero')
        self.zeroButton.setToolTip('Remettre la position à zéro')
        self.zeroButton.setStyleSheet("padding: 6px; font: bold 8pt;")
        self.zeroButton.setMaximumWidth(80)
        self.zeroButton.setMaximumHeight(30)
        
        unitControlLayout.addWidget(self.unitButton)
        unitControlLayout.addSpacing(10)
        unitControlLayout.addWidget(self.zeroButton)
        
        posLayout.addWidget(self.position, 3)
        posLayout.addLayout(unitControlLayout, 1)
        
        groupLayout.addLayout(posLayout)
        
        # Deuxième ligne : Stop + Jog
        controlLayout = QHBoxLayout()
        controlLayout.setSpacing(10)
        
        self.stopButton = QToolButton()
        self.stopButton.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconStop});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconStop});background-color: gray;}}"
        )
        self.stopButton.setFixedSize(60, 60)
        self.stopButton.setToolTip('⏹ Arrêt d\'urgence')
        controlLayout.addWidget(self.stopButton)
        
        self.moins = QToolButton()
        self.moins.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconMoins});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconMoins});background-color: gray;}}"
        )
        self.moins.setFixedSize(50, 50)
        self.moins.setAutoRepeat(True)
        self.moins.setToolTip('Déplacer dans le sens négatif')
        controlLayout.addWidget(self.moins)
        
        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(10000)
        self.jogStep.setDecimals(2)
        self.jogStep.setValue(self.jogValue)
        self.jogStep.setStyleSheet("font: bold 11pt; padding: 8px;")
        self.jogStep.setMinimumHeight(40)
        controlLayout.addWidget(self.jogStep, 1)
        
        self.plus = QToolButton()
        self.plus.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconPlus});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconPlus});background-color: gray;}}"
        )
        self.plus.setFixedSize(50, 50)
        self.plus.setAutoRepeat(True)
        self.plus.setToolTip('Déplacer dans le sens positif')
        controlLayout.addWidget(self.plus)
        
        groupLayout.addLayout(controlLayout)
        mainGroup.setLayout(groupLayout)
        mainLayout.addWidget(mainGroup)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)

    def actionButton(self):
        self.plus.clicked.connect(self.pMove)
        self.moins.clicked.connect(self.mMove)
        self.zeroButton.clicked.connect(self.Zero)
        self.stopButton.clicked.connect(self.StopMot)
        self.unitButton.currentIndexChanged.connect(self.unit)

    def StopMot(self):
        '''Stop motor'''
        self.MOT.stopMotor()
        print("⏹ Arrêt moteur demandé")

    def pMove(self):
        '''Jog +'''
        a = float(self.jogStep.value())
        a = float(a / self.unitChange)
        b = self.MOT.position()
        
        if b + a > self.butePos:
            print("⚠️ STOP : Butée Positive")
            self.MOT.stopMotor()
        else:
            self.MOT.rmove(a)
            print(f"➕ Jog +{self.jogStep.value():.2f} {self.unitName}")

    def mMove(self):
        '''Jog -'''
        a = float(self.jogStep.value())
        a = float(a / self.unitChange)
        b = self.MOT.position()
        
        if b - a < self.buteNeg:
            print("⚠️ STOP : Butée Négative")
            self.MOT.stopMotor()
        else:
            self.MOT.rmove(-a)
            print(f"➖ Jog -{self.jogStep.value():.2f} {self.unitName}")

    def Zero(self):
        '''Reset position to zero'''
        pos_avant = self.MOT.position() * self.unitChange
        self.MOT.setzero()
        print(f"🔄 Position remise à zéro (était: {pos_avant:.2f} {self.unitName})")

    def unit(self):
        '''Unit change'''
        self.indexUnit = self.unitButton.currentIndex()
        valueJog = self.jogStep.value() / self.unitChange
        
        if self.indexUnit == 0:
            self.unitChange = 1
            self.unitName = 'step'
        elif self.indexUnit == 1:
            self.unitChange = float(1/(self.stepmotor))
            self.unitName = 'um'
        elif self.indexUnit == 2:
            self.unitChange = float(1/(self.stepmotor/1000))
            self.unitName = 'mm'
        elif self.indexUnit == 3:
            self.unitChange = float(1/self.stepmotor*0.0066666666)
            self.unitName = 'ps'
        elif self.indexUnit == 4:
            self.unitChange = 1/self.stepmotor
            self.unitName = '°'
            
        if self.unitChange == 0:
            self.unitChange = 1
        
        self.jogStep.setSuffix(f" {self.unitName}")
        self.jogStep.setValue(valueJog * self.unitChange)

    def Position(self, Posi):
        '''Position display from thread'''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        a = a * self.unitChange
        
        if self.etat == 'FDC-':
            self.position.setText('⚠️ FDC-')
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 20pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 10px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'FDC+':
            self.position.setText('⚠️ FDC+')
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 20pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 10px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'Poweroff':
            self.position.setText('❌ Power Off')
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 18pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 10px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'mvt':
            self.position.setText('En mouvement...')
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 18pt;
                    color: white;
                    background-color: #1e1e1e;
                    padding: 10px;
                    border: 2px solid #4a9eff;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'notconnected':
            self.position.setText('❌ Serveur non connecté')
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 12pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 10px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        elif self.etat == 'errorConnect':
            self.position.setText('❌ Équipement non connecté')
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 12pt;
                    color: #ff6b6b;
                    background-color: #1e1e1e;
                    padding: 10px;
                    border: 2px solid #ff6b6b;
                    border-radius: 5px;
                }
            """)
        else:
            self.position.setText(f"{round(a, 2)} {self.unitName}")
            self.position.setStyleSheet("""
                QLabel {
                    font: bold 28pt;
                    color: #00ff00;
                    background-color: #1e1e1e;
                    padding: 10px;
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
        '''Stop thread on close'''
        self.thread2.stopThread()
        self.isWinOpen = False
        time.sleep(0.1)


class PositionThread(QtCore.QThread):
    '''Second thread to display the position'''
    POS = QtCore.pyqtSignal(object)
    ETAT = QtCore.pyqtSignal(str)

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
                time.sleep(0.1)
                
                try:
                    etat = self.MOT.etatMotor()
                    time.sleep(0.1)
                    self.POS.emit([Posi, etat])
                    time.sleep(0.1)
                except Exception as e:
                    print(e, 'Error emit')

    def ThreadINIT(self):
        self.stop = False

    def stopThread(self):
        self.stop = True
        time.sleep(0.1)


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    mot5 = ONEMOTOR(IpAdress="10.0.1.30", NoMotor=12, unit=1, jogValue=100)
    mot5.show()
    mot5.startThread2()
    appli.exec()