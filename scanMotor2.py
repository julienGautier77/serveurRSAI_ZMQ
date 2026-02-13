#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de scan moteur synchronisé avec le serveur de tir ZMQ.
Style modernisé cohérent avec oneMotorGui.

@author: juliengautier
"""

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QMessageBox, QCheckBox
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout
from PyQt6.QtWidgets import QDoubleSpinBox, QProgressBar, QComboBox, QLabel, QLineEdit
from PyQt6.QtWidgets import QGroupBox, QToolButton
from PyQt6.QtGui import QIcon
import sys
import time
import qdarkstyle
import numpy as np
import pathlib
import os

try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    print("ZMQ non disponible - pip install pyzmq")
    ZMQ_AVAILABLE = False

import tirSalleJaune as tirSJ


class TirSalleJauneDummy:
    """
    Classe dummy pour simuler tirSalleJaune en mode test.
    """
    
    def __init__(self):
        self.isConnected = False
        print("[DUMMY] TirSalleJaune DUMMY initialisé")
    
    def tirConnect(self):
        print("[DUMMY] Connexion laser simulée")
        self.isConnected = True
        return True
    
    def disconnect(self):
        print("[DUMMY] Déconnexion simulée")
        self.isConnected = False
        return False
    
    def Tir(self):
        print("[DUMMY] Tir unique simulé")
        time.sleep(0.1)
        return True
    
    def multi_shot(self, freq, nb_tir):
        freq_map = {0: 0.1, 1: 0.2, 2: 0.5, 3: 1.0}
        freq_hz = freq_map.get(freq, 0.1)
        print(f"[DUMMY] Multi-shot: {nb_tir} tirs @ {freq_hz} Hz")
        return True
    
    def stopTir(self):
        print("[DUMMY] Stop tir simulé")


# Style commun pour les GroupBox
GROUPBOX_STYLE = """
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
"""

GROUPBOX_STYLE_TITLE = """
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
"""


class SCAN(QWidget):
    """
    Widget de scan moteur synchronisé avec serveur de tir.
    """
    
    def __init__(self, MOT, parent=None):
        super(SCAN, self).__init__(parent)
        
        self.isWinOpen = False
        self.parent = parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.MOT = MOT
        self.indexUnit = 1
        
        # Configuration
        self.p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(self.p.parent) + sepa + 'icons' + sepa
        
        # Icons
        self.iconPlay = pathlib.PurePosixPath(pathlib.Path(self.icon + "playGreen.png"))
        self.iconStop = pathlib.PurePosixPath(pathlib.Path(self.icon + "close.png"))
        
        # Lecture configuration serveur
        self.configPath = str(self.p.parent) + sepa + 'confServer.ini'
        self.conf = QtCore.QSettings(self.configPath, QtCore.QSettings.Format.IniFormat)
        
        self.server_ip = self.conf.value('SHOTSERVER/server_host', '127.0.0.1')
        self.sub_port = int(self.conf.value('SHOTSERVER/serverPort', 5009))
        
        # Mode dummy
        dummyValue = self.conf.value('SHOTSERVER/modedummy', 'False')
        self.dummyMode = str(dummyValue).lower() in ('true', '1', 'yes')
        
        # Connexion ZMQ
        self.context = None
        self.sub_socket = None
        self.zmq_connected = False
        
        # Classe dummy
        self.tirDummy = TirSalleJauneDummy()
        
        try:
            self.name = self.MOT.name
            self.stepmotor = 1 / self.MOT.getStepValue()
            self.setWindowTitle(
                f'Scan : {self.MOT.getEquipementName()} ({self.MOT.IpAddress}) '
                f'[M{self.MOT.NoMotor}] {self.MOT.name}'
            )
        except Exception as e:
            print(f'Erreur initialisation scan: {e}')
            self.name = "Unknown"
            self.stepmotor = 1

        self.setup()
        self.actionButton()
        self.unit()
        
        # Thread de scan
        self.threadScan = ThreadScan(self)
        self.threadScan.nbRemain.connect(self.updateProgress)
        self.threadScan.info.connect(self.updateInfo)
        self.threadScan.finished.connect(self.onScanFinished)
        
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))

    def getTirModule(self):
        if self.dummyMode:
            return self.tirDummy
        return tirSJ

    def connect_zmq(self):
        if not ZMQ_AVAILABLE:
            self.updateConnectionStatus(False, "ZMQ non disponible")
            return False
        
        try:
            self.context = zmq.Context()
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.connect(f"tcp://{self.server_ip}:{self.sub_port}")
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "SHOOT")
            self.sub_socket.setsockopt(zmq.RCVTIMEO, 1000)
            
            self.zmq_connected = True
            self.updateConnectionStatus(True, f"{self.server_ip}:{self.sub_port}")
            print(f"ZMQ connecté à {self.server_ip}:{self.sub_port}")
            return True
            
        except Exception as e:
            self.updateConnectionStatus(False, f"Erreur: {e}")
            print(f"Erreur connexion ZMQ: {e}")
            self.zmq_connected = False
            return False

    def disconnect_zmq(self):
        if self.sub_socket:
            try:
                self.sub_socket.close()
            except:
                pass
            self.sub_socket = None
        
        if self.context:
            try:
                self.context.term()
            except:
                pass
            self.context = None
        
        self.zmq_connected = False
        self.updateConnectionStatus(False, "Déconnecté")
        print("ZMQ déconnecté")

    def updateConnectionStatus(self, connected, message=""):
        if connected:
            self.connectionStatus.setText("● Connecté")
            self.connectionStatus.setStyleSheet("color: #00ff00; font: bold 9pt;")
        else:
            self.connectionStatus.setText("● Déconnecté")
            self.connectionStatus.setStyleSheet("color: #ff6b6b; font: bold 9pt;")
        
        if message:
            self.connectionInfo.setText(message)

    def setup(self):
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(6)
        mainLayout.setContentsMargins(8, 8, 8, 8)
        
        # ========== TITRE ==========
        titleGroup = QGroupBox(f"Scan - {self.name}")
        titleGroup.setStyleSheet(GROUPBOX_STYLE_TITLE)
        titleGroup.setMaximumHeight(80)
        
        titleLayout = QHBoxLayout()
        titleLayout.setSpacing(10)
        
        # Unité
        self.unitBouton = QComboBox()
        self.unitBouton.addItems(['Step', 'µm', 'mm', 'ps', '°'])
        self.unitBouton.setCurrentIndex(self.indexUnit)
        self.unitBouton.setStyleSheet("font: 9pt; padding: 3px;")
        self.unitBouton.setMaximumWidth(70)
        
        titleLayout.addWidget(QLabel("Unité:"))
        titleLayout.addWidget(self.unitBouton)
        titleLayout.addStretch()
        
        # Mode dummy
        self.dummyCheckbox = QCheckBox("Mode Dummy")
        self.dummyCheckbox.setChecked(self.dummyMode)
        self.dummyCheckbox.setStyleSheet("color: orange; font: 9pt;")
        titleLayout.addWidget(self.dummyCheckbox)
        
        titleGroup.setLayout(titleLayout)
        mainLayout.addWidget(titleGroup)
        
        # ========== CONNEXION SERVEUR ==========
        serverGroup = QGroupBox("Shot Server")
        serverGroup.setStyleSheet(GROUPBOX_STYLE)
        serverGroup.setMaximumHeight(100)
        
        serverLayout = QVBoxLayout()
        serverLayout.setSpacing(5)
        
        # Ligne 1: IP et Port
        serverRow1 = QHBoxLayout()
        serverRow1.addWidget(QLabel("IP:"))
        self.serverIpEdit = QLineEdit(self.server_ip)
        self.serverIpEdit.setMaximumWidth(120)
        self.serverIpEdit.setStyleSheet("padding: 3px;")
        serverRow1.addWidget(self.serverIpEdit)
        
        serverRow1.addWidget(QLabel("Port:"))
        self.serverPortEdit = QLineEdit(str(self.sub_port))
        self.serverPortEdit.setMaximumWidth(60)
        self.serverPortEdit.setStyleSheet("padding: 3px;")
        serverRow1.addWidget(self.serverPortEdit)
        
        self.but_reconnect = QPushButton("Reconnecter")
        self.but_reconnect.setMaximumWidth(100)
        self.but_reconnect.setStyleSheet("padding: 5px;")
        serverRow1.addWidget(self.but_reconnect)
        
        serverRow1.addStretch()
        serverLayout.addLayout(serverRow1)
        
        # Ligne 2: Status
        serverRow2 = QHBoxLayout()
        self.connectionStatus = QLabel("● Déconnecté")
        self.connectionStatus.setStyleSheet("color: #ff6b6b; font: bold 9pt;")
        serverRow2.addWidget(self.connectionStatus)
        
        self.connectionInfo = QLabel("")
        self.connectionInfo.setStyleSheet("color: #888; font: 9pt;")
        serverRow2.addWidget(self.connectionInfo)
        serverRow2.addStretch()
        serverLayout.addLayout(serverRow2)
        
        serverGroup.setLayout(serverLayout)
        mainLayout.addWidget(serverGroup)
        
        # ========== PROGRESSION ==========
        progressGroup = QGroupBox("Progression")
        progressGroup.setStyleSheet(GROUPBOX_STYLE)
        progressGroup.setMaximumHeight(90)
        
        progressLayout = QVBoxLayout()
        progressLayout.setSpacing(5)
        
        # Barre de progression
        progressRow1 = QHBoxLayout()
        self.val_nbStepRemain = QLabel('--')
        self.val_nbStepRemain.setStyleSheet("font: bold 11pt; color: #4a9eff;")
        self.val_nbStepRemain.setMinimumWidth(50)
        progressRow1.addWidget(self.val_nbStepRemain)
        
        self.progressBar = QProgressBar()
        self.progressBar.setMinimumWidth(200)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 3px;
            }
        """)
        progressRow1.addWidget(self.progressBar)
        progressLayout.addLayout(progressRow1)
        
        # Info texte
        self.infoText = QLabel('Prêt')
        self.infoText.setStyleSheet("color: #888; font: 9pt;")
        self.infoText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progressLayout.addWidget(self.infoText)
        
        progressGroup.setLayout(progressLayout)
        mainLayout.addWidget(progressGroup)
        
        # ========== PARAMÈTRES SCAN ==========
        scanGroup = QGroupBox("Paramètres Scan")
        scanGroup.setStyleSheet(GROUPBOX_STYLE)
        
        scanLayout = QGridLayout()
        scanLayout.setSpacing(8)
        scanLayout.setContentsMargins(10, 15, 10, 10)
        
        # Ligne 1: Positions
        scanLayout.addWidget(QLabel("Nb positions:"), 0, 0)
        self.val_nbr_step = QDoubleSpinBox()
        self.val_nbr_step.setMaximum(10000)
        self.val_nbr_step.setMinimum(1)
        self.val_nbr_step.setDecimals(0)
        self.val_nbr_step.setValue(10)
        self.val_nbr_step.setStyleSheet("padding: 5px;")
        scanLayout.addWidget(self.val_nbr_step, 0, 1)
        
        scanLayout.addWidget(QLabel("Pas:"), 0, 2)
        self.val_step = QDoubleSpinBox()
        self.val_step.setMaximum(100000)
        self.val_step.setMinimum(-100000)
        self.val_step.setDecimals(3)
        self.val_step.setStyleSheet("padding: 5px;")
        scanLayout.addWidget(self.val_step, 0, 3)
        
        # Ligne 2: Position initiale et finale
        scanLayout.addWidget(QLabel("Position ini:"), 1, 0)
        self.val_ini = QDoubleSpinBox()
        self.val_ini.setMaximum(100000)
        self.val_ini.setMinimum(-100000)
        self.val_ini.setDecimals(3)
        self.val_ini.setStyleSheet("padding: 5px;")
        scanLayout.addWidget(self.val_ini, 1, 1)
        
        scanLayout.addWidget(QLabel("Position fin:"), 1, 2)
        self.val_fin = QDoubleSpinBox()
        self.val_fin.setMaximum(100000)
        self.val_fin.setMinimum(-100000)
        self.val_fin.setDecimals(3)
        self.val_fin.setValue(100)
        self.val_fin.setStyleSheet("padding: 5px;")
        scanLayout.addWidget(self.val_fin, 1, 3)
        
        # Ligne 3: Tirs
        scanLayout.addWidget(QLabel("Tirs/position:"), 2, 0)
        self.val_nbTir = QDoubleSpinBox()
        self.val_nbTir.setMaximum(1000)
        self.val_nbTir.setMinimum(1)
        self.val_nbTir.setDecimals(0)
        self.val_nbTir.setValue(1)
        self.val_nbTir.setStyleSheet("padding: 5px;")
        scanLayout.addWidget(self.val_nbTir, 2, 1)
        
        scanLayout.addWidget(QLabel("Fréquence:"), 2, 2)
        self.val_freq = QComboBox()
        self.val_freq.addItems(['0.1 Hz', '0.2 Hz', '0.5 Hz', '1 Hz'])
        self.val_freq.setCurrentIndex(0)
        self.val_freq.setStyleSheet("padding: 5px;")
        scanLayout.addWidget(self.val_freq, 2, 3)
        
        scanGroup.setLayout(scanLayout)
        mainLayout.addWidget(scanGroup)
        
        # ========== CONTRÔLES ==========
        controlGroup = QGroupBox("Contrôles")
        controlGroup.setStyleSheet(GROUPBOX_STYLE)
        controlGroup.setMaximumHeight(100)
        
        controlLayout = QHBoxLayout()
        controlLayout.setSpacing(15)
        controlLayout.setContentsMargins(10, 15, 10, 10)
        
        # Bouton Start
        self.but_start = QToolButton()
        self.but_start.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconPlay});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconPlay});background-color: gray;}}"
        )
        self.but_start.setMinimumSize(60, 60)
        self.but_start.setMaximumSize(60, 60)
        self.but_start.setToolTip('Démarrer le scan')
        
        # Bouton Stop
        self.but_stop = QToolButton()
        self.but_stop.setStyleSheet(
            f"QToolButton:!pressed{{border-image: url({self.iconStop});background-color: transparent;}}"
            f"QToolButton:pressed{{image: url({self.iconStop});background-color: gray;}}"
        )
        self.but_stop.setMinimumSize(60, 60)
        self.but_stop.setMaximumSize(60, 60)
        self.but_stop.setToolTip('Arrêter le scan')
        self.but_stop.setEnabled(False)
        
        controlLayout.addStretch()
        controlLayout.addWidget(self.but_start)
        controlLayout.addWidget(self.but_stop)
        controlLayout.addStretch()
        
        controlGroup.setLayout(controlLayout)
        mainLayout.addWidget(controlGroup)
        
        mainLayout.addStretch()
        self.setLayout(mainLayout)
        self.setFixedWidth(450)

    def actionButton(self):
        self.unitBouton.currentIndexChanged.connect(self.unit)
        self.val_nbr_step.editingFinished.connect(self.stepChange)
        self.val_ini.editingFinished.connect(self.stepChange)
        self.val_fin.editingFinished.connect(self.stepChange)
        self.val_step.editingFinished.connect(self.changeFinal)
        self.but_start.clicked.connect(self.startScan)
        self.but_stop.clicked.connect(self.stopScan)
        self.but_reconnect.clicked.connect(self.reconnect)
        self.dummyCheckbox.stateChanged.connect(self.toggleDummyMode)

    def toggleDummyMode(self, state):
        self.dummyMode = (state == 2)
        self.conf.setValue('SHOTSERVER/modedummy', str(self.dummyMode))
        
        if self.dummyMode:
            self.dummyCheckbox.setStyleSheet("color: orange; font: bold 9pt;")
            print("Mode DUMMY activé")
        else:
            self.dummyCheckbox.setStyleSheet("color: gray; font: 9pt;")
            print("Mode RÉEL activé")

    def reconnect(self):
        self.disconnect_zmq()
        self.server_ip = self.serverIpEdit.text()
        self.sub_port = int(self.serverPortEdit.text())
        
        self.conf.setValue('SHOTSERVER/server_host', self.server_ip)
        self.conf.setValue('SHOTSERVER/serverPort', self.sub_port)
        
        self.connect_zmq()

    def updateInfo(self, txt):
        self.infoText.setText(txt)

    def updateProgress(self, remaining, total):
        self.val_nbStepRemain.setText(str(remaining))
        self.progressBar.setMaximum(total)
        self.progressBar.setValue(total - remaining)

    def onScanFinished(self):
        self.stopScan()
        self.val_nbStepRemain.setText('Terminé')
        self.infoText.setStyleSheet("color: #00ff00; font: bold 9pt;")

    def stopScan(self):
        self.threadScan.stop = True
        self.MOT.stopMotor()
        
        tir = self.getTirModule()
        if hasattr(tir, 'stopTir'):
            tir.stopTir()
        
        self.setControlsEnabled(True)
        self.but_start.setEnabled(True)
        self.but_stop.setEnabled(False)
        self.infoText.setStyleSheet("color: #888; font: 9pt;")

    def setControlsEnabled(self, enabled):
        self.val_nbr_step.setEnabled(enabled)
        self.val_step.setEnabled(enabled)
        self.val_ini.setEnabled(enabled)
        self.val_fin.setEnabled(enabled)
        self.val_nbTir.setEnabled(enabled)
        self.val_freq.setEnabled(enabled)
        self.serverIpEdit.setEnabled(enabled)
        self.serverPortEdit.setEnabled(enabled)
        self.but_reconnect.setEnabled(enabled)
        self.dummyCheckbox.setEnabled(enabled)
        self.unitBouton.setEnabled(enabled)

    def stepChange(self):
        nbStep = self.val_nbr_step.value()
        vInit = self.val_ini.value()
        vFin = self.val_fin.value()
        
        if nbStep <= 1:
            vStep = vFin - vInit
        else:
            vStep = (vFin - vInit) / (nbStep - 1)
        
        self.val_step.setValue(vStep)

    def changeFinal(self):
        nbStep = self.val_nbr_step.value()
        vInit = self.val_ini.value()
        vStep = self.val_step.value()
        vFin = vInit + (nbStep - 1) * vStep
        self.val_fin.setValue(vFin)

    def startScan(self):
        if not self.zmq_connected and not self.dummyMode:
            QMessageBox.warning(
                self, "Non connecté",
                "Connexion au serveur de tir non établie.\n"
                "Vérifiez l'IP et le port, puis cliquez sur Reconnecter.\n"
                "Ou activez le mode Dummy pour tester."
            )
            return
        
        self.stepChange()
        self.infoText.setStyleSheet("color: #4a9eff; font: 9pt;")
        self.threadScan.start()
        self.setControlsEnabled(False)
        self.but_start.setEnabled(False)
        self.but_stop.setEnabled(True)

    def unit(self):
        ii = self.unitBouton.currentIndex()
        
        units = {
            0: (1, 'step'),
            1: (float(self.stepmotor), 'µm'),
            2: (float(self.stepmotor / 1000), 'mm'),
            3: (float(self.stepmotor * 0.00666667), 'ps'),
            4: (float(self.stepmotor), '°'),
        }
        
        self.unitChange, self.unitName = units.get(ii, (1, 'step'))
        
        if self.unitChange == 0:
            self.unitChange = 1
        
        self.val_step.setSuffix(f" {self.unitName}")
        self.val_ini.setSuffix(f" {self.unitName}")
        self.val_fin.setSuffix(f" {self.unitName}")

    def closeEvent(self, event):
        self.isWinOpen = False
        
        if self.threadScan.isRunning():
            self.threadScan.stop = True
            self.threadScan.wait(2000)
        
        self.disconnect_zmq()
        event.accept()


class ThreadScan(QtCore.QThread):
    """
    Thread de scan synchronisé avec le serveur de tir ZMQ.
    """
    
    nbRemain = QtCore.pyqtSignal(int, int)
    info = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(ThreadScan, self).__init__(parent)
        self.parent = parent
        self.stop = False
        self.shots_received = 0
        self.shots_needed = 0

    def wait_position(self, target_pos, precision=5, timeout=60):
        unit = self.parent.unitChange
        unit_name = self.parent.unitName
        
        self.info.emit(f"→ {round(target_pos * unit, 2)} {unit_name}")
        self.parent.MOT.move(int(target_pos))
        
        start_time = time.time()
        
        while not self.stop:
            current_pos = self.parent.MOT.position()
            
            if abs(current_pos - target_pos) <= precision:
                self.info.emit(f"✓ Position: {round(current_pos * unit, 2)} {unit_name}")
                return True
            
            if time.time() - start_time > timeout:
                self.info.emit("⚠️ Timeout position!")
                return False
            
            time.sleep(0.1)
        
        return False

    def trigger_shots(self, nb_shots, freq_index):
        tir = self.parent.getTirModule()
        
        try:
            if nb_shots == 1:
                self.info.emit("🎯 Tir unique...")
                result = tir.Tir()
                print(f"Tir unique déclenché: {result}")
            else:
                freq_map = {0: '0.1', 1: '0.2', 2: '0.5', 3: '1.0'}
                self.info.emit(f"🎯 {nb_shots} tirs @ {freq_map[freq_index]} Hz...")
                result = tir.multi_shot(freq_index, nb_shots)
                print(f"Multi-shot: {nb_shots} @ freq={freq_index}, result={result}")
            
            return result is not None
            
        except Exception as e:
            self.info.emit(f"❌ Erreur tir: {e}")
            print(f"Erreur trigger_shots: {e}")
            import traceback
            traceback.print_exc()
            return False

    def wait_for_shots(self, nb_shots, freq_index, timeout=300):
        # Mode dummy sans ZMQ
        if self.parent.dummyMode and not self.parent.zmq_connected:
            freq_map = {0: 0.1, 1: 0.2, 2: 0.5, 3: 1.0}
            freq_hz = freq_map.get(freq_index, 0.1)
            
            for i in range(nb_shots):
                if self.stop:
                    return False
                time.sleep(1.0 / freq_hz)
                self.info.emit(f"[DUMMY] Tir {i+1}/{nb_shots}")
            
            return True
        
        if not self.parent.zmq_connected:
            self.info.emit("❌ Non connecté au serveur")
            return False
        
        self.shots_received = 0
        self.shots_needed = nb_shots
        
        freq_map = {0: 0.1, 1: 0.2, 2: 0.5, 3: 1.0}
        freq_hz = freq_map.get(freq_index, 0.1)
        expected_duration = nb_shots / freq_hz
        adaptive_timeout = max(timeout, expected_duration * 2 + 30)
        
        self.info.emit(f"⏳ Attente {nb_shots} tir(s)...")
        start_time = time.time()
        
        try:
            while self.shots_received < nb_shots and not self.stop:
                elapsed = time.time() - start_time
                if elapsed > adaptive_timeout:
                    self.info.emit("⚠️ Timeout tirs!")
                    return False
                
                try:
                    topic = self.parent.sub_socket.recv_string()
                    event = self.parent.sub_socket.recv_json()
                    
                    if topic == "SHOOT":
                        self.shots_received += 1
                        shoot_number = event.get('number', '?')
                        self.info.emit(f"💥 Tir {self.shots_received}/{nb_shots} (#{shoot_number})")
                        print(f"Tir reçu: {self.shots_received}/{nb_shots} (#{shoot_number})")
                        
                except Exception as e:
                    err_str = str(e).lower()
                    if "temporarily unavailable" not in err_str and "temporairement non disponible" not in err_str:
                        print(f"Erreur recv ZMQ: {e}")
            
            return self.shots_received >= nb_shots
            
        except Exception as e:
            self.info.emit(f"❌ Erreur ZMQ: {e}")
            print(f"Erreur ZMQ: {e}")
            return False

    def run(self):
        print('=== Démarrage séquence scan ===')
        self.stop = False
        
        self.info.emit(f'▶ Scan démarré à {time.strftime("%H:%M:%S")}')
        t_start = time.time()

        unit_change = self.parent.unitChange
        v_ini = self.parent.val_ini.value() / unit_change
        v_fin = self.parent.val_fin.value() / unit_change
        v_step = self.parent.val_step.value() / unit_change
        nb_tirs = int(self.parent.val_nbTir.value())
        freq_index = self.parent.val_freq.currentIndex()
        
        if v_step == 0:
            positions = [v_ini]
        else:
            positions = list(np.arange(v_ini, v_fin + v_step/2, v_step))
        
        nb_positions = len(positions)
        total_shots = nb_positions * nb_tirs
        
        self.nbRemain.emit(total_shots, total_shots)
        
        freq_labels = ['0.1 Hz', '0.2 Hz', '0.5 Hz', '1 Hz']
        print(f"Positions: {nb_positions}, Tirs/pos: {nb_tirs} @ {freq_labels[freq_index]}, Total: {total_shots}")
        
        shots_done = 0
        
        for i, pos in enumerate(positions):
            if self.stop:
                break
            
            print(f"\n--- Position {i+1}/{nb_positions}: {pos} ---")
            
            if not self.wait_position(pos, precision=5, timeout=60):
                if not self.stop:
                    self.info.emit("❌ Position non atteinte")
                break
            
            time.sleep(0.1)
            
            if not self.trigger_shots(nb_tirs, freq_index):
                if not self.stop:
                    self.info.emit("❌ Échec déclenchement")
                break
            
            if not self.wait_for_shots(nb_tirs, freq_index):
                if not self.stop:
                    self.info.emit("❌ Tirs non reçus")
                break
            
            shots_done += nb_tirs
            remaining = total_shots - shots_done
            self.nbRemain.emit(remaining, total_shots)
            
            print(f"Position {i+1}/{nb_positions} OK, reste {remaining}")
        
        duration = (time.time() - t_start) / 60
        if self.stop:
            self.info.emit(f'⏹ Interrompu ({duration:.1f} min)')
        else:
            self.info.emit(f'✅ Terminé en {duration:.1f} min')
            self.nbRemain.emit(0, total_shots)
        
        print(f'=== Fin scan ({duration:.1f} min) ===')