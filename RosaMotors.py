#!/home/sallejaune/loaenv/bin/env python
# -*- coding: utf-8 -*-
#last modified 27/05/25

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QVBoxLayout,QHBoxLayout,QPushButton,QGridLayout,QTreeWidget,QTreeWidgetItem
from PyQt6.QtWidgets import QLabel,QSizePolicy,QTreeWidgetItemIterator,QProgressBar
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtCore import pyqtSlot
import qdarkstyle,sys
import ast
import socket as _socket
import time
import os
import pathlib
from oneMotorGuiServerRSAI import ONEMOTORGUI
from threeMotorGuiFB import THREEMOTORGUI
from TiltGui import TILTMOTORGUI
from PyQt6 import QtCore
import tirSalleJaune as tirSJ

class MAINMOTOR(QWidget):
    """  widget tree with IP adress and motor
 
    """
    updateBar_signal = QtCore.pyqtSignal(object)
    
    def __init__(self, chamber=None,parent=None):

        super(MAINMOTOR, self).__init__(parent)
        self.isWinOpen = False
        self.parent = parent
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.progressWin = ProgressScreen(parent = self)
        self.progressWin.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)
        self.progressWin.show()
        text = 'Loading  program  : ...'
        self.updateBar_signal.emit([text,2])

        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        

        fileconf = str(p.parent) + sepa + "confServer.ini"
        print(fileconf)
        self.confServer = QtCore.QSettings(fileconf,QtCore.QSettings.Format.IniFormat)
        self.server_host = str( self.confServer.value('MAIN'+'/server_host') )# 
        self.serverPort =int(self.confServer.value('MAIN'+'/serverPort'))
        self.clientSocket = _socket.socket(_socket.AF_INET,_socket.SOCK_STREAM)
        self.chamber = chamber
        try :
            self.clientSocket.connect((self.server_host,self.serverPort))
            self.isconnected = True
        except :
            self.isconnected = False
        self.widdgetTir = tirSJ.SalleJauneConnect()
        self.aff()

    def aff(self):
        
        cmdsend = " %s" %('listRack',)
        self.clientSocket.sendall((cmdsend).encode())
        self.listRack = self.clientSocket.recv(1024).decode()
        self.listRack = ast.literal_eval(self.listRack)
        self.motItem = []
        self.rackName = []
        self.motorCreatedId = []
        self.motorCreated = []

        for IP in self.listRack:
            cmd = 'nomRack'
            cmdsend = " %s, %s, %s " %(IP,1,cmd)
            self.clientSocket.sendall((cmdsend).encode())
            nameRack = self.clientSocket.recv(1024).decode().split()[0]
            self.rackName.append(nameRack)

        self.rack = dict(zip(self.rackName,self.listRack)) # dictionnaire key name of the rack values IPadress
        self.listMotorName = []
        self.listMotButton = list()
        irack = 0 
        self.dic_moteurs={}
        pp = '.'
        self.pourcent = 0 
        for IP in self.listRack: 
            text = 'Set motors Parameters '  + pp
            self.pourcent = self.pourcent + 1
            self.updateBar_signal.emit([text,self.pourcent])
            dict_name = "self.dictMotor" + "_" + str(IP)
            num = list(range(1,15))
            listMot = []
            for i in range(0,14):
                cmd = 'name'
                cmdsend = " %s, %s, %s " %(IP,i+1,cmd)
                self.clientSocket.sendall((cmdsend).encode())
                name = self.clientSocket.recv(1024).decode().split()[0]
                self.listMotorName.append(name)
                listMot.append(name)
    
            irack+=1
            self.dic_moteurs[dict_name] = dict(zip(listMot,num))
            self.dic_moteurs[dict_name]['ip'] = str(IP)
       
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
                ppp='.'
                for i in range(0,14):
                    cmd = 'name'
                    cmdsend = " %s, %s, %s " %(IP,i+1,cmd)
                    self.clientSocket.sendall((cmdsend).encode())
                    name = self.clientSocket.recv(1024).decode().split()[0]
                    self.listMotorNameFilter.append(name)
                    text = 'connect motor to server '+ IP + " : " + str(name) + ppp
                    ppp = ppp +'.'
                    self.pourcent = self.pourcent + 1 
                    self.updateBar_signal.emit([text,self.pourcent])

        text = 'widget loading ...'
        self.updateBar_signal.emit([text,self.pourcent])           
        self.SETUP()
        self.updateBar_signal.emit(['end',100])
        self.EXPAND()
        self.progressWin.close()


    def SETUP(self):
        vbox1 = QVBoxLayout()

        vbox1.addWidget(self.widdgetTir)
        chamberName = QLabel()
        chamberName.setText('Motors Control: %s' % self.chamber)
        chamberName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox1.addWidget(chamberName)
        self.butWarning=QLabel('Focal Spot Miror')
        self.butWarning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.anim = QtCore.QPropertyAnimation(self.butWarning, b"size",self)
        self.anim.setStartValue(QtCore.QSize(20, 25))
        self.anim.setEndValue(QtCore.QSize(350, 25))
        self.anim.setDuration(5000)
        self.anim.setLoopCount(-1)
        vbox1.addWidget(self.butWarning)
        
        self.tree = QTreeWidget()
        self.tree.header().hide()
        z = 0
        if self.chamber is not None:
            self.setWindowTitle('  Client RSAI  ' + self.chamber)
            for i in range (0,len(self.rackNameFilter)):
                rackTree = QTreeWidgetItem(self.tree,[self.rackNameFilter[i]])
                for j in range (0,14):
                    self.motItem.append( QTreeWidgetItem(rackTree,[self.listMotorNameFilter[z],'']))
                    z+= 1  
                    text = 'widget loading ...'
                    self.updateBar_signal.emit([text,self.pourcent])
                    self.pourcent= self.pourcent + 1
        else :
            self.setWindowTitle('Client RSAI ')
            for i in range (0,len(self.listRack)):
                rackTree = QTreeWidgetItem(self.tree,[self.rackName[i]])
                for j in range (0,14):
                    self.motItem.append( QTreeWidgetItem(rackTree,[self.listMotorName[z],'']))
                    z+= 1
                    self.updateBar_signal.emit([text,self.pourcent])
                    self.pourcent= self.pourcent + 1

        vbox1.addWidget(self.tree)
        self.setLayout(vbox1)

        self.tree.itemClicked.connect(self.actionPush)
        self.tree.itemExpanded.connect(self.EXPAND)
        self.tree.itemCollapsed.connect(self.EXPAND)
        self.resize(self.sizeHint().width(),self.minimumHeight())
        self.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Maximum)
        
        ################################################################################################""
        # Special Button
        ###############################################################################################
        grid_layout = QGridLayout()
        text = 'special button '
        self.pourcent= self.pourcent + 1
        self.updateBar_signal.emit([text,self.pourcent])
        self.pourcent= self.pourcent + 1
        # self.lame = THREEMOTORGUI(IPVert='10.0.1.30', NoMotorVert = 10 , IPLat='10.0.1.30', NoMotorLat = 7, IPFoc='10.0.1.30', NoMotorFoc=8, nomWin= 'Lame rosa')
        # self.lame_But = QPushButton('Lame')
        # self.lame_But.clicked.connect(lambda:self.open_widget(self.lame))

        self.camWidget = THREEMOTORGUI(IPVert='10.0.1.31', NoMotorVert = 12 , IPLat='10.0.1.31', NoMotorLat = 8,IPFoc='10.0.1.31', NoMotorFoc=10, nomWin= 'Cam Focal Spot')
        self.cam_But = QPushButton('CAM')
        self.cam_But.clicked.connect(lambda:self.open_widget(self.camWidget))

        self.P1TB = TILTMOTORGUI('10.0.1.30',2,'10.0.1.30',1,nomWin='P1 Turning Box ',nomTilt='P1 TB')
        self.P1TB_But = QPushButton('P1 TB')
        self.P1TB_But.clicked.connect(lambda:self.open_widget(self.P1TB))

        self.P2TB = TILTMOTORGUI('10.0.1.30',4,'10.0.1.30',3,nomWin='P2 Turning Box ',nomTilt='P2TB')
        self.P2TB_But = QPushButton('P2 TB')
        self.P2TB_But.clicked.connect(lambda:self.open_widget(self.P2TB))

        self.updateBar_signal.emit([text,self.pourcent])
        self.pourcent= self.pourcent + 1
        
        self.P3TB = TILTMOTORGUI(IPLat='10.0.1.30',NoMotorLat=6,IPVert='10.0.1.30',NoMotorVert=5,nomWin='P3 Turning Box ',nomTilt='P3TB')
        self.P3TB_But = QPushButton('P3 TB')
        self.P3TB_But.clicked.connect(lambda:self.open_widget(self.P3TB))

        self.P1M = TILTMOTORGUI('10.0.1.31',4,'10.0.1.31',3,nomWin='P1 mirror  ',nomTilt='P1 M')
        self.P1Mir_But = QPushButton('P1 Mir')
        self.P1Mir_But.clicked.connect(lambda:self.open_widget(self.P1M))

        self.updateBar_signal.emit([text,self.pourcent])
        self.pourcent= self.pourcent + 1

        self.P2Mir_But = QPushButton('P2 Mir')
        self.P2Mir_But.setEnabled(True)
        
        self.P3Mir_But = QPushButton('P3 Mir')
        self.P3Mir_But.setEnabled(True)
        
        self.P1OPA = TILTMOTORGUI('10.0.1.31',2,'10.0.1.31',1,nomWin='P1 OPA ',nomTilt='P1 OPA')
        self.P1OAP_But = QPushButton('P1 OAP')
        self.P1OAP_But.clicked.connect(lambda:self.open_widget(self.P1OPA ))
        
        self.jet = THREEMOTORGUI(IPVert='10.0.1.31', NoMotorVert = 13, IPLat='10.0.1.31', NoMotorLat = 11, IPFoc='10.0.1.31', NoMotorFoc=14, nomWin= 'JET rosa')
        self.jet_But = QPushButton('Jet')
        self.jet_But.clicked.connect(lambda:self.open_widget(self.jet))
        
        self.jet2 = THREEMOTORGUI(IPVert='10.0.3.31', NoMotorVert = 1, IPLat='10.0.3.31', NoMotorLat = 5, IPFoc='10.0.3.31', NoMotorFoc=11, nomWin= 'jet 2 ')
        self.jet2_But = QPushButton('Jet 2')
        self.jet2_But.clicked.connect(lambda:self.open_widget(self.jet2))
        
        self.cam2 = THREEMOTORGUI(IPVert='10.0.1.30', NoMotorVert = 12, IPLat='10.0.1.30', NoMotorLat = 13, IPFoc='10.0.1.30', NoMotorFoc=14, nomWin= 'Compton')
        self.cam2_But = QPushButton('Cam2')
        self.cam2_But.clicked.connect(lambda:self.open_widget(self.cam2 ))

        grid_layout.addWidget(self.P1TB_But,0,0)
        grid_layout.addWidget(self.P2TB_But,0,1)
        grid_layout.addWidget(self.P3TB_But,0,2)
        grid_layout.addWidget(self.P1Mir_But,1,0)
        grid_layout.addWidget(self.P2Mir_But,1,1)
        grid_layout.addWidget(self.P3Mir_But,1,2)
        grid_layout.addWidget(self.P1OAP_But ,2,0)
        grid_layout.addWidget(self.jet_But,2,1)
        grid_layout.addWidget(self.cam_But,2,2)
        grid_layout.addWidget(self.jet2_But,3,0)
        grid_layout.addWidget(self.cam2_But,3,1)

        self.updateBar_signal.emit([text,self.pourcent])
        self.pourcent= self.pourcent + 1

        ## Focal Spot 
        self.motFS = ONEMOTORGUI(IpAdress="10.0.1.31", NoMotor = 5, showRef=False, unit=1,jogValue=100,parent=self)
        self.thread = PositionThread(self,mot=self.motFS.MOT[0]) # thread for displaying position
        self.thread.POS.connect(self.Position)
        self.thread.ThreadINIT()
        self.thread.start()
        self.ref0 = self.motFS.refValueStep[0]
        self.ref1 = self.motFS.refValueStep[1]

        vbox1.addLayout(grid_layout)
        self.updateBar_signal.emit([text,self.pourcent])
        self.pourcent= self.pourcent + 1

    @pyqtSlot(object)   
    def Position(self,Posi):
        ''' 
        Position  display read from the second thread
        '''
        self.Posi = Posi
        Pos = Posi[0]
        self.etat = str(Posi[1])
        #a = float(Pos)* float((self.motFS.stepmotor[0]))
        
        if self.ref0 - 100 < Pos < self.ref0 + 100 :
            self.butWarning.setStyleSheet("background-color:red")
            self.butWarning.setText('Focal Spot Miror : IN')
            
            self.anim.start()
           

        elif self.ref1 - 100 < Pos < self.ref1 + 100 :
            self.butWarning.setStyleSheet("background-color:green")
            self.butWarning.setText('Focal Spot Miror : OUT')
            self.anim.stop()
        else :
            self.butWarning.setStyleSheet("background-color: transparent ")
            self.butWarning.setText('Focal Spot Miror : ?')
            self.anim.stop()

    def actionPush(self,item:QTreeWidgetItem,colum:int):
        
        if item.parent() :
            rackname = item.parent().text(0)
            motorname = item.text(0)
            ip = self.rack[rackname]
            numMot = self.dic_moteurs["self.dictMotor" + "_" + str(ip)][item.text(0)]
            motorID = str(ip)+'M'+str(numMot)
            if motorID in self.motorCreatedId: 
                index = self.motorCreatedId.index(motorID)
                self.open_widget(self.motorCreated[index])
            else :
                self.motorWidget = ONEMOTORGUI(ip,numMot)
                time.sleep(0.1)
                self.open_widget(self.motorWidget)
                self.motorCreatedId.append(motorID)
                self.motorCreated.append(self.motorWidget)

    def EXPAND(self):
        row = 20
        rowH = self.tree.sizeHintForRow(0)
        totalH = row * rowH 
        count = 0
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.parent():
                if item.parent().isExpanded():
                    count +=1
            else:
                count += 1
            iterator += 1

        totalH = row * count 
        self.resize(self.sizeHint().width(),totalH + 50)

    def actionButton(self):
        self.upRSAI.clicked.connect(self.updateFromRsai)
         
    def updateFromRsai(self):
        print('update')
        cmdsend = " %s" %('updateFromRSAI',)
        self.clientSocket.sendall((cmdsend).encode())
        errr = self.clientSocket.recv(1024).decode()
        self.listMotorName = []
        self.listMotButton = list()
        irack = 0 

        for IP in self.listRack: 
            for i in range(0,14):
                cmd = 'name'
                cmdsend = " %s, %s, %s " %(IP,i+1,cmd)
                self.clientSocket.sendall((cmdsend).encode())
                name = self.clientSocket.recv(1024).decode().split()[0]
                self.listMotorName.append(name)
                self.listMotButton.append(QPushButton(name,self))
            irack+=1
        
    def open_widget(self,fene):
        
        """ open new widget 
        """
        if fene.isWinOpen is False:
            #New widget"
            fene.show()
            fene.startThread2()
            fene.isWinOpen = True
        else:
            #fene.activateWindow()
            fene.raise_()
            fene.showNormal()

    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.isWinOpen = False
        for mot in self.motorCreated:
            mot.close()
        time.sleep(0.1)    
        self.clientSocket.close()
        time.sleep(0.1)
        event.accept()
        


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    import time 
    POS = QtCore.pyqtSignal(object) # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self,parent=None,mot='',):
        super(PositionThread,self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False
        self.positionSleep = 1
        self.etat_old = ""
        self.Posi_old = 0

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                
                Posi = (self.MOT.position())
                time.sleep(self.positionSleep)
                etat = self.MOT.etatMotor()
                try :
                    # print(etat)
                    #time.sleep(0.1)
                    if self.Posi_old != Posi or self.etat_old != etat: # on emet que si different
                        self.POS.emit([Posi,etat])
                        self.Posi_old = Posi
                        self.etat_old = etat
                    
                except:
                    print('error emit')
                  
    def ThreadINIT(self):
        self.stop = False   
                        
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)

class ProgressScreen(QWidget):
    '''class pour la progress bar au demarage de l'application 
    '''
    def __init__(self,parent=None):

        super().__init__()

        self.parent = parent 
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons' + sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setWindowTitle(' Loading ...')
        self.setGeometry(600, 300, 300, 100)
        #self.setWindowFlags(Qt.WindowType.FramelessWindowHint| Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout()

        self.label = QLabel('Loading ')
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label2 = QLabel("Laboratoire d'Optique Appliquée")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label2.setStyleSheet('font :bold 20pt;color: white')
        self.action = QLabel('Load visu')
        layout.addWidget(self.label2)
        layout.addWidget(self.label)
        layout.addWidget(self.action)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        if self.parent is not None:
            self.parent.updateBar_signal.connect(self.setLabel)

    def setLabel(self,labels) :
        label = labels[0]
        val = labels[1]
        self.action.setText(str(label))
        self.progress_bar.setValue(int(val))
        QtCore.QCoreApplication.processEvents() # c'est moche mais pas de mise  jour sinon ???
if __name__ == '__main__':
    appli = QApplication(sys.argv)
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    s = MAINMOTOR(chamber ='rosa')
    s.show()
    appli.exec_()