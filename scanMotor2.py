#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 20:23:31 2019

@author: juliengautier
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox, QProgressBar
from PyQt6.QtWidgets import QComboBox, QLabel
from PyQt6.QtGui import QIcon
import tirSalleJaune as tirSJ
import sys
import time
import qdarkstyle
import numpy as np
from PyQt6.QtCore import pyqtSignal as Signal
import socket as _socket

# #### To be modified and tested


class SCAN(QWidget):
    """ scan widget
    MOT= motor object
    """
    def __init__(self, MOT, parent=None):
        
        super(SCAN, self).__init__(parent)
        
        self.isWinOpen = False
        self.parent = parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.MOT = MOT

        self.indexUnit = 1
        try:
            self.name = self.MOT.name
            self.stepmotor = 1/self.MOT.getStepValue()
            self.setWindowTitle('Scan  : ' + str(self.MOT.getEquipementName()) + ' (' + str(self.MOT.IpAddress) + ')  ' + ' [M'+ str(self.MOT.NoMotor) + ']  ' + self.MOT.name)
        except Exception as e:
            print('error in scan ', e)

        self.setup()
        self.actionButton()
        self.unit()
        self.threadScan = ThreadScan(self)
        self.threadScan.nbRemain.connect(self.Remain)
        self.threadScan.info.connect(self.infoWrite)
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.threadShoot = ThreadShoot(self)
        self.threadShoot.nbRemainShoot.connect(self.RemainShoot)

    def startTrigThread(self):
        self.threadScan.trigClient.start()

    def setup(self):
        self.vbox = QVBoxLayout()
        hboxTitre = QHBoxLayout()
        self.nom = QLabel(self.name)
        self.nom.setStyleSheet("font: bold 30pt")
        hboxTitre.addWidget(self.nom)
        self.vbox.addLayout(hboxTitre)
        
        self.unitBouton = QComboBox()
        self.unitBouton.addItem('Step')
        self.unitBouton.addItem('um')
        self.unitBouton.addItem('mm')
        self.unitBouton.addItem('ps')
        self.unitBouton.addItem('°')
        self.unitBouton.setMaximumWidth(100)
        self.unitBouton.setMinimumWidth(100)
        self.unitBouton.setCurrentIndex(self.indexUnit)
        
        hboxTitre.addWidget(self.unitBouton)
        
        lab_nbStepRemain = QLabel('Remaining step')
        self.val_nbStepRemain = QLabel(self)
        
        hboxTitre.addWidget(lab_nbStepRemain)
        hboxTitre.addWidget(self.val_nbStepRemain)

        self.progressBar = QProgressBar()
        hboxTitre.addWidget(self.progressBar)
        hboxTitre.addSpacing(100)
        self.infoText = QLabel('...')
        hboxTitre.addWidget(self.infoText)
        self.lab_nbr_step = QLabel('nb of step')
        self.val_nbr_step = QDoubleSpinBox(self)
        
        self.val_nbr_step.setMaximum(10000)
        self.val_nbr_step.setMinimum(1)
        self.val_nbr_step.setValue = 10
        
        self.lab_step = QLabel("step value")
        self.val_step = QDoubleSpinBox()
        self.val_step.setMaximum(10000)
        self.val_step.setMinimum(-10000)
        self.lab_ini = QLabel('ini value')
        self.val_ini = QDoubleSpinBox()
        self.val_ini.setMaximum(10000)
        self.val_ini.setMinimum(-10000)
        
        self.lab_fin = QLabel('Final value')
        self.val_fin = QDoubleSpinBox()
        self.val_fin.setMaximum(10000)
        self.val_fin.setMinimum(-10000)
        self.val_fin.setValue(100)
        
        self.lab_nbTir = QLabel('Nb of shoot')
        self.val_nbTir = QDoubleSpinBox()
        self.val_nbTir.setMaximum(100)
        self.val_nbTir.setValue(1)
        self.val_nbShoot = self.val_nbTir.value()
        self.lab_time = QLabel('Frequence')
        self.val_time = QDoubleSpinBox()
        self.val_time.setMaximum(1)
        self.val_time.setSuffix(" %s" % 'Hz')
        self.val_time.setValue(0.1)
        #self.val_time.setDecimals(1)
        
        self.but_start = QPushButton('Start sequence')
        self.but_stop = QPushButton('STOP')
        self.but_stop.setStyleSheet("border-radius:20px;background-color: red")
        self.but_stop.setEnabled(False)
        
        self.but_Shoot = QPushButton('Shoot')
        
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.lab_nbr_step  , 0, 0)
        grid_layout.addWidget(self.val_nbr_step  , 0, 1)
        grid_layout.addWidget(self.lab_step  , 0, 2)
        grid_layout.addWidget(self.val_step  , 0, 3)
        grid_layout.addWidget(self.but_start,0,4)
        grid_layout.addWidget(self.lab_ini,1,0)
        grid_layout.addWidget(self.val_ini,1,1)
        grid_layout.addWidget(self.lab_fin,1,2)
        grid_layout.addWidget(self.val_fin,1,3)
        grid_layout.addWidget(self.but_stop,1,4)
        grid_layout.addWidget(self.lab_nbTir,2,0)
        grid_layout.addWidget(self.val_nbTir,2,1)
        grid_layout.addWidget(self.lab_time,2,2)
        grid_layout.addWidget(self.val_time,2,3)
        grid_layout.addWidget(self.but_Shoot,2,4)
        self.vbox.addLayout(grid_layout)
        self.setLayout(self.vbox)
 
    def actionButton(self):
        '''
           buttons action setup 
        '''
        self.unitBouton.currentIndexChanged.connect(self.unit)
        self.val_nbr_step.editingFinished.connect(self.stepChange)
        self.val_ini.editingFinished.connect(self.stepChange)
        self.val_fin.editingFinished.connect(self.stepChange)
        self.val_step.editingFinished.connect(self.changeFinal)
        self.but_start.clicked.connect(self.startScan)
        self.but_stop.clicked.connect(self.stopScan)
        self.but_Shoot.clicked.connect(self.startShoot)

    def infoWrite(self,txt):
        self.infoText.setText(txt)

    def startShoot(self):

        self.stepChange()
        self.threadShoot.start()
        self.lab_nbr_step.setEnabled(False)
        self.val_nbr_step.setEnabled(False)
        self.lab_step.setEnabled(False)
        self.lab_ini.setEnabled(False)
        self.val_step.setEnabled(False)
        self.val_ini.setEnabled(False)
        self.lab_fin.setEnabled(False)
        self.val_fin.setEnabled(False)
        self.lab_nbTir.setEnabled(False)
        self.val_nbTir.setEnabled(False)
        self.lab_time.setEnabled(False)
        self.val_time.setEnabled(False)
        self.but_start.setEnabled(False)
        self.but_Shoot.setEnabled(False)
        self.but_stop.setEnabled(True)
        self.but_stop.setStyleSheet("border-radius:20px;background-color: red")
        a = tirSJ.Tir()
        print(a)
        
        if a == 0 or a == "":
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Not connected !")
            msg.setInformativeText("Please connect !!")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()
       
    def stopScan(self):
        
        self.threadScan.stopThread()
        self.threadShoot.stopThread()
        self.MOT.stopMotor()
        self.lab_nbr_step.setEnabled(True)
        self.val_nbr_step.setEnabled(True)
        self.lab_step.setEnabled(True)
        self.lab_ini.setEnabled(True)
        self.val_step.setEnabled(True)
        self.val_ini.setEnabled(True)
        self.lab_fin.setEnabled(True)
        self.val_fin.setEnabled(True)
        self.lab_nbTir.setEnabled(True)
        self.val_nbTir.setEnabled(True)
        self.lab_time.setEnabled(True)
        self.val_time.setEnabled(True)
        self.but_start.setEnabled(True)
        self.but_Shoot.setEnabled(True)
        self.but_stop.setEnabled(False)
        self.but_stop.setStyleSheet("border-radius:20px;background-color: red")
        #a = tirSJ.stopTir()

    def Remain(self,nbstepdone,nbMax):
        self.val_nbStepRemain.setText(str((nbstepdone)))
        self.progressBar.setMaximum(int(nbMax))
        self.progressBar.setValue(nbMax-nbstepdone)
        
        if nbstepdone == 0 :
            print ('fin scan remain')
            self.val_nbStepRemain.setText('scan done')
            self.stopScan()
            
    def RemainShoot(self, nbstepdone)   :
        #print('remain shoot', nbstepdone, self.nbStep)
        
        self.val_nbStepRemain.setText(str((nbstepdone)))
        
        if self.val_nbShoot == nbstepdone:
            print ('fin scan multi shoot')
            self.stopScan()
            
    def stepChange(self):
        self.nbStep = self.val_nbr_step.value()
        self.vInit = self.val_ini.value()
        self.vFin = self.val_fin.value()
        if self.nbStep == 1:
            self.vStep = self.vFin-self.vInit
        else :
            self.vStep = (self.vFin-self.vInit)/(self.nbStep-1)
        self.val_step.setValue(self.vStep)
        self.val_nbShoot = self.val_nbTir.value()
        
    def changeFinal(self):
       self.nbStep = self.val_nbr_step.value()
       self.vInit = self.val_ini.value()
       self.vStep = self.val_step.value()
       self.vFin = self.vInit + (self.nbStep-1) * self.vStep
       self.val_fin.setValue(self.vFin)
       self.val_nbShoot = self.val_nbTir.value()
    
    def startScan(self):
        self.stepChange()
        self.threadScan.start()
        self.lab_nbr_step.setEnabled(False)
        self.val_nbr_step.setEnabled(False)
        self.lab_step.setEnabled(False)
        self.lab_ini.setEnabled(False)
        self.val_step.setEnabled(False)
        self.val_ini.setEnabled(False)
        self.lab_fin.setEnabled(False)
        self.val_fin.setEnabled(False)
        self.lab_nbTir.setEnabled(False)
        self.val_nbTir.setEnabled(False)
        self.lab_time.setEnabled(False)
        self.val_time.setEnabled(False)
        self.but_start.setEnabled(False)
        self.but_Shoot.setEnabled(False)
        self.but_stop.setEnabled(True)
        self.but_stop.setStyleSheet("border-radius:20px;background-color: red")
    
    def unit(self):
        '''
        unit change mot foc
        '''
        ii = self.unitBouton.currentIndex()
        if ii == 0: #  step
            self.unitChange = 1
            self.unitName = 'step'
            
        if ii == 1: # micron
            self.unitChange = float((1*self.stepmotor)) 
            self.unitName = 'um'
        if ii == 2: #  mm 
            self.unitChange = float((self.stepmotor)/1000)
            self.unitName='mm'
        if ii == 3: #  ps  double passage : 1 microns=6fs
            self.unitChange = float(1*self.stepmotor*0.0066666666) 
            self.unitName = 'ps'
        if ii == 4: #  en degres
            self.unitChange = 1 *self.stepmotor
            self.unitName='°'    
            
        if self.unitChange == 0:
            self.unitChange = 1 #avoid 0 
        
        self.val_step.setSuffix(" %s" % self.unitName)
        self.val_ini.setSuffix(" %s" % self.unitName)
        self.val_fin.setSuffix(" %s" % self.unitName)
 
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False
        
        self.threadScan.trigClient.stopClientThread()
        time.sleep(0.1)
        #print('close scan widget')
        event.accept() 
    

class ThreadShoot(QtCore.QThread):
    nbRemainShoot = QtCore.pyqtSignal(float)
    
    def __init__(self, parent=None):
        super(ThreadShoot, self).__init__(parent)
        self.parent = parent
        self.stop = False
        
    def run(self):
        self.stop = False
        nb = 0
        for nu in range(0, int(self.parent.val_nbTir.value())):
            if self.stop is True:
                break
            nb += 1
            time.sleep(self.parent.val_time.value())
            nbstepdone = nb
            self.nbRemainShoot.emit(nbstepdone)
            
    def stopThread(self):
        self.stop = True
        print( "stop thread Shoot" ) 
        
        
        
class ThreadScan(QtCore.QThread):
   
    nbRemain = QtCore.pyqtSignal(int,int)
    info = QtCore.pyqtSignal(str) # to send info to main widget 

    def __init__(self, parent=None):
        super(ThreadScan,self).__init__(parent)
        self.parent = parent
        self.stop = False
        date = time.strftime("%Y_%m_%d_%H_%M_%S")
        
        #self.trigClient = THREADCLIENTTRIG(parent = self)
        #self.trigClient.newShotnumber.connect(self.TrigReceived)
        #self.trigClient.emitConnected = False
        # self.trigClient.start()
        self.trigNumber = 0
        self.mvt = 0 
        self.nbshooted = 0 # nombre de tir effectuée
    
    def TrigReceived(self, nbshoot):
        print('new trig')
        precis = 5  # precision for position checking
        self.nbshoot = nbshoot
        self.trigNumber = self.trigNumber + 1 # nombre de tir sans bouger 
        self.nbshooted = self.nbshooted + 1  # nombre total de tir 
        
        if int(self.nbshooted) >= int(self.nbTotShot) :
            self.trigClient.emitConnected = False
            print('scan multishoot finished')
            self.info.emit('Sequence ended at %s, duration: %.1f min' % (time.ctime(), (time.time()-self.t1)/60 ))

        elif self.trigNumber < (self.val_nbTir):
            print('on a tiré',self.trigNumber,' sans bouger' )
            self.info.emit("Trig shoot without moving   %s" % str(self.trigNumber))

        elif self.trigNumber == (self.val_nbTir):
            print('on a assez tiré : ',self.trigNumber,' sans bouger' )
            print('on bouge le moteur',self.movement[self.mvt])
            self.info.emit("shoot without moving   %s" % str(self.trigNumber))
            self.info.emit("motor move to   %s" % str(round(self.movement[self.mvt]*self.parent.unitChange,2)) )
            self.parent.MOT.move(self.movement[self.mvt])
            while True:
                        if self.stop is True:
                            break
                        else :
                            b = self.parent.MOT.position()
                            print('position ', b,self.movement[self.mvt] - precis ,self.movement[self.mvt] + precis )
                            time.sleep(0.1)
                            
                            if self.movement[self.mvt] - precis < b < self.movement[self.mvt] + precis :
                                print("position reached", str(b))
                                self.info.emit("position reached  %s" % round(b*self.parent.unitChange,2)) 
                                break
            print('multishot ici',self.freq,self.val_nbTir)
            time.sleep(8) # cat labview 
            tirSJ.multi_shot(self.freq,self.val_nbTir)
            print('tir envoye multi')
            msg = 'multi shot %s @ %s' % (str(self.freq), str(self.val_nbTir))
            self.info.emit(msg)              
            self.mvt = self.mvt +1 
            self.trigNumber = 0
        
        self.nbRemain.emit(int(self.nbTotShot- self.nbshooted),int(self.nbTotShot))
        
    def run(self):

        print('run sequence')
        self.nbshooted = 0
        self.stop = False
        
        self.info.emit('Start sequence (at %s)' % time.ctime())

        self.vini = self.parent.vInit/self.parent.unitChange
        self.vfin = self.parent.vFin/self.parent.unitChange
        self.step = self.parent.vStep/self.parent.unitChange
        self.val_time = self.parent.val_time.value()
        self.val_nbTir = self.parent.val_nbTir.value()
        
        if self.val_time == 1:
            self.freq = 3
            self.multi = True
        elif self.val_time == 0.5:  
            self.freq = 2
            self.multi = True
        elif self.val_time == 0.2 :
            self.freq = 1
            self.multi = True
        elif self.val_time == 0.1 :
            self.freq = 0
            self.multi = True
        else:
            self.val_time = 1/self.val_time
            self.multi = False

        self.parent.MOT.move(self.vini)
        self.t1 = time.time()
        b = self.parent.MOT.position()
        while b!= self.vini:
            if self.stop is True:
                break
            else:	
                time.sleep(0.1)
                b = self.parent.MOT.position()

        time.sleep(0.1)

        self.info.emit("first position reached %s" % round(b*self.parent.unitChange,2))
        self.movement = np.arange(self.vini+self.step,self.vfin+self.step,self.step)
        print(self.movement)
        self.nbTotShot = int( (np.size(self.movement) +1 ) * self.val_nbTir)
        self.nbRemain.emit(int(self.nbTotShot),int(self.nbTotShot))
        nb = 0

        if self.multi is True : 
                
                print('multishoot @%s' % str(self.freq))
                print('number of shot /mvt%s' % str(self.val_nbTir))
                self.mvt = 0 
                self.trigClient.emitConnected = True
                tirSJ.multi_shot(self.freq,self.val_nbTir)
                print('%s tir envoye @%s'% (str(self.freq), str(self.val_nbTir)))

        else : # premier tir a la position ini pas compris dans self.movement
            for nu in range (0,int(self.val_nbTir)):
                            nb+=1
                            self.info.emit('shot')
                            a = tirSJ.Tir()
                            print('shot' )
                            if a == 0 or a == "":
                                print('error shot')
                                self.nbRemain.emit(int(self.nbTotShot-nb),int(self.nbTotShot))
                                print('wait',self.val_time)
                                self.info.emit('wait '+ str(self.val_time)+ "s")
                                time.sleep(self.val_time)

            for mv in self.movement:
                
                if self.stop is True:
                    break
                else:
                    mv = int(mv)
                    self.parent.MOT.move(mv)
                    b = self.parent.MOT.position()
                    b = int(b)
                    while True:
                        if self.stop is True:
                            break
                        else :
                            b = self.parent.MOT.position()
                            time.sleep(0.1)
                            precis = 1
                            if b == mv :
                                print( "position reached", str(b))
                                self.info.emit("position reached  %s" % round(b*self.parent.unitChange,2)) 
                                break
                        
                        for nu in range (0,int(self.val_nbTir)):
                            nb+=1
                            self.info.emit('shot')
                            a = tirSJ.Tir()
                            print('shot' )
                            if a == 0 or a == "":
                                print('error shot')
                                self.nbRemain.emit(int(self.nbTotShot-nb),int(self.nbTotShot))
                                print('wait',self.val_time)
                                self.info.emit('wait '+ str(self.val_time)+ "s")
                                time.sleep(self.val_time)

        if self.multi is False :
            self.info.emit('Sequence ended at %s, duration: %.1f min' % (time.ctime(), (time.time()-self.t1)/60 ))
            self.parent.stopScan()

    def stopThread(self):
        self.stop = True
        self.trigClient.emitConnected = False
        print( "stop thread" )  

class THREADCLIENTTRIG(QtCore.QThread):
    '''
    Second thread for trigger
    '''
    newShotnumber = Signal(int)  # QtCore.Signal(int) # signal to send 
    
    def __init__(self,parent=None):
        super(THREADCLIENTTRIG, self).__init__(parent)
        self.nbshoot = 0
        self.parent = parent 
        self.emitConnected = False
        print('run trigger server client')
        self.clientSocket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.serverHost = '10.0.1.57'
        self.serverPort = 5009
        self.clientSocket.connect((self.serverHost, self.serverPort))
        self.ClientIsConnected = True
        print('client connected to server', self.serverHost)
        

    def run(self):
        #  quand on lance le scan on regarde le nombre de tir trigger
        cmd = 'numberShoot?'
        self.clientSocket.send(cmd.encode())
            # print('connected...')
        try:
            receiv = self.clientSocket.recv(64500)
            self.nbshoot = int(receiv.decode())
            nbshot_temp = self.nbshoot
        except:
                nbshot_temp = -1
                print('error connection')
                self.ClientIsConnected = False

        while self.ClientIsConnected is True:
            cmd = 'numberShoot?'
            self.clientSocket.send(cmd.encode())
            # print('connected...')
            try:
                receiv = self.clientSocket.recv(64500)
                nbshot_temp = int(receiv.decode())
                #print(nbshot_temp)
            except:
                nbshot_temp = -1
                print('error connection')
                self.ClientIsConnected = False
            if self.nbshoot != nbshot_temp:
                self.nbshoot = nbshot_temp
                if self.emitConnected is True:
                    self.newShotnumber.emit(self.nbshoot)
                # print('emit trig')
            time.sleep(0.02)
     
    def stopClientThread(self):
        print('close connection to trig')
        self.ClientIsConnected = False
        self.clientSocket.close()


if __name__=='__main__':
    appli = QApplication(sys.argv)
    s = THREADCLIENTTRIG()
    s.start()
    appli.exec()