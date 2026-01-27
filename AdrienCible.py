from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget,QMessageBox
from PyQt6.QtWidgets import QVBoxLayout,QHBoxLayout,QPushButton,QGridLayout,QTreeWidget,QTreeWidgetItem
from PyQt6.QtWidgets import QLabel,QSizePolicy,QTreeWidgetItemIterator,QToolButton,QDoubleSpinBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import qdarkstyle,sys
import ast
import socket as _socket
import time
import os
import pathlib
from oneMotorGuiServerRSAI import ONEMOTORGUI
import moteurRSAISERVER
from PyQt6 import QtCore
import pyqtgraph as pg  # pyqtgraph biblio permettent l'affichage


class WINDOWRANGE(QWidget):
    """Samll widget to set axis range
    """
    def __init__(self):
        super().__init__()
        self.isWinOpen = False
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        self.setWindowTitle('Graphic Range')
        self.setup()
        
    def setup(self):
        # hRangeBox=QHBoxLayout()
        hRangeGrid = QGridLayout()
        
        self.labelXmin = QLabel('Xmin:')
        self.xMinBox = QDoubleSpinBox(self)
        self.xMinBox.setMinimum(-100000)
        self.xMinBox.setMaximum(100000)
        hRangeGrid.addWidget(self.labelXmin, 0, 0)
        hRangeGrid.addWidget(self.xMinBox, 0, 1)
        self.labelXmax = QLabel('Xmax:')
        self.xMaxBox = QDoubleSpinBox(self)
        self.xMaxBox.setMaximum(100000)
        self.xMaxBox.setMinimum(-100000)
        hRangeGrid.addWidget(self.labelXmax, 1, 0)
        hRangeGrid.addWidget(self.xMaxBox, 1, 1)
        
        self.labelYmin = QLabel('Ymin:')
        self.yMinBox = QDoubleSpinBox(self)
        self.yMinBox.setMinimum(-10000000)
        self.yMinBox.setMaximum(10000000)
        hRangeGrid.addWidget(self.labelYmin, 2, 0)
        hRangeGrid.addWidget(self.yMinBox, 2, 1)
        self.labelYmax = QLabel('Ymax:')
        self.yMaxBox = QDoubleSpinBox(self)
        self.yMaxBox.setMaximum(10000000)
        self.yMaxBox.setMinimum(-10000000)
        hRangeGrid.addWidget(self.labelYmax, 3, 0)
        hRangeGrid.addWidget(self.yMaxBox, 3, 1)
        self.applyButton = QPushButton('Apply')
        self.ResetButton = QPushButton('Auto')
        hRangeGrid.addWidget(self.applyButton, 4, 0)
        hRangeGrid.addWidget(self.ResetButton, 4, 1)
        self.setLayout(hRangeGrid)
        
    def closeEvent(self, event):
        """ when closing the window
        """
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept()

class WidgetCible(QWidget):
    """  widget tree with IP adress and motor
 
    """
    def __init__(self,IPVert,MotVert,IPLat,MotLat,titre='',name='MAIN',parent=None):

        super(WidgetCible, self).__init__(parent)
        self.isWinOpen = False
        self.parent = parent
        self.IPVert = IPVert
        self.MotVert = MotVert
        self.IPLat = IPLat
        self.MotLat = MotLat 
        self.titre = titre
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon + 'LOA.png'))
        fileconf = "confCible.ini"
        self.name = name
        self.conf = QtCore.QSettings(fileconf,QtCore.QSettings.Format.IniFormat)
        self.VertWidget = ONEMOTORGUI(IpAdress = self.IPVert, NoMotor = self.MotVert)
        self.LatWidget = ONEMOTORGUI(IpAdress = self.IPLat, NoMotor = self.MotLat)
        self.MotLat = moteurRSAISERVER.MOTORRSAI( self.IPVert, self.MotLat)
        self.MotVert = moteurRSAISERVER.MOTORRSAI(self.IPLat,  self.MotVert)
        self.unitChangeLat = float((1/self.MotLat.getStepValue()))
        self.unitChangeVert = float((1/self.MotVert.getStepValue()))
        
        self.posX = 0
        self.posY = 0
        self.Xshoot = []
        self.Yshoot = []

        self.jogValueLat = self.conf.value(self.name+'/stepLat')
        self.jogValueVert = self.conf.value(self.name+'/stepVert')

        self.setup()

    def setup(self):

        self.setWindowTitle(self.titre)
        size = 20
        vbox1 = QVBoxLayout()
        self.widgetRange = WINDOWRANGE()
        self.widgetRange.applyButton.clicked.connect(self.setRangeOn)
        self.widgetRange.ResetButton.clicked.connect(self.setRangeReset)

        self.winImage = pg.GraphicsLayoutWidget()
        self.winPLOT = self.winImage.addPlot()
        self.winPLOT.setLabel('left', 'Position Vertical (um)')
        self.winPLOT.setLabel('bottom', 'Position Lateral (um)')

        self.posiAct = self.winPLOT.plot(clear=True, symbol='o', symbolPen=None, symbolBrush='g',pen =None)
        
        self.positionShot = self.winPLOT.plot(clear=False, symbol='+', symbolPen=None, symbolBrush='r',pen = None )
        vbox1.addWidget(self.winImage)
        
        grid_layout = QGridLayout()
        self.posLat = QPushButton('Lateral:')
        self.posLat.setStyleSheet("font: 12pt")
        self.posLat.setMaximumHeight(30)
        self.position_Lat = QLabel('12345667')
        self.position_Lat.setStyleSheet('font: bold 18pt;color:white')
        self.position_Lat.setMaximumHeight(30)
        
        self.moinsLat = QToolButton()
        self.moinsLat.setText('-')
        self.moinsLat.setMinimumWidth(size)
        self.moinsLat.setMaximumWidth(size)
        self.moinsLat.setMinimumHeight(size)
        self.moinsLat.setMaximumHeight(size)
        self.moinsLat.clicked.connect(self.mMoveLat)
        
        self.moinsLatShoot = QToolButton()
        self.moinsLatShoot.setText('-')
        self.moinsLatShoot.setMinimumWidth(size)
        self.moinsLatShoot.setMaximumWidth(size)
        self.moinsLatShoot.setMinimumHeight(size)
        self.moinsLatShoot.setMaximumHeight(size)
        self.moinsLatShoot.setStyleSheet("background-color: red")

        self.moinsLatShoot.clicked.connect(self.mMoveLatShoot)
        
        self.jogStepLat = QDoubleSpinBox()
        self.jogStepLat.setMaximum(10000)
        self.jogStepLat.setMinimumWidth(size*4)
        self.jogStepLat.setMaximumWidth(size*4)
        self.jogStepLat.setMinimumHeight(size)
        self.jogStepLat.setMaximumHeight(size)
        self.jogStepLat.setValue(float(self.conf.value(self.name+'/stepLat') ))
        
        self.plusLat = QToolButton()
        self.plusLat.setText('+')
        self.plusLat.setMinimumWidth(size)
        self.plusLat.setMaximumWidth(size)
        self.plusLat.setMinimumHeight(size)
        self.plusLat.setMaximumHeight(size)
        self.plusLat.clicked.connect(self.pMoveLat)

        self.plusLatShoot = QToolButton()
        self.plusLatShoot.setStyleSheet("background-color: red")
        self.plusLatShoot .setText('+')
        self.plusLatShoot .setMinimumWidth(size)
        self.plusLatShoot .setMaximumWidth(size)
        self.plusLatShoot .setMinimumHeight(size)
        self.plusLatShoot .setMaximumHeight(size)
        self.plusLatShoot .clicked.connect(self.pMoveLatShot)

        self.posVert = QPushButton('Vertical:')
        self.posVert.setStyleSheet("font: 12pt")
        self.posVert.setMaximumHeight(30)
        self.position_Vert = QLabel('1234556')
        self.position_Vert.setStyleSheet('font: bold 18pt;color:white')
        self.position_Vert.setMaximumHeight(30)
        
        self.moinsVert = QToolButton()
        self.moinsVert.setText('-')
        self.moinsVert.setMinimumWidth(size)
        self.moinsVert.setMaximumWidth(size)
        self.moinsVert.setMinimumHeight(size)
        self.moinsVert.setMaximumHeight(size)
        self.moinsVert.clicked.connect(self.mMoveVert)

        self.moinsVertShoot = QToolButton()
        self.moinsVertShoot.setText('-')
        self.moinsVertShoot.setMinimumWidth(size)
        self.moinsVertShoot.setMaximumWidth(size)
        self.moinsVertShoot.setMinimumHeight(size)
        self.moinsVertShoot.setMaximumHeight(size)
        self.moinsVertShoot.setStyleSheet("background-color: red")
        self.moinsVertShoot.clicked.connect(self.mMoveVertShoot)

        self.jogStepVert = QDoubleSpinBox()
        self.jogStepVert.setMaximum(10000)
        self.jogStepVert.setMinimumWidth(size*4)
        self.jogStepVert.setMaximumWidth(size*4)
        self.jogStepVert.setMinimumHeight(size)
        self.jogStepVert.setMaximumHeight(size)
        self.jogStepVert.setValue(float(self.conf.value(self.name+'/stepVert')))
        
        self.plusVert = QToolButton()
        self.plusVert.setText('+')
        self.plusVert.setMinimumWidth(size)
        self.plusVert.setMaximumWidth(size)
        self.plusVert.setMinimumHeight(size)
        self.plusVert.setMaximumHeight(size)
        self.plusVert.clicked.connect(self.pMoveVert)

        self.plusVertShoot = QToolButton()
        self.plusVertShoot.setText('+')
        self.plusVertShoot.setMinimumWidth(size)
        self.plusVertShoot.setMaximumWidth(size)
        self.plusVertShoot.setMinimumHeight(size)
        self.plusVertShoot.setMaximumHeight(size)
        self.plusVertShoot.setStyleSheet("background-color: red")
        self.plusVertShoot.clicked.connect(self.pMoveVertShoot)

        self.resetBut = QToolButton()
        self.resetBut.setText('Reset')
        self.resetBut.clicked.connect(self.reset)

        self.valMaxLabel = QLabel('Vert Max :')
        self.valMax = QDoubleSpinBox()
        self.valMax.setMinimum(-10000000)
        self.valMax.setMaximum(10000000)
        self.valMax.setValue(float(self.conf.value(self.name+'/vertMax')))
        self.valMinLabel = QLabel('Vert Min :')
        self.valMin = QDoubleSpinBox()
        self.valMin.setMinimum(-10000000)
        self.valMin.setMaximum(10000000)
        self.valMin.setValue(float(self.conf.value(self.name+'/vertMin')))
        grid_layout.addWidget(self.posLat,0,0)
        grid_layout.addWidget(self.moinsLatShoot,0,1)
        grid_layout.addWidget(self.moinsLat,0,2)
        grid_layout.addWidget(self.jogStepLat,0,3)
    
        grid_layout.addWidget(self.plusLat,0,4)
        grid_layout.addWidget(self.plusLatShoot,0,5)
        grid_layout.addWidget(self.position_Lat,0,6)

        grid_layout.addWidget(self.posVert,1,0)
        grid_layout.addWidget(self.moinsVertShoot,1,1)
        grid_layout.addWidget(self.moinsVert,1,2)
        grid_layout.addWidget(self.jogStepVert,1,3)
        grid_layout.addWidget(self.plusVert,1,4)
        grid_layout.addWidget(self.plusVertShoot,1,5)
        grid_layout.addWidget(self.position_Vert,1,6)
        grid_layout.addWidget(self.resetBut,0,7)

        self.buttRange = QPushButton('Range')
        grid_layout.addWidget(self.buttRange,1,7)
        grid_layout.addWidget(self.valMaxLabel,0,8)
        grid_layout.addWidget(self.valMax,0,9)
        grid_layout.addWidget(self.valMinLabel,1,8)
        grid_layout.addWidget(self.valMin,1,9)
        vbox1.addLayout(grid_layout )
        #vbox1.addLayout(hVertBox)

        self.setLayout(vbox1)
        self.posVert.clicked.connect(lambda:self.open_widget(self.VertWidget))
        self.posLat.clicked.connect(lambda:self.open_widget(self.LatWidget))
        self.threadLat = PositionThread(self,mot=self.MotLat) # thread for displaying position Lat
        self.threadLat.POS.connect(self.PositionLat)
        self.threadVert = PositionThread(self,mot=self.MotVert) # thread for displaying  position Vert
        self.threadVert.POS.connect(self.PositionVert)
        self.buttRange.clicked.connect(lambda:self.open_widget(self.widgetRange))

        self.jogStepLat.editingFinished.connect(self.changeValue)
        self.jogStepVert.editingFinished.connect(self.changeValue)
        self.valMax.editingFinished.connect(self.changeValue)
        self.valMin.editingFinished.connect(self.changeValue)

    def setRangeOn(self):

        self.xZoomMin = (self.widgetRange.xMinBox.value())
        self.yZoomMin = (self.widgetRange.yMinBox.value())
        self.xZoomMax = (self.widgetRange.xMaxBox.value())
        self.yZoomMax = (self.widgetRange.yMaxBox.value())
        self.winPLOT.setXRange(self.xZoomMin, self.xZoomMax)
        self.winPLOT.setYRange(self.yZoomMin, self.yZoomMax)
        
    def setRangeReset(self):

        self.winPLOT.autoRange(True)

    def pMoveLatShot(self):
        
        self.Xshoot.append(self.posX)
        self.Yshoot.append(self.posY)

        self.positionShot.setData(x=self.Xshoot,y=self.Yshoot) 
        
        a = float(self.jogStepLat.value())
        a = float(a/self.unitChangeLat)
        self.MotLat.rmove(a)

    def mMoveLatShoot(self):
        
        self.Xshoot.append(self.posX)
        self.Yshoot.append(self.posY)
        self.positionShot.setData(x=self.Xshoot,y=self.Yshoot) 
        b = float(self.jogStepLat.value())
        a = float(b/self.unitChangeLat)
        
        self.MotLat.rmove(-a)


    def pMoveVertShoot(self):
        
        self.Xshoot.append(self.posX)
        self.Yshoot.append(self.posY)
        self.positionShot.setData(x=self.Xshoot,y=self.Yshoot) 
        b = float(self.jogStepVert.value())
        a = float(b/self.unitChangeVert)
        if  self.posY + b >= self.valMax.value():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(" Wrong position!")
            msg.setInformativeText("Are you sur to move ? ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel)
            ret = msg.exec()
            if ret == QMessageBox.StandardButton.Ok :
                self.MotVert.rmove(a)
            else :
                print ('on bouge pas ')
                pass
        else:
            self.MotVert.rmove(a)

    def mMoveVertShoot(self):
        
        self.Xshoot.append(self.posX)
        self.Yshoot.append(self.posY)
        self.positionShot.setData(x=self.Xshoot,y=self.Yshoot) 
        b = float(self.jogStepVert.value())
        a = float(b/self.unitChangeVert)
        if   self.posY -b< self.valMin.value():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(" Wrong position!")
            msg.setInformativeText("Are you sur to move ? ")
            msg.setWindowTitle("Warning ...")
            msg.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok|QMessageBox.StandardButton.Cancel)
            ret = msg.exec()
            if ret ==QMessageBox.StandardButton.Ok :
                self.MotVert.rmove(-a)
            else : 
                pass
        else : 
            self.MotVert.rmove(-a)

    def reset(self):
        self.Xshoot = []
        self.Yshoot = [] 
        self.positionShot.setData(x=self.Xshoot,y=self.Yshoot) 

    def PositionLat(self,Posi):
        ''' 
        Position Lat  display with the second thread
        '''
        Pos = Posi[0]
        a = float(Pos)
        b = a # value in step
        a = a * self.unitChangeLat

        self.position_Lat.setText(str(round(a,2))+' um ') 
        
        self.posX = a
        self.posiAct.setData(x=[self.posX],y=[self.posY])

    def PositionVert(self,Posi):
        ''' 
        Position Vert display with the second thread
        '''
        Pos = Posi[0]
        a = float(Pos)
        b = a # value in step
        a = a*self.unitChangeLat

        self.position_Vert.setText(str(round(a,2)) + ' um ')
              
        self.posY = a

    def pMoveLat(self):
        '''
        action jog + foc 
        '''
        a = float(self.jogStepLat.value())
        a = float(a/self.unitChangeLat)
        self.MotLat.rmove(a)
            
    def mMoveLat(self): 
        '''
        action jog - foc
        '''
        a = float(self.jogStepLat.value())
        a = float(a/self.unitChangeLat)
        self.MotLat.rmove(-a)

    def pMoveVert(self):
        '''
        action jog + foc 
        '''
        a = float(self.jogStepVert.value())
        a = float(a/self.unitChangeVert)
        self.MotVert.rmove(a)
            
    def mMoveVert(self): 
        '''
        action jog - foc
        '''
        a = float(self.jogStepVert.value())
        a = float(a/self.unitChangeVert)
        self.MotVert.rmove(-a) 
            
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

    def startThread2(self):
        self.threadLat.ThreadINIT()
        self.threadLat.start()
        time.sleep(0.07)
        self.threadVert.ThreadINIT()
        self.threadVert.start()

    def changeValue(self):
        self.conf.setValue(self.name+'/stepLat',self.jogStepLat.value())
        self.conf.setValue(self.name+'/stepVert',self.jogStepVert.value())
        self.conf.setValue(self.name+'/vertMax',self.valMax.value())
        self.conf.setValue(self.name+'/vertMin',self.valMin.value())

    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.threadLat.stopThread()
        self.threadVert.stopThread()
        self.isWinOpen = False
        time.sleep(0.1)
        event.accept() 

class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    import time 
    POS = QtCore.pyqtSignal(object) # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self,parent=None,mot=''):
        
        super(PositionThread,self).__init__(parent)
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
                #try :
                etat = self.MOT.etatMotor()
                #time.sleep(0.1)
                self.POS.emit([Posi,etat])
                #time.sleep(0.1)
                #except: 
                    #print('error emit etat')  
                    
    def ThreadINIT(self):
        self.stop = False   
                        
    def stopThread(self):
        self.stop = True
        #self.terminate()

if __name__ =='__main__':
    appli = QApplication(sys.argv)
    mot = WidgetCible()
    mot.show()
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    mot.startThread2()
    appli.exec_()