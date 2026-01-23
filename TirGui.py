#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 14:32:54 2018
Control tir laview 
@author: loa
"""
from PyQt6 import QtCore
import qdarkstyle
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget,QMessageBox,QVBoxLayout,QPushButton,QHBoxLayout
from PyQt6.QtGui import QShortcut
import time
import sys
import tirSalleJaune as tirSJ
# import moteurRSAI as RSAI  # Moteur RSAI
PY = sys.version_info[0]
if PY<3:
    print('wrong version of python : Python 3.X must be used')
#%%
class TIRGUI(QWidget) :
    """
    User interface for shooting class : 
    
    """
    
    def __init__(self,parent=None):
        
        super(TIRGUI, self).__init__(parent)
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setup()
        self.actionButton()
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
     
    def setup(self):
        
        vbox1=QVBoxLayout()
        self.tirButton=QPushButton('LASER SHOT')
        self.tirButton.setMinimumHeight(150)
        self.tirButton.setStyleSheet("background-color: red ;border-radius:75px")
        vbox1.addWidget(self.tirButton)
        hbox=QHBoxLayout()
        self.connectButton=QPushButton('Connect')
        hbox.addWidget(self.connectButton)
        self.disconnectButton=QPushButton('Disconnect')
        hbox.addWidget(self.disconnectButton)
        vbox1.addLayout(hbox)
        
        self.setLayout(vbox1)
        
    
    
    def actionButton(self):
        self.setWindowTitle('Tir Salle Jaune')# affichage nom du moteur sur la barre de la fenetre
        self.connectButton.clicked.connect(self.Connect)
        self.disconnectButton.clicked.connect(self.Disconnect)
        self.tirButton.clicked.connect(self.TirAct)
        self.shortcut = QShortcut(QKeySequence("Ctrl+t"), self)
        self.shortcut.activated.connect(self.TirAct)
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.fini()
        time.sleep(0.1)
        event.accept()   
        
    def fini(self): # a la fermeture de la fenetre on arrete le thread secondaire
        self.isWinOpen=False
        time.sleep(0.1)     
        
        
    def Connect(self):
        a=tirSJ.tirConnect()
        print (a)
        if a==1:
            self.connectButton.setStyleSheet("background-color: green")
            self.connectButton.setText("Connected")
            self.TirConnected=1
            
        else :
            self.connectButton.setStyleSheet("background-color: gray")
            self.connectButton.setText("Connection")
            self.TirConnected=0

    def Disconnect(self):
        tirSJ.disconnect()
        self.connectButton.setStyleSheet("background-color: gray")
        self.connectButton.setText("Connection")
        self.TirConnected=0
    
    def TirAct(self):
        
        a=tirSJ.Tir()
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        print( "tir :",a)
        if a==0 or a=="":
            self.TirConnected=0
            print( "Probleme tir")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Not connected !")
            msg.setInformativeText("Please connect !!")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.exec_()




   
if __name__ =='__main__':
    appli=QApplication(sys.argv)
    tt=TIRGUI()
    tt.show()
    appli.exec_()