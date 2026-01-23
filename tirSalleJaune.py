#########################################################################
# 
# LabVIEW TCP Server Client Script
# 
# 
# 
#########################################################################

import socket as _socket
import time, sys 
from PyQt6.QtWidgets import QApplication, QComboBox, QSpinBox
from PyQt6.QtWidgets import QWidget,QGridLayout
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QSizePolicy
import qdarkstyle
import pathlib
import os 
import time 
import select
from PyQt6.QtCore import pyqtSignal
    
rgbcolor_gray = '(0,48,57)'
_serverHost = '10.0.4.50'
_serverPort = 50007
isConnected = 0
_sockobj    = None

TirConnected = 0


# --------------------------------------




def tirConnect():
    #'opens a connection to LabVIEW Server'
    global _sockobj, isConnected
    _sockobj = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)      # create socket
    _sockobj.settimeout(20)
    isConnected = True
    try :
        a = _sockobj.connect((_serverHost, _serverPort))   # connect to LV
        isConnected = True
    except :
        isConnected = False
    return isConnected


def disconnect():
    #'closes the connection to LabVIEW Server'
    global isConnected
    try :
        _sockobj.close()                             # close socket
    except:
        pass
    isConnected = False
    return isConnected


def passCommand(command):
    'passes a command to LabVIEW Server'
    # try :
    _sockobj.send(command)
#    time.sleep(0.5)
    data = _sockobj.recv(65536)
    # except :
        # data = 0
    #execString = "lvdata = " + data
    #exec execString
    return data

def Tir():
    try:
        print('Tir envoyé')
        recu =  passCommand(b"Tir")
        print('Tir recu')
        if recu is not None :
            isConnected = True
        return isConnected 
    except:
        print('issue with Tir')
        return None
    
def stopTir():
    recu = passCommand(b"Stop")

    
def multi_shot(nb_freq,nb_tir):
    """
        0 : 0.1 Hz
        1 : 0.2 Hz
        2 : 0.5 Hz
        3 : 1.0 Hz
    """
    # print(b"Shot %i,%i" % (nb_freq,nb_tir))
    try:
        _sockobj.send(b"Shot %i,%i" % (nb_freq,nb_tir))
        isConnected = True
        print('tir salle program',nb_freq,nb_tir)
    except:
        print('issue with multi_shot passCommand')
        return None
    return isConnected

class SalleJauneConnect(QWidget):

    def __init__(self, parent=None):
        
        super(QWidget, self).__init__(parent)
        self.parent = parent
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' +sepa
        self.isWinOpen = False
        self.setup()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.multi = multiTirThread(parent=self)
        self.isConnected = False 
        self.testConnection = TESTCONNECTION()
        self.testConnection.signalConnection.connect(self.diconnectedSig)

    def setup(self):

        self.setWindowTitle('Salle Jaune Connection')
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))

        self.connectButton = QPushButton('Click to connect')                       
        self.connectButton.clicked.connect(self.connect)
        
        lab_IP = QLabel("Laser Server  :  %s  :  %i " % (_serverHost, _serverPort) )
        lab_IP.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.connectButton)
        #hlayout.addWidget(self.disconnectButton)

        vlayout = QVBoxLayout()  
        vlayout.addWidget(lab_IP)
        vlayout.addLayout(hlayout)

        self.widgetLayout = QWidget()
        self.gridLayout = QGridLayout()
        self.tirButton = QPushButton('One Shot')
        
        self.tirButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tirButton.clicked.connect(self.shoot)
        
        but_multi = QPushButton('Multi Shot')
        but_multi.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        but_multi.clicked.connect(self.multiShoot)
        self.but_freq = QComboBox()
        self.but_freq.addItem('0.1 Hz')
        self.but_freq.addItem('0.2 Hz')
        self.but_freq.addItem('0.5 Hz')
        self.but_freq.addItem('1 Hz')
        self.but_freq.setIconSize(QSize(0, 0))
        self.but_nbtir = QSpinBox()
        self.but_nbtir.setMinimum(1)
        self.but_nbtir.setValue(2)

        but_stop = QPushButton('STOP')
        but_stop.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        but_stop.clicked.connect(self.stop_tir)

        self.gridLayout.addWidget(self.tirButton,0,0,4,2)
        self.gridLayout.addWidget (but_multi,0,2,2,2)
        self.gridLayout.addWidget(self.but_freq,0,4)
        self.gridLayout.addWidget(self.but_nbtir,1,4)
        self.gridLayout.addWidget(but_stop,2,2,2,3)
        
        self.widgetLayout.setLayout(self.gridLayout)
        self.widgetLayout.setEnabled(False)
        vlayout.addWidget(self.widgetLayout)
        self.setLayout(vlayout)
        

    def connect(self):

        if self.isConnected is False:
            a = tirConnect()
            if a == True:
                self.connectButton.setStyleSheet("background-color: rgb(0, 170, 0)")
                self.connectButton.setText("Connected")
                self.isConnected = True
                print('Connected to Labview')
                self.widgetLayout.setEnabled(True)
                self.testConnection.stop = False
                #self.testConnection.start()
            else:
                self.connectButton.setStyleSheet("background-color: %s"%rgbcolor_gray)
                self.connectButton.setText("Click to Connect")
                self.isConnected  = False
                self.widgetLayout.setEnabled(False)
                print('NOT connected to Labview')
                self.testConnection.stopThread()
        else :
            a = disconnect()
            self.connectButton.setStyleSheet("background-color: %s"%rgbcolor_gray)
            self.connectButton.setText("Click to Connect")
            self.isConnected  = False
            self.widgetLayout.setEnabled(False)
            print('NOT connected to Labview')
            self.testConnection.stopThread()
    
    def diconnectedSig(self):
        self.connectButton.setStyleSheet("background-color: %s"%rgbcolor_gray)
        self.connectButton.setText("Click to Connect")
        self.isConnected  = False
        self.widgetLayout.setEnabled(False)
        print('NOT connected to Labview')
        self.testConnection.stopThread()
    
    def shoot(self):
        if isConnected == 1:
            a = Tir()
            print("tir :", a)
            if a == True:
                self.isConnected  = True
            else: 
                a = "probleme tir"
                print("Probleme tir")

    def stop_tir(self):
        print('stop')
        a = stopTir()

    def multiShoot(self):
        """
        0 : 0.1 Hz
        1 : 0.2 Hz
        2 : 0.5 Hz
        3 : 1.0 Hz
    """
        if self.isConnected == True :
            freq = self.but_freq.currentIndex()
            nb_tir = self.but_nbtir.value()
            print('multishot',freq,nb_tir)
            self.multi.start()
            #multi_shot(freq,nb_tir)


class multiTirThread(QtCore.QThread):
    '''
    Second thread  to mutlishoot
    '''

    def __init__(self,parent=None):

        super(multiTirThread,self).__init__(parent)
        self.parent = parent
        self.stop = False
        
    def run(self):
        if self.stop is False:
            self.freq = self.parent.but_freq.currentIndex()
            self.nb_tir = self.parent.but_nbtir.value()
            multi_shot(self.freq,self.nb_tir)
              
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        #self.terminate()

class TESTCONNECTION(QtCore.QThread):
    '''
     thread  to test the connection to laser
    '''
    signalConnection = pyqtSignal(bool)

    def __init__(self,parent=None):

        super(TESTCONNECTION,self).__init__(parent)
        self.parent = parent
        self.stop = False
        self.connected = False

    def run(self):
        while self.stop is False :
            time.sleep(1)
            if self.stop is True:
                break
            else :
                try:
                    #_sockobj.send(b'\x00',_socket.MSG_DONTWAIT)
                    rlist, _, _ = select.select([_sockobj],[],[],0)
                    self.connected = not bool(rlist)
                    # print('connection Ok')
                except Exception as e:
                    print (e)
                    self.connected = False
            if self.connected is False :
                print('connection perdue')
                self.signalConnection.emit(self.connected) 

    def stopThread(self): 
        self.stop = True 



if __name__ == "__main__":
    appli = QApplication(sys.argv)
    e = SalleJauneConnect()
    e.show()
    appli.exec()
