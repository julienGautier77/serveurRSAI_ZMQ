"""
Serveur RSAI avec ZMQ ROUTER-DEALER
Version avec les workers
We use moteurRSAIFDB to dialog with the firebird data base for synchronisation with RSAI client/server software
After we only use pilmotTango.dll to dialog to the rack
dummy class pour la firebird db et pour la dll PilMotTango
"""

import zmq
import time
import threading
import ctypes
import pathlib
import os
import traceback
from datetime import datetime
from collections import deque
# import uuid
from PyQt6 import QtCore
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton, QTextEdit, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon
import qdarkstyle
import socket as _socket

Mut = threading.Lock()


class WorkerSignals(QObject):
    """
    Classe pour émettre des signaux PyQt depuis les workers threading.Thread
    Les workers threading.Thread ne peuvent pas hériter de QObject,
    donc on utilise une classe dédiée pour les signaux
    """
    signalClientWorker = pyqtSignal(object)
    signalUpdate = pyqtSignal(object)
    signalHeartbeat = pyqtSignal(str)
    signalLog = pyqtSignal(str)


class SERVERRSAI(QWidget):
    signalServer = pyqtSignal(object)
    
    def __init__(self, parent=None, test=False):
        super(SERVERRSAI, self).__init__(parent)

        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.hostname = _socket.gethostname()
        self.iphost = _socket.gethostbyname(self.hostname)
        self.test = test

        # log 
        self.actionLog = deque(maxlen=30)
        self.logWindow = None
        # Log initial
        self.addLog('SYSTEM', 'Démarrage du serveur RSAI ZMQ')
        self.refreshLog()

        try:
            
            import moteurRSAIFDB
            
            self.moteurRSAIFDB = moteurRSAIFDB # use to connect to the database and to create the inifile 
            self.db = self.moteurRSAIFDB.FirebirdConnect() # Connect to firebird database 
            db_connected = self.db.ConnectToDB()
            RSAIServer = self.db.IsServerRSAIConnected() 
            if RSAIServer is False:
                self.addLog('ERROR', 'RSAI  serveur software is not launched ... ')
            else : 
                self.addLog('SYSTEM', 'RSAI  serveur software is launched')
            self.setWindowTitle('RSAI SERVER ZMQ (connected to firedbird DB)')
            if not db_connected:
                # La connexion a échoué, basculer vers dummy
                self.addLog('ERROR', 'Échec de connexion databse firebird RSAI')
                raise ConnectionError("Failed to connect to database")
            else:
                self.addLog('SYSTEM', 'connexion to databse firebird RSAI')
                
        except Exception as e:
            self.addLog('ERROR', '🔄 Switching to dummy database firebird RSAI')
            import moteurRSAIFDB_dummy as moteurRSAIFDB
            self.moteurRSAIFDB = moteurRSAIFDB
            self.db = self.moteurRSAIFDB.FirebirdConnect()
            self.setWindowTitle('RSAI SERVER ZMQ (DUMMY)')

        self.initFromRSAIDB()
        self.setup()
        self.connexionRack()

        # Créer le serveur ZMQ
        self.server = SERVERZMQ(
            PilMot=self.PilMot,
            conf=self.conf,
            listRackIP=self.listRackIP,
            dict_moteurs=self.dict_moteurs,
            parent=self
        )
        self.server.start()
    
    def initFromRSAIDB(self):
        self.listRackIP = self.db.rEquipmentList()
        self.rackName = []
        self.nbMotorRack = [] # npb de moteur dans les racks 
        for IP in self.listRackIP:
            self.rackName.append(self.db.nameEquipment(IP))

        self.dictRack = dict(zip(self.rackName, self.listRackIP))
        self.dict_moteurs = {}

        self.conf = QtCore.QSettings('confMoteurRSAIServer.ini', QtCore.QSettings.Format.IniFormat)
        i = 0
        for ip in self.listRackIP:
            self.listMotorServ = []
            self.listMotor = self.db.listMotorName(ip)
            self.nbMotorRack.append(len(self.listMotor))
            num = list(range(1, len(self.listMotor) + 1))
            dict_name = "self.dictMotor" + "_" + str(ip)
            self.listMotor = [element.replace('Â', ' ') for element in self.listMotor]
            self.listMotor = [element.replace('°', ' ') for element in self.listMotor]
            self.listMotor = [element.replace(' ', '_') for element in self.listMotor]
            
            ii = 0
            for mot in self.listMotor:
                motConf = self.db.nameEquipment(ip) + 'M' + str(ii + 1)
                self.listMotorServ.append(motConf)
                
                if mot == ' ' or mot == '':
                    mot = 'M' + str(ii + 1)
                    self.listMotor[ii] = mot
                ii += 1
            
            self.dict_moteurs[dict_name] = dict(zip(num, self.listMotorServ))
            self.dict_moteurs[dict_name]['ip'] = str(ip)
            
            #  On cree in fichier ini poour eviter d interroger la base de données a chaque fois
            # il peut y aoir des problemes si le rack a le meme nom : rajouter l'ip au nom du rack ? 
            j = 0
            for mot in self.listMotorServ:
                moteur = self.moteurRSAIFDB.MOTORRSAI(IpAdrress=ip, NoMotor=j + 1, db=self.db)
                name = mot
                nameGiven = self.listMotor[j]
                nomRack = moteur.getEquipementName()
                step = moteur.step
                butmoins = moteur.butMoins if moteur.butMoins != '' else 0
                butplus = moteur.butPlus if moteur.butPlus != '' else 0
                refName = moteur.refName
                refValue = moteur.refValue
                
                self.conf.setValue(name + "/nom", nameGiven)
                self.conf.setValue(name + "/nomRack", nomRack)
                self.conf.setValue(name + "/IPRack", ip)
                self.conf.setValue(name + "/numESim", i)
                self.conf.setValue(name + "/numMoteur", j + 1)
                self.conf.setValue(name + "/stepmotor", 1 / float(step))
                self.conf.setValue(name + "/buteePos", butplus)
                self.conf.setValue(name + "/buteeNeg", butmoins)
                self.conf.setValue(name + "/moteurType", "RSAI")
                
                for v in range(0, 6):
                    if refName[v] == ' ' or refName[v] == '':
                        refName[v] = 'REF' + str(v)
                    if refValue[v] == '' or refValue[v] == ' ':
                        refValue[v] = 0
                    self.conf.setValue(name + "/ref" + str(v) + "Name", refName[v])
                    self.conf.setValue(name + "/ref" + str(v) + "Pos", refValue[v])
                j += 1
                
            i += 1

    def updateFromRSAI(self):
        self.addLog('SYSTEM', 'updated from RSAI DataBase')
        self.initFromRSAIDB()
        return 'OK'
    
    def setup(self):

        self.setWindowIcon(QIcon('./icons/LOA.png'))
        
        vbox1 = QVBoxLayout()
        hbox1 = QHBoxLayout()
        label = QLabel('Server RSAI (ZMQ)')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: green; font-weight: bold;")
        
        vbox1.addWidget(label)
        
        labelIP = QLabel()
        labelIP.setText('IP: ' + self.iphost)
        labelPort = QLabel('Port: 5555 (ZMQ ROUTER)')
        hbox1.addWidget(labelIP)
        hbox1.addWidget(labelPort)
        vbox1.addLayout(hbox1)
        hbox0 = QVBoxLayout()
        vbox1.addLayout(hbox0)
        ll = QLabel('Rack(s) connected : ')
        ll.setStyleSheet("color: green; font-weight: bold;")
        hbox0.addWidget(ll)
        self.box = []

        i = 0
        for name in self.rackName:
            self.box.append(checkBox(name=str(name), ip=self.listRackIP[i], parent=self))
            hbox0.addWidget(self.box[i])
            i += 1

        hbox2 = QHBoxLayout()
        labelClient = QLabel('Clients connectés:  ')
        labelClient.setStyleSheet("color: green; font-weight: bold;")
        self.clientCountLabel = QLabel('0')
        self.clientCountLabel.setStyleSheet("font-weight: bold; font-size: 14pt;")
        hbox2.addWidget(labelClient)
        hbox2.addWidget(self.clientCountLabel)
        hbox2.addStretch()
        vbox1.addLayout(hbox2)
        
        # Bouton pour afficher l'historique des actions
        hbox3 = QHBoxLayout()
        self.logButton = QPushButton('📋 Afficher l\'historique des actions')
        self.logButton.clicked.connect(self.showLog)
        self.logButton.setMinimumHeight(40)
        hbox3.addWidget(self.logButton)
        vbox1.addLayout(hbox3)
        
        self.setLayout(vbox1)

    def connexionRack(self):

        p = pathlib.Path(__file__)
        sepa = os.sep
        iplist = ''
        for ip in self.listRackIP:
            iplist = iplist + ip + '\0' + '      '
        sizeBuffer = len(self.listRackIP) * 16
        
        IPs_C = ctypes.create_string_buffer(iplist.encode(), sizeBuffer)
        
        dll_file = str(p.parent) + sepa + 'PilMotTango.dll'
        try:
            self.PilMot = ctypes.windll.LoadLibrary(dll_file)
            self.addLog('SYSTEM', ' Using PilMotTango.dll')
            if self.test:
                raise Exception("test mode")
        except Exception as e:
            self.addLog('ERROR', ' Error import PilMotTango.dll')
            import dummyPilMotTango_dll
            self.PilMot = dummyPilMotTango_dll.DummyPilMotTango()
            self.addLog('SYSTEM', ' 🔄 Using dummy PilMotTango')

        nbeqp = len(self.listRackIP)
        argout = self.PilMot.Start(ctypes.c_int(nbeqp), IPs_C)
        time.sleep(2)
        if argout == 1:
            self.addLog('SYSTEM', f'Connexion RSAI OK - {len(self.listRackIP)} rack(s)')
        else:
            self.addLog('ERROR', 'Échec de connexion RSAI')
        
        self.threadRack = THREADRACKCONNECT(PilMot=self.PilMot, parent=self)
        self.threadRack.start()

    def addLog(self, action, details=""):
        """Ajoute une action au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'details': details
        }
        self.actionLog.append(log_entry)
        print(f"[LOG] {timestamp} - {action}  -  {details}")
    
    def showLog(self):
        """Affiche la fenêtre de log"""
        if self.logWindow is None or not self.logWindow.isVisible():
            self.logWindow = LogWindow(parent=self)
            self.logWindow.setLogs(list(self.actionLog))
            self.logWindow.show()
        else:
            self.logWindow.raise_()
            self.logWindow.activateWindow()
            self.refreshLog()
    
    def refreshLog(self):
        """Rafraîchit l'affichage du log"""
        if self.logWindow and self.logWindow.isVisible():
            self.logWindow.setLogs(list(self.actionLog))
    
    def clearLogs(self):
        """Efface tous les logs"""
        self.actionLog.clear()
        self.addLog("Historique effacé", "")

    def closeEvent(self, event):
        self.threadRack.stopThread()
        time.sleep(1)
        self.server.stopThread()
        time.sleep(1.2)
        
        try:
            self.db.closeConnection()
        except Exception as e:
            print(f'error closing DB connection: {e}')
            pass
        time.sleep(1)
        try: 
            self.PilMot.Stop()
            print('Rack RSAI connection stopped')
        except Exception as e:
            print(e)
        event.accept()


class SERVERZMQ(QtCore.QThread):
    """
    Serveur ZMQ ROUTER - Reste en QThread car besoin de signaux PyQt
    Les workers sont des threading.Thread pour plus de simplicité
    """

    def __init__(self, PilMot, conf, listRackIP, dict_moteurs, parent=None):
        super(SERVERZMQ, self).__init__(parent)
        self.parent = parent
        self.PilMot = PilMot
        self.conf = conf
        self.listRackIP = listRackIP
        self.dict_moteurs = dict_moteurs

        # Configuration ZMQ
        self.context = zmq.Context()
        self.frontend_port = 5555
        self.backend_port = 5556
        self.num_workers = 20

        # ROUTER pour recevoir les clients
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.setsockopt(zmq.LINGER,0) # le socket s'arrte de suite
        self.frontend.setsockopt(zmq.SNDHWM, 1000)
        self.frontend.setsockopt(zmq.RCVHWM, 1000)
        self.frontend.bind(f"tcp://*:{self.frontend_port}")

        # DEALER pour distribuer aux workers
        self.backend = self.context.socket(zmq.DEALER)
        self.backend.setsockopt(zmq.SNDHWM, 1000)
        self.backend.setsockopt(zmq.RCVHWM, 1000)
        self.backend.setsockopt(zmq.LINGER,0)
        self.backend.bind(f"tcp://*:{self.backend_port}")

        self.isConnected = True
        self.clientList = {}
        self.workers = []

        # Gestion des clients morts via heartbeat
        self.client_heartbeats = {}
        self.heartbeat_timeout = 30
        self.heartbeat_check_interval = 30

        # Signaux pour communication avec UI
        self.signals = WorkerSignals()
        self.signals.signalClientWorker.connect(self.signalFromClient)
        self.signals.signalUpdate.connect(self.updateFromRSAI)
        self.signals.signalHeartbeat.connect(self.updateHeartbeat)
        self.signals.signalLog.connect(self.handleLog)

        self.parent.addLog('SYSTEM',f'Serveur ZMQ ROUTER prêt sur le port {self.frontend_port}')
        
        self.parent.addLog('SYSTEM',f'Heartbeat activé: timeout {self.heartbeat_timeout}s')

    def run(self):
        # Démarrer les workers avec threading.Thread
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self.worker_function,
                args=(i,),
                daemon=True,
                name=f"Worker-{i}"
            )
            worker.start()
            self.workers.append(worker)

        self.parent.addLog('SYSTEM',f'{self.num_workers} workers  démarrés')
        # Démarrer le thread de surveillance des heartbeats
        self.heartbeat_thread = threading.Thread(
            target=self.check_dead_clients,
            daemon=True,
            name="Heartbeat-Monitor"
        )
        self.heartbeat_thread.start()
        self.parent.addLog('SYSTEM',f'Thread de surveillance heartbeat démarré')
        
        try:
            # Démarrer le proxy ROUTER-DEALER
            zmq.proxy(self.frontend, self.backend)
            self.parent.addLog('SYSTEM',f'Proxy Router-DEALER started')
        except Exception as e:
            self.parent.addLog('SYSTEM',f'Proxy Router-DEALER started  {e} ')
        finally:
            self.stopThread()


    def worker_function(self, worker_id):
        """
        Worker ZMQ DEALER
        - Ne gère PAS les clients
        - Ne gère PAS les enveloppes
        - Traite uniquement les messages
        """

        context = zmq.Context.instance()
        socket = context.socket(zmq.DEALER)

        socket.setsockopt(zmq.IDENTITY, f"Worker-{worker_id}".encode())
        socket.connect(f"tcp://localhost:{self.backend_port}")
        socket.setsockopt(zmq.LINGER, 0)
        active_clients = set()

        while self.isConnected:
            try:
                # ✅ Recevoir TOUTES les frames (identité + vide + message)
                frames = socket.recv_multipart()
                
                if len(frames) < 3:
                    # print(f"⚠️ Worker-{worker_id}: frames incomplètes: {len(frames)}")
                    self.parent.addLog('ERROR',f"⚠️ Worker-{worker_id}: frames incomplètes: {len(frames)}")
                    continue
                
                client_id = frames[0].decode('utf-8')
                empty = frames[1]  # Frame vide
                message = frames[2].decode('utf-8')
                
                #print(f"📥 Worker-{worker_id} reçu de {client_id}: {message}")
                
                # Traiter le message
                response, log_message = self.process_message(message, client_id)
                
                # Log si nécessaire
                if log_message:
                    self.signals.signalLog.emit(f"WORKER-{worker_id}||{log_message}")
                
                # Tracer le client
                if client_id not in active_clients:
                    active_clients.add(client_id)
                    self.signals.signalClientWorker.emit([client_id, f"Worker-{worker_id}"])
                    
                # Mettre à jour le heartbeat
                self.signals.signalHeartbeat.emit(client_id)
                # ✅ Renvoyer TOUTES les frames (identité + vide + réponse)
                socket.send_multipart([
                    client_id.encode('utf-8'),
                    b'',
                    response.encode('utf-8')
                ])
                
                # print(f"📤 Worker-{worker_id} envoyé à {client_id}: {response[:50]}")

            except zmq.ContextTerminated:
                break

            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    break
                print(f"❌ ZMQ error Worker-{worker_id}: {e}")

            except Exception as e:
                print(f"❌ Exception Worker-{worker_id}: {e}")
                traceback.print_exc()
                try:
                    socket.send_string("error\n")
                except Exception:
                    pass

        socket.close()
        print(f"🔴 Worker {worker_id} arrêté")

    def process_message(self, msgReceived, client_id):
        """Traite un message reçu et retourne la réponse"""
        try:
            msgsplit = msgReceived.split(',')
            msgsplit = [msg.strip() for msg in msgsplit]
            if len(msgsplit) > 1:
                ip = msgsplit[0]
                axe = int(msgsplit[1])
                cmd = msgsplit[2]
                numEsim = int(self.listRackIP.index(ip))
                dict_name = "self.dictMotor" + "_" + str(ip)
                name = self.dict_moteurs[dict_name][axe]
                #  print("message decode ip axe,cmd,num esim,name:", ip, axe, cmd, numEsim, name)
            else:
                cmd = msgsplit[0]
            
            # print(cmd, "cmd")
            if len(msgsplit) > 3:
                valueStr = msgsplit[3]
                para3 = str(valueStr)
                try:
                    value = ctypes.c_int(int(valueStr))
                except Exception as e:
                    print(f'Error converting value to int: {e}')
                    value = ctypes.c_int(1)
            else:
                value = ctypes.c_int(0)

            if len(msgsplit) > 4:
                para4 = msgsplit[4]
                para4 = str(para4)

            vit = ctypes.c_int(int(10000))

            #  Traitement des commandes
            if cmd == 'clientid':
                return client_id + '\n', None

            elif cmd == 'ping' or cmd == 'heartbeat':
                return 'pong\n', None

            elif cmd == 'dict':
                return str(self.dict_moteurs) + '\n', None

            elif cmd == 'updateFromRSAI':
                self.signals.signalUpdate.emit('ok')
                log_message = ('System', f"UPDATE - Mise à jour base de données demandée par : {client_id}")
                return 'ok\n', log_message

            elif cmd == 'listRack': #  liste IP de racks
                return str(self.listRackIP) + '\n', None

            elif cmd == 'move':
                regCde = ctypes.c_uint(2)
                err = self.PilMot.wCdeMot(numEsim, axe, regCde, value, vit)
                log_message = ("move", f"{client_id} {name}  → position  {valueStr}")
                return 'ok\n', log_message

            elif cmd == 'rmove':
                regCde = ctypes.c_uint(4)
                err = self.PilMot.wCdeMot(numEsim, axe, regCde, value, vit)
                log_message = ("rmove", f"RMOVE - {name} déplacement relatif {valueStr}")
                return 'ok\n', log_message

            elif cmd == 'stop':
                regCde = ctypes.c_uint(8)
                err = self.PilMot.wCdeMot(numEsim, axe, regCde, 0, 0)
                log_message = ("Stop",f"{'STOP - '}{name} arrêté ")
                return 'ok\n', log_message

            elif cmd == 'position':
                pos = self.PilMot.rPositionMot(numEsim, axe)
                return str(pos) + '\n', None

            elif cmd == 'etat':
                a = self.PilMot.rEtatMoteur(numEsim, axe)
                etatConnection = self.PilMot.rEtatConnexion(ctypes.c_int16(numEsim))

                if etatConnection == 3:
                    if (a & 0x0800) != 0:
                        etat = 'Poweroff'
                    elif (a & 0x0200) != 0:
                        etat = 'Phasedebranche'
                    elif (a & 0x0400) != 0:
                        etat = 'courtcircuit'
                    elif (a & 0x0001) != 0:
                        etat = 'FDC+'
                    elif (a & 0x0002) != 0:
                        etat = 'FDC-'
                    elif (a & 0x0004) != 0:
                        etat = 'Log+'
                    elif (a & 0x0008) != 0:
                        etat = 'Log-'
                    elif (a & 0x0020) != 0:
                        etat = 'mvt'
                    elif (a & 0x0080) != 0:
                        etat = 'ok'
                    elif (a & 0x8000) != 0:
                        etat = 'etatCameOrigin'
                    else:
                        etat = '?'
                else:
                    etat = 'errorConnect'

                return etat + '\n', None

            elif cmd == 'setzero':
                regCde = ctypes.c_int(1024)
                err = self.PilMot.wCdeMot(numEsim, axe, regCde, ctypes.c_int(0), ctypes.c_int(0))
                log_message =("Set Zero", f"SETZERO - {name} position mise à zéro")
                return 'ok\n', log_message

            elif cmd == 'name':
                nameGiven = str(self.conf.value(name + '/nom'))
                return nameGiven, None

            elif cmd == 'setName':
                try:
                    ## to do 
                    log_message = f"SETNAME - {name} renommé en {para3}"
                    return 'ok\n', log_message
                except Exception as e:
                    # print(f'Error setName: {e}')
                    log_message =('System', f"SETNAME - {name}  Error renommé en {para3}")
                    return 'errorFB\n', log_message

            elif 'ref' in cmd:
                ref = str(self.conf.value(name + '/' + str(cmd)))
                return ref + '\n', None

            elif cmd == 'setRefPos':
                nRef = int(para4)
                valPos = int(para3)
                try:
                    self.parent.db.setPosRef(ip, axe, nRef, valPos)
                    self.conf.setValue(name + "/ref" + str(nRef - 1) + "Pos", valPos)
                    log_message = ('Reference', f"SETREF - {name} REF{nRef} position → {valPos}")
                    return 'ok\n', None
                except Exception as e:
                    #print(f'Error setRefPos: {e}')
                    log_message = ('ERROR', f"SETREFPos - {e}")
                    return 'errorFB\n', log_message

            elif cmd == 'setRefName':
                nRef = int(para4)
                try:
                    # print('set ref name')
                    self.parent.db.setNameRef(ip, axe, nRef, para3)
                    self.conf.setValue(name + "/ref" + str(nRef - 1) + "Name", para3)
                    log_message = ('Reference', f"SETREF - {name} REF{nRef} renommée → {para3}")
                    return 'ok\n', None
                except Exception as e:
                    print(f'Error setRefName: {e}')
                    log_message = ('ERROR', f"SETREF - {e}")
                    return 'error FB\n', log_message

            elif cmd == 'step':
                st = str(self.conf.value(name + '/stepmotor'))
                return st + '\n', None

            elif cmd == 'buteePos' or cmd == 'buteeNeg':
                but = str(self.conf.value(name + '/' + cmd))
                return but + '\n', None
            elif cmd == 'setButeePos' :
                try:
                    butPos = int(para3)
                    self.parent.db.setButeePos(ip, axe, butPos)
                    self.conf.setValue(name + '/buteePos', butPos)
                    log_message = ('Butee', f"SETBUTEEPOS - {name} butée positive → {butPos}")
                    return 'ok\n', None
                except Exception as e:
                    # print(f'Error setButeePos: {e}')
                    log_message = ('ERROR', f"SETBUTEEPOS - {e}")
                    return 'errorFB\n', log_message
            elif cmd == 'setButeeNeg':
                try:
                    butNeg = int(para3)
                    self.parent.db.setButLogPlusValue(butNeg)
                    self.conf.setValue(name + '/buteeNeg', butNeg)
                    log_message = ('Butee', f"SETBUTEENEG - {name} butée négative → {butNeg}")
                    return 'ok\n', None
                except Exception as e:
                    # print(f'Error setButeeNeg: {e}')
                    log_message = ('ERROR', f"SETBUTEENEG - {e}")
                    return 'errorFB\n', log_message
            elif cmd == 'nomRack':
                nameRack = str(self.conf.value(name + '/' + cmd))
                return nameRack + '\n', None
            elif cmd == 'nbMotRack': # retourne la liste de tous le nombre de moteur par rack
                nbMotRack = self.parent.nbMotorRack
                return str(nbMotRack) + '\n', None
            elif cmd == 'nbMotRackIP': # retourne l nombre de moteur pour le rack IP 
                nbMotRack = self.parent.nbMotorRack
                return str(nbMotRack) + '\n', None
            else:
                log_message = ('System', f"UNKNOWN COMMAND - Commande inconnue: {cmd}")
                return 'error: unknown command\n', log_message

        except Exception as e:
            # print(f'Erreur traitement message: {e}')
            # traceback.print_exc()
            return 'error\n', f"ERROR - Exception lors du traitement du message: {e}"
        
    def handleLog(self, log_data):
        """Gère les messages de log reçus des workers"""
        try:
            client_id, message = log_data.split('||', 1)
            self.parent.addLog('ACTION', f"{client_id} : {message}")
        except Exception as e:
            print(f'Erreur handleLog: {e}')

    def signalFromClient(self, sig):
        client_id = sig[0]
        client_address = sig[1]

        if client_address == 0:
            if client_id in self.clientList:
                del self.clientList[client_id]
            if client_id in self.client_heartbeats:
                del self.client_heartbeats[client_id]
            self.parent.addLog('CLIENT', f"Déconnexion du client :  {client_id}")
        
        else:
            if client_id in self.clientList:
                # print('le client existe')
                self.client_heartbeats[client_id] = time.time()
            else:
                self.clientList[client_id] = client_address
                self.client_heartbeats[client_id] = time.time()
                self.parent.addLog('CLIENT', f"✅ connexion du nouveau client :{client_id}")
        #print(f'Clients actifs: {len(self.clientList)}')
        #print('client list:', self.clientList)
        #txt = "\n".join([f"{key}: {value}" for key, value in self.clientList.items()])
        self.parent.clientCountLabel.setText(str(len(self.clientList)))

    def updateHeartbeat(self, client_id):
        self.client_heartbeats[client_id] = time.time()

    def check_dead_clients(self):
        while self.isConnected:
            try:
                time.sleep(self.heartbeat_check_interval)

                current_time = time.time()
                dead_clients = []

                for client_id, last_seen in list(self.client_heartbeats.items()):
                    if current_time - last_seen > self.heartbeat_timeout:
                        dead_clients.append(client_id)

                for client_id in dead_clients:
                    self.parent.addLog('SYSTEM',f'💀 Client mort détecté (timeout {self.heartbeat_timeout}s): {client_id}')
                    self.signalFromClient([client_id, 0])

                if dead_clients:
                    print(f'Nettoyage de {len(dead_clients)} client(s) mort(s)')

            except Exception as e:
                print(f'Erreur check_dead_clients: {e}')

        print('Thread heartbeat arrêté')

    def updateFromRSAI(self, a):
        print('updateFromRSAI dans SERVERZMQ')
        self.parent.updateFromRSAI()
        time.sleep(0.5)
        self.conf = self.parent.conf
        self.listRackIP = self.parent.listRackIP
        self.dict_moteurs = self.parent.dict_moteurs

    def stopThread(self):
        self.isConnected = False
        time.sleep(4)
        try: 
            self.frontend.close()
            self.backend.close()
            self.context.term()
            print('Serveur ZMQ arrêté')
        except Exception as e :
            print(f'error arret fronted  {e}')



class checkBox(QCheckBox):
    def __init__(self, name='test', ip='', parent=None):
        super(checkBox, self).__init__()
        self.parent = parent
        self.ip = ip
        self.name = name
        self.setText(self.name + ' ( ' + self.ip + ')')
        self.setObjectName(self.ip)


class THREADRACKCONNECT(QtCore.QThread):
    def __init__(self, PilMot, parent=None):
        super(THREADRACKCONNECT, self).__init__(parent)
        self.parent = parent
        self.PilMot = PilMot
        self.stop = False

    def run(self):
        while not self.stop:
            nbEqu = len(self.parent.listRackIP)
            for numEsim in range(0, nbEqu):
                rcon = self.PilMot.rEtatConnexion(ctypes.c_int16(numEsim))
                if rcon == 3:
                    self.parent.box[numEsim].setChecked(True)
                else:
                    self.parent.box[numEsim].setChecked(False)
            time.sleep(1)

    def stopThread(self):
        print('thread check rack stopped')
        self.stop = True


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
            # print('actions',action)
            # Coloration selon le type d'action
            if 'system' in action.lower():
                color = "#4a9eff"  # Bleu pour les mouvements
                icon = "→"
            elif 'error' in action.lower():
                color = "#ff6b6b"  # Rouge pour les arrêts
                icon = "⏹"
            elif 'action' in action.lower():
                color = "#ffd43b"  # Jaune pour zero
                icon = "⓪"
            elif 'client' in action.lower():
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


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    server = SERVERRSAI(test=True)
    server.show()
    sys.exit(app.exec())
