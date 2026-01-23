#!/home/sallejaune/loaenv/bin/env python
# -*- coding: utf-8 -*-
# last modified 08/01/2026
# Transformé pour ZMQ DEALER - Compatible avec serveur ROUTER-DEALER

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem
from PyQt6.QtWidgets import QLabel, QSizePolicy, QTreeWidgetItemIterator
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer
import qdarkstyle
import sys
import ast
import time
import os
import pathlib
from oneMotorGui import ONEMOTORGUI
from PyQt6 import QtCore
import tirSalleJaune as tirSJ
import __init__
# Import ZMQ
import zmq
import threading


class ZMQClient:
    """
    Client ZMQ DEALER pour communiquer avec le serveur ROUTER
    Remplace les sockets TCP
    Doit pourvoir etre remplace par la class zmq_client-RSAI ? 
    """
    
    def __init__(self, server_address="tcp://localhost:5555"):
        self.server_address = server_address
        self.context = zmq.Context()
        self.socket = None
        self.isconnected = False
        self.server_available = False
        self.mut = threading.Lock()
        
        # Configuration reconnexion
        self.reconnect_interval = 5
        self.heartbeat_interval = 15
        self.monitor_enabled = True
        
        # Démarrer la connexion
        self._connect()
        
        # Démarrer le thread de monitoring
        self.monitor_thread = threading.Thread(target=self._monitor_connection, daemon=True)
        self.monitor_thread.start()
    
    def _connect(self):
        """Établit la connexion ZMQ DEALER"""
        try:
            if self.socket:
                self.socket.close()
            
            self.socket = self.context.socket(zmq.DEALER)
            self.socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5s timeout
            self.socket.setsockopt(zmq.SNDTIMEO, 5000)
            self.socket.setsockopt(zmq.LINGER, 1000)
            self.socket.setsockopt(zmq.SNDHWM, 100)
            self.socket.setsockopt(zmq.RCVHWM, 100)
            
            # Identité unique
            identity = f"MAINMOTOR_{time.time()}".encode('utf-8')
            self.socket.setsockopt(zmq.IDENTITY, identity)
            
            self.socket.connect(self.server_address)
            self.isconnected = True
            self.server_available = True
            print(f"✅ Client ZMQ connecté à {self.server_address}")
            
        except Exception as e:
            self.isconnected = False
            self.server_available = False
            print(f"❌ Erreur de connexion ZMQ: {e}")
    
    def _monitor_connection(self):
        """Thread de monitoring avec heartbeat et reconnexion"""
        print("🔍 Thread de monitoring ZMQ démarré")
        
        while self.monitor_enabled:
            try:
                time.sleep(self.heartbeat_interval)
                
                if not self.isconnected or not self.server_available:
                    print("🔄 Tentative de reconnexion ZMQ...")
                    self._connect()
                    time.sleep(self.reconnect_interval)
                    continue
                
                # Envoyer heartbeat
                if self.isconnected:
                    try:
                        with self.mut:
                            self.socket.send_string('', zmq.SNDMORE | zmq.DONTWAIT)
                            self.socket.send_string('ping', zmq.DONTWAIT)
                            
                            if self.socket.poll(1000):
                                self.socket.recv()
                                response = self.socket.recv_string()
                                self.server_available = (response.strip() == 'pong')
                            else:
                                self.server_available = False
                                self.isconnected = False
                    except Exception as e:
                        print(f"❌ Erreur heartbeat: {e}")
                        self.server_available = False
                        self.isconnected = False
                        
            except Exception as e:
                print(f"❌ Erreur monitoring: {e}")
        
        print("🛑 Thread de monitoring arrêté")
    
    def sendMessage(self, message):
        """
        Envoie un message via ZMQ DEALER
        Compatible avec l'ancienne API TCP
        """
        if not self.server_available:
            print("⚠️ Serveur non disponible")
            return "error: server not available"
        
        with self.mut:
            try:
                # DEALER envoie: [frame vide, message]
                self.socket.send_string('', zmq.SNDMORE)
                self.socket.send_string(message)
                
                # Recevoir: [frame vide, réponse]
                self.socket.recv()
                response = self.socket.recv_string()
                
                self.isconnected = True
                self.server_available = True
                return response
                
            except zmq.Again:
                print("⏱️ Timeout communication")
                self.isconnected = False
                self.server_available = False
                return "error: timeout"
                
            except Exception as e:
                print(f"❌ Erreur communication: {e}")
                self.isconnected = False
                self.server_available = False
                return f"error: {e}"
    
    def close(self):
        """Ferme la connexion ZMQ"""
        self.monitor_enabled = False
        time.sleep(0.5)
        
        if self.socket:
            self.socket.close()
        self.context.term()
        self.isconnected = False
        print("🔒 Connexion ZMQ fermée")


class MAINMOTOR(QWidget):
    """
    Widget tree avec IP adress et moteurs
    Version ZMQ - Compatible avec serveur ROUTER-DEALER
    """
    
    def __init__(self, chamber=None, parent=None):
        super(MAINMOTOR, self).__init__(parent)
        self.isWinOpen = False
        self.parent = parent
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        
        # Lire la configuration du serveur
        p = pathlib.Path(__file__).parent
        sepa = os.sep
        fileconf = str(p) + sepa + "confServer.ini"
        confServer = QtCore.QSettings(fileconf, QtCore.QSettings.Format.IniFormat)
        
        # Configuration ZMQ
        server_host = str(confServer.value('MAIN/server_host', 'localhost'))
        server_port = str(confServer.value('MAIN/serverPort', '5555'))
        self.server_address = f"tcp://{server_host}:{server_port}"
        
        print(f"🔧 Connexion au serveur ZMQ: {self.server_address}")
        
        # Créer le client ZMQ
        self.zmqClient = ZMQClient(self.server_address)
        self.isconnected = self.zmqClient.isconnected
        
        self.chamber = chamber
        self.widdgetTir = tirSJ.SalleJauneConnect()
        
        # Timer pour vérifier la connexion
        self.connectionTimer = QTimer()
        self.connectionTimer.timeout.connect(self.checkConnection)
        self.connectionTimer.start(2000)  # Vérifier toutes les 2s
        
        # Attendre la connexion
        if self.waitForConnection(timeout=10):
            self.aff()
        else:
            print("⚠️ Impossible de se connecter au serveur")
            QLabel("⚠️ Serveur non disponible", self)

    def waitForConnection(self, timeout=10):
        """Attend que la connexion soit établie"""
        start_time = time.time()
        print("⏳ Attente de connexion au serveur ZMQ...")

        while time.time() - start_time < timeout:
            if self.zmqClient.isconnected and self.zmqClient.server_available:
                print("✅ Connexion établie !")
                return True
            time.sleep(0.5)
            QApplication.processEvents()  # Garder l'UI responsive

        print(f"⏱️ Timeout: connexion impossible après {timeout}s")
        return False

    def checkConnection(self):
        """Vérifie périodiquement l'état de la connexion"""
        self.isconnected = self.zmqClient.isconnected and self.zmqClient.server_available

        # Mettre à jour l'UI si nécessaire
        if not self.isconnected:
            self.setWindowTitle('Client RSAI (Déconnecté)')
        else:
            if self.chamber:
                self.setWindowTitle(f'Client RSAI {self.chamber}')
            else:
                self.setWindowTitle('Client RSAI')
    
    def sendCommand(self, command):
        """
        Envoie une commande au serveur ZMQ
        Wrapper pour compatibilité avec l'ancien code
        """
        try:
            response = self.zmqClient.sendMessage(command)
            return response
        except Exception as e:
            print(f"❌ Erreur commande: {e}")
            return f"error: {e}"

    def aff(self):
        # Récupérer la liste des racks
        cmdsend = "listRack"
        response = self.sendCommand(cmdsend)
        try:
            self.listRack = ast.literal_eval(response)
        except Exception as e:
            print(f"❌ Erreur parsing listRack: {response, e}")
            self.listRack = []
            return
        #  print(f'list rack{self.listRack}')
        self.motItem = []
        self.rackName = []
        self.motorCreatedId = []
        self.motorCreated = []
        
        # Récupérer les noms des racks
        for IP in self.listRack:
            cmd = 'nomRack'
            cmdsend = f"{IP}, 1, {cmd}"
            response = self.sendCommand(cmdsend)
            nameRack = response.split()[0] if response else "Unknown"
            self.rackName.append(nameRack)

        #print(f'liste rack name {self.rackName}')
        self.rack = dict(zip(self.rackName, self.listRack))
        self.listMotorName = []
        self.listMotButton = list()
        irack = 0
        self.dic_moteurs = {}
        self.nbMotRack = ast.literal_eval(self.sendCommand('nbMotRack'))
        print(f'nb de moteurs par rack: {self.nbMotRack}')

        # Récupérer les noms des moteurs
        for IP in self.listRack:
            dict_name = "self.dictMotor" + "_" + str(IP)
            num = list(range(1, self.nbMotRack[irack]+1))
            listMot = []

            for i in range(0, self.nbMotRack[irack]):
                cmd = 'name'
                cmdsend = f"{IP}, {i+1}, {cmd}"
                response = self.sendCommand(cmdsend)
                name = response.split()[0] if response else f"Motor_{i+1}"
                self.listMotorName.append(name)
                listMot.append(name)
            irack += 1
            self.dic_moteurs[dict_name] = dict(zip(listMot, num))
            self.dic_moteurs[dict_name]['ip'] = str(IP)

        # Filtrer par chambre si nécessaire
        self.rackNameFilter = []
        self.listMotorNameFilter = []

        if self.chamber is not None:
            for name in self.rackName:
                if self.chamber in name.lower():
                    self.rackNameFilter.append(name)

            self.rackIPFilter = []
            for key in self.rack.keys():
                if self.chamber in key.lower():
                    self.rackIPFilter.append(self.rack[key])

            for IP in self.rackIPFilter:
                for i in range(0, 14): #self.nbMotRack[irack]
                    cmd = 'name'
                    cmdsend = f"{IP}, {i+1}, {cmd}"
                    response = self.sendCommand(cmdsend)
                    name = response.split()[0] if response else f"Motor_{i+1}"
                    self.listMotorNameFilter.append(name)

        self.SETUP()
        #self.EXPAND()

    def SETUP(self):
        vbox1 = QVBoxLayout()

        vbox1.addWidget(self.widdgetTir)

        # Label avec statut de connexion
        self.connectionLabel = QLabel()
        self.updateConnectionLabel()
        vbox1.addWidget(self.connectionLabel)

        chamberName = QLabel()
        chamberName.setText('Motors Control : %s' % self.chamber)
        chamberName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox1.addWidget(chamberName)
        for w in (
            self.widdgetTir,
            self.connectionLabel,
            chamberName,
        ):
            w.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed
                )

        self.tree = QTreeWidget()
        self.tree.header().hide()
        # Configuration pour permettre l'expansion automatique
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        z = 0

        if self.chamber is not None:
            self.setWindowTitle('Client RSAI ' + self.chamber)
            for i in range(0, len(self.rackNameFilter)):
                rackTree = QTreeWidgetItem(self.tree, [self.rackNameFilter[i]])
                for j in range(0, 14): # faire quelque chose pour savoir le nombre d'axe du rack 
                    self.motItem.append(QTreeWidgetItem(rackTree, [self.listMotorNameFilter[z], '']))
                    z += 1
        else:
            self.setWindowTitle('Client RSAI')
            for i in range(0, len(self.listRack)):
                rackTree = QTreeWidgetItem(self.tree, [self.rackName[i]])
                #z=0
                print(self.listMotorName)
                for j in range(0, self.nbMotRack[i]):
                    self.motItem.append(QTreeWidgetItem(rackTree, [self.listMotorName[z], '']))
                    z += 1

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.tree)
        vbox2.setContentsMargins(0, 0, 0, 0)
        vbox2.setSpacing(0)
        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        vbox.addLayout(vbox1)
        vbox.addLayout(vbox2)
        self.setLayout(vbox)

        self.tree.itemClicked.connect(self.actionPush)
        self.tree.itemExpanded.connect(self.EXPAND)
        self.tree.itemCollapsed.connect(self.EXPAND)

        # Ajuster la taille initiale
        self.adjustSize()
    
        # Définir une taille minimale et maximale raisonnable
        self.setMinimumWidth(400)
    
        # Appeler EXPAND pour ajuster correctement
        #self.EXPAND()

        # Timer pour mettre à jour le label de connexion
        self.labelTimer = QTimer()
        self.labelTimer.timeout.connect(self.updateConnectionLabel)
        self.labelTimer.start(1000)

    def updateConnectionLabel(self):
        """Met à jour le label de statut de connexion"""
        if self.zmqClient.server_available:
            self.connectionLabel.setText(f"✅ Connecté au serveur ZMQ : {self.server_address}")
            self.connectionLabel.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connectionLabel.setText("⚠️ Serveur non disponible - Reconnexion en cours...")
            self.connectionLabel.setStyleSheet("color: orange; font-weight: bold;")

    def actionPush(self, item: QTreeWidgetItem, colum: int):
        if item.parent():
            rackname = item.parent().text(0)
            motorname = item.text(0)
            ip = self.rack[rackname]
            numMot = self.dic_moteurs["self.dictMotor" + "_" + str(ip)][item.text(0)]
            motorID = str(ip) + 'M' + str(numMot)

            if motorID in self.motorCreatedId:
                index = self.motorCreatedId.index(motorID)
                self.open_widget(self.motorCreated[index])
            else:
                # Créer un widget moteur avec ZMQ
                self.motorWidget = ONEMOTORGUI(ip, numMot)
                time.sleep(0.1)
                self.open_widget(self.motorWidget)
                self.motorCreatedId.append(motorID)
                self.motorCreated.append(self.motorWidget)

    def EXPAND(self):
        """
        Ajuste automatiquement la hauteur du widget en fonction du nombre d'items visibles
        avec une limite maximale raisonnable marche moyen ...
        BOF!!
        """
        # Attendre que le tree soit complètement mis à jour
        QApplication.processEvents()
        
        # Compter les items visibles
        count = 0
        iterator = QTreeWidgetItemIterator(self.tree)
        
        while iterator.value():
            item = iterator.value()
            if item.parent():
                # Item enfant : compter seulement si le parent est expandé
                if item.parent().isExpanded():
                    count += 1
            else:
                # Item racine : toujours compter
                count += 1
            iterator += 1
        
        # Calculer la hauteur réelle en mesurant les items
        totalH = 0
        iterator2 = QTreeWidgetItemIterator(self.tree)
        while iterator2.value():
            item = iterator2.value()
            if not item.parent() or (item.parent() and item.parent().isExpanded()):
                rect = self.tree.visualItemRect(item)
                if rect.height() > 0:
                    totalH += rect.height()
            iterator2 += 1
        
        # Si la mesure échoue, utiliser une hauteur fixe par item
        if totalH < count * 20:  # Sécurité
            rowH = 30  # Hauteur réaliste par ligne
            totalH = count * rowH
        
        # Ajouter une petite marge
        totalH += 10
        # Définir des limites raisonnables
        MAX_TREE_HEIGHT = 600  # Hauteur maximale du tree
        EXTRA_SPACE = 15  # Espace pour les autres widgets
        # Calculer la hauteur idéale du tree (basée sur le contenu réel)
        idealTreeHeight = min(totalH, MAX_TREE_HEIGHT)
        # Hauteur totale de la fenêtre
        newHeight = idealTreeHeight + EXTRA_SPACE
        # Ajuster la hauteur du tree pour correspondre exactement au contenu
        self.tree.setFixedHeight(idealTreeHeight)
        # Si on atteint la hauteur max, activer le scroll
        if totalH > MAX_TREE_HEIGHT:
            self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        else:
            self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
         # Redimensionner la fenêtre
        currentWidth = self.width()
        self.resize(max(currentWidth, 400), newHeight)
        # self.updateGeometry()
        # Debug pour voir ce qui se passe
        #print(f"📊 Items visibles: {count}, Hauteur calculée: {totalH}px, Hauteur tree: {idealTreeHeight}px, Total fenêtre: {newHeight}px")

    def actionButton(self):
        self.upRSAI.clicked.connect(self.updateFromRsai)
  
    def updateFromRsai(self):
        print('🔄 Mise à jour depuis RSAI...')
        cmdsend = "updateFromRSAI"
        response = self.sendCommand(cmdsend)

        if "error" in response:
            print(f"❌ Erreur update: {response}")
            return

        self.listMotorName = []
        self.listMotButton = list()
        irack = 0
        for IP in self.listRack:
            for i in range(0, 14):
                cmd = 'name'
                cmdsend = f"{IP}, {i+1}, {cmd}"
                response = self.sendCommand(cmdsend)
                name = response.split()[0] if response else f"Motor_{i+1}"
                self.listMotorName.append(name)
                self.listMotButton.append(QPushButton(name, self))
            irack += 1
  
        print("✅ Mise à jour terminée")

    def open_widget(self, fene):
        """Ouvre un nouveau widget"""
        if fene.isWinOpen is False:
            fene.show()
            fene.startThread2()
            fene.isWinOpen = True
        else:
            fene.raise_()
            fene.showNormal()

    def closeEvent(self, event):
        """Fermeture de la fenêtre"""
        print("🔒 Fermeture de MAINMOTOR...")
        self.isWinOpen = False

        # Arrêter les timers
        self.connectionTimer.stop()
        if hasattr(self, 'labelTimer'):
            self.labelTimer.stop()

        # Fermer tous les widgets moteurs
        for mot in self.motorCreated:
            mot.close()
        time.sleep(0.1)
        
        # Fermer la connexion ZMQ
        self.zmqClient.close()
        time.sleep(0.1)
        
        event.accept()
        print("✅ MAINMOTOR fermé")
    
    
if __name__ == '__main__':
    appli = QApplication(sys.argv)
    
    # Créer la fenêtre principale
    s = MAINMOTOR(chamber='rosa')
    s.show()
    
    sys.exit(appli.exec())