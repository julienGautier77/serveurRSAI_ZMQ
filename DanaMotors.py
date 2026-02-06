#!/home/sallejaune/loaenv/bin/python
# -*- coding: utf-8 -*-
"""
DanaMotors.py - Interface DANA avec boutons spéciaux et Focal Spot Monitor
Hérite de MainTrees.py sans le modifier
Avec écran de progression au démarrage
"""

from PyQt6.QtWidgets import (QApplication, QPushButton, QGridLayout, QLabel, 
                              QHBoxLayout, QProgressBar, QDialog, QVBoxLayout,
                              QGraphicsColorizeEffect)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QPropertyAnimation,QSize
from PyQt6.QtGui import QColor,QPixmap
import sys
import time
import pathlib
import os
import qdarkstyle
from PyQt6.QtGui import QIcon

# Import de la classe qui fonctionne
from MainTrees import MAINMOTOR
from oneMotorGui import ONEMOTORGUI

# Import des widgets spéciaux
try:
    from threeMotorGui import THREEMOTORGUI
    from TiltGui import TILTMOTORGUI
except ImportError:
    print("⚠️ Widgets spéciaux non disponibles")
    THREEMOTORGUI = None
    TILTMOTORGUI = None


class ProgressScreen(QDialog):
    """
    Écran de progression pour le chargement de l'interface DANA
    """
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Chargement DANA Motors")
        self.setModal(True)
        self.setFixedSize(500, 250)
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        p = pathlib.Path(__file__)
        self.icon_path = str(p.parent) + os.sep + 'icons' + os.sep 
        layout = QVBoxLayout()
        if os.path.exists(self.icon_path+ 'LOA.png'):
            icon_label = QLabel()
            pixmap = QPixmap(self.icon_path + 'LOA.png')
            icon_label.setPixmap(pixmap.scaled(64, 64, 
                                       Qt.AspectRatioMode.KeepAspectRatio, 
                                       Qt.TransformationMode.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
        
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon_path + 'LOA.png'))
        
        
        # Titre
        title = QLabel("Initialisation DANA Motors Control")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #4a9eff; margin: 10px;")
        layout.addWidget(title)
        
        # Label de statut
        self.statusLabel = QLabel("Démarrage...")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.statusLabel.setStyleSheet("font-size: 11pt; color: green; margin: 5px;")
        layout.addWidget(self.statusLabel)
        
        # Barre de progression
        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: white;
                height: 30px;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progressBar)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #2b2b2b;")
    
    def update_progress(self, value, text):
        """Met à jour la barre de progression"""
        self.progressBar.setValue(value)
        self.statusLabel.setText(text)
        QApplication.processEvents()


class PositionThread(QThread):
    """Thread pour lire la position du moteur Focal Spot"""
    POS = pyqtSignal(object)
    
    def __init__(self, parent, mot):
        super().__init__(parent)
        self.parent = parent
        self.mot = mot
        self.running = True
    
    def ThreadINIT(self):
        """Initialisation du thread"""
        self.running = True
    
    def run(self):
        """Boucle principale du thread"""
        while self.running:
            try:
                pos = self.mot.position()
                etat = self.mot.etatMotor()
                self.POS.emit([pos, etat])
                time.sleep(0.5)  # Mise à jour toutes les 0.5s
            except Exception as e:
                print(f"❌ Erreur lecture position Focal Spot: {e}")
                time.sleep(1)
    
    def stop(self):
        """Arrête le thread"""
        self.running = False


class DANAMOTOR(MAINMOTOR):
    """
    Classe DANA - Hérite de MAINMOTOR
    Ajoute les boutons spéciaux et le monitoring Focal Spot
    """
    
    # Signal pour mettre à jour la barre de progression
    updateBar_signal = pyqtSignal(list)
    
    def __init__(self, parent=None):
        #  Créer et afficher l'écran de progression
        self.progressScreen = ProgressScreen()
        self.progressScreen.show()
        self.pourcent = 0
        p = pathlib.Path(__file__)
        self.icon_path = str(p.parent) + os.sep + 'icons' + os.sep 
        
        self.progressScreen.update_progress(5, "Connexion au serveur ZMQ...")
        QApplication.processEvents()  # IMPORTANT : forcer l'affichage
        
        # Appeler super().__init__ 
        super().__init__(chamber='dana', parent=parent)
        
        # Connecter le signal APRÈS super().__init__
        self.updateBar_signal.connect(self.update_progress_bar)
    
    def update_progress(self, value, text):
        """Met à jour l'écran de progression (appel direct)"""
        if hasattr(self, 'progressScreen') and self.progressScreen:
            self.progressScreen.update_progress(value, text)
            QApplication.processEvents()  # Forcer la mise à jour
    
    @pyqtSlot(list)
    def update_progress_bar(self, data):
        """Slot pour mettre à jour via signal (si nécessaire)"""
        text, value = data
        self.update_progress(value, text)
    
    def aff(self):
        """Surcharge de aff() pour ajouter la progression"""
        # Étape 2 : Récupération des racks
        self.update_progress(10, "Récupération de la liste des racks...")
        
        # Appeler le aff() du parent
        super().aff()
        
        # Étape 3 : Racks récupérés
        self.update_progress(15, f"{len(self.rackNameFilter)} rack(s) DANA trouvé(s)")
    
    def SETUP(self):
        """
        Surcharge SETUPajouter les boutons spéciaux et la progression
        """
        # Étape 4 : Configuration de l'interface
        self.update_progress(20, "Configuration de l'interface...")
        
        # Appeler le SETUP normal de MAINMOTOR
        super().SETUP()
        
        # Étape 5 : Création des boutons spéciaux
        self.update_progress(25, "Création des boutons spéciaux...")
        self.create_dana_special_buttons()
        
        # Étape 6 : Configuration du Focal Spot Monitor
        self.update_progress(85, "Configuration du Focal Spot Monitor...")
        self.create_focal_spot_monitor()
        
        # Étape 7 : Finalisation
        self.update_progress(100, "✅ Interface DANA prête !")
        time.sleep(0.5)
        
        # Fermer l'écran de progression
        if hasattr(self, 'progressScreen') and self.progressScreen:
            self.progressScreen.close()
            self.progressScreen = None
    
    def create_dana_special_buttons(self):
        """Crée et ajoute les boutons spéciaux DANA"""
        
        if not THREEMOTORGUI or not TILTMOTORGUI:
            print("⚠️ Widgets spéciaux non disponibles")
            return
        
        # Récupérer le layout principal
        main_layout = self.layout()
        
        # Créer une grille pour les boutons
        grid_layout = QGridLayout()
        
        # Progression pour chaque bouton
        self.pourcent = 25
        
        # JET (Cible)
        self.pourcent += 5
        self.update_progress(self.pourcent, "Création motors JET...")
        self.jet = THREEMOTORGUI(
            IPVert='10.0.6.30', NoMotorVert=7, 
            IPLat='10.0.6.30', NoMotorLat=13,
            IPFoc='10.0.6.30', NoMotorFoc=12,
            nomWin='DANA JET', nomTilt='JET1', nomFoc='Jet Foc'
        )
        self.jet_But = QPushButton('JET')
        self.jet_But.setIcon(QIcon(self.icon_path + "target.png"))
        self.jet_But.setIconSize(QSize(20, 20))
        self.jet_But.clicked.connect(lambda: self.open_widget(self.jet))
        self.jet_But.setMinimumHeight(40)

        # CAM (Focal Spot)
        self.pourcent += 15
        self.update_progress(self.pourcent, "Création motors CAM...")
        self.camWidget = THREEMOTORGUI(
            IPVert='10.0.6.30', NoMotorVert=5, 
            IPLat='10.0.6.31', NoMotorLat=13,
            IPFoc='10.0.6.30', NoMotorFoc=9,
            nomWin='Focal Spot DANA', nomTilt='CAM FS', nomFoc=''
        )
        self.cam_But = QPushButton('📷 FSpot')
        self.cam_But.clicked.connect(lambda: self.open_widget(self.camWidget))
        self.cam_But.setMinimumHeight(40)

        # P1 TB
        self.pourcent += 5
        self.update_progress(self.pourcent, "Création boutons Turning Box...")
        self.P1TB = TILTMOTORGUI(
            '10.0.6.31', 1, '10.0.6.31', 2,
            nomWin='P1 Turning Box', nomTilt='P1 TB'
        )
        self.P1TB_But = QPushButton('📦 P1 TB')
        self.P1TB_But.clicked.connect(lambda: self.open_widget(self.P1TB))
        self.P1TB_But.setMinimumHeight(40)

        # P2 TB (Désactivé)
        self.P2TB_But = QPushButton('📦 P2 TB')
        self.P2TB_But.setEnabled(False)
        self.P2TB_But.setMinimumHeight(40)

        # P3 TB
        self.pourcent += 5
        self.update_progress(self.pourcent, "Création boutons Mirrors. P3 TB...")
        self.P3TB = TILTMOTORGUI(
            '10.0.6.31', 3, '10.0.6.31', 4,
            nomWin='P3 Turning Box', nomTilt='P3TB'
        )
        self.P3TB_But = QPushButton('📦 P3 TB')
        self.P3TB_But.clicked.connect(lambda: self.open_widget(self.P3TB))
        self.P3TB_But.setMinimumHeight(40)

        # P1 Mirror
        self.pourcent += 5
        self.update_progress(self.pourcent, "Création  Mirrors P1 ...")
        self.P1M = TILTMOTORGUI(
            IPLat="10.0.6.30", NoMotorLat=11,
            IPVert="10.0.6.30", NoMotorVert=3,
            nomWin='P1 Mirror', background=''
        )
        self.P1Mir_But = QPushButton('🪞 P1 Mir')
        self.P1Mir_But.clicked.connect(lambda: self.open_widget(self.P1M))
        self.P1Mir_But.setMinimumHeight(40)

        # P2 Mirror (Désactivé)
        self.P2Mir_But = QPushButton('🪞 P2 Mir')
        self.P2Mir_But.setEnabled(False)
        self.P2Mir_But.setMinimumHeight(40)

        # P3 Mirror
        self.pourcent += 5
        self.update_progress(self.pourcent, "Création  Mirrors P3 ...")
        self.P3M = TILTMOTORGUI(
            '10.0.6.31', 7, '10.0.6.31', 8,
            nomWin='P3 mirror', nomTilt='P3 M'
        )
        self.P3Mir_But = QPushButton('🪞 P3 Mir')
        self.P3Mir_But.clicked.connect(lambda: self.open_widget(self.P3M))
        self.P3Mir_But.setMinimumHeight(40)

        # P1 OAP
        self.pourcent += 1
        self.update_progress(self.pourcent, "Création bouton OAP...")
        self.P1OPA = TILTMOTORGUI(
            IPVert='10.0.6.31', NoMotorVert=9,
            IPLat='10.0.6.31', NoMotorLat=10,
            nomWin='P1 Spherique', nomTilt='P1 Sphe'
        )
        self.P1OAP_But = QPushButton('⚫ P1 OAP')
        self.P1OAP_But.clicked.connect(lambda: self.open_widget(self.P1OPA))
        self.P1OAP_But.setMinimumHeight(40)

        self.cible = THREEMOTORGUI(
            IPVert='10.0.6.30', NoMotorVert=10, 
            IPLat='10.0.6.31', NoMotorLat=5,
            IPFoc='10.0.6.30', NoMotorFoc=1,
            nomWin='Porte Lame', nomTilt='Lame', nomFoc='Foc Lame'
        )
        self.cible_But = QPushButton('Lame')
        self.cible_But.clicked.connect(lambda: self.open_widget(self.cible))
        self.cible_But.setMinimumHeight(40)

        self.periscope = THREEMOTORGUI(
            IPVert='10.0.6.31', NoMotorVert=6, 
            IPLat='10.0.6.31', NoMotorLat=12,
            IPFoc='10.0.6.30', NoMotorFoc=2,
            nomWin='Periscope', nomTilt='Periscope', nomFoc='Foc periscope'
        )
        self.periscope_But = QPushButton('Pscope')
        self.periscope_But.clicked.connect(lambda: self.open_widget(self.periscope))
        self.periscope_But.setMinimumHeight(40)

        # Disposition en grille 3x3
        grid_layout.addWidget(self.P1TB_But, 0, 0)
        grid_layout.addWidget(self.P2TB_But, 0, 1)
        grid_layout.addWidget(self.P3TB_But, 0, 2)
        grid_layout.addWidget(self.P1Mir_But, 1, 0)
        grid_layout.addWidget(self.P2Mir_But, 1, 1)
        grid_layout.addWidget(self.P3Mir_But, 1, 2)
        grid_layout.addWidget(self.P1OAP_But, 2, 0)
        grid_layout.addWidget(self.jet_But, 2, 1)
        grid_layout.addWidget(self.cam_But, 2, 2)
        grid_layout.addWidget(self.cible_But, 3, 0)
        grid_layout.addWidget(self.periscope_But, 3, 1)
        
        # Insérer la grille dans le layout principal
        main_layout.insertLayout(1, grid_layout)
        
        print("✅ Boutons spéciaux DANA ajoutés")
    
    def create_focal_spot_monitor(self):
        """Crée le widget de monitoring du Focal Spot"""
        
        self.update_progress(85, "Initialisation Focal Spot Monitor...")
        
        # Créer le widget moteur Focal Spot (caché)
        self.motFS = ONEMOTORGUI(
            IpAdress="10.0.6.31", 
            NoMotor=14, 
            showRef=False, 
            unit=1, 
            jogValue=100, 
            parent=self
        )
        
        self.update_progress(88, "Lecture des références Focal Spot...")
        
        # Récupérer les positions de référence
        try:
            self.ref0 = self.motFS.refValueStep[0]  # Position IN
            self.ref1 = self.motFS.refValueStep[1]  # Position OUT
            print(f"📍 Références Focal Spot - IN: {self.ref0}, OUT: {self.ref1}")
        except Exception as e:
            print(f"⚠️ Erreur lecture références Focal Spot: {e}")
            self.ref0 = 0
            self.ref1 = 10000
        
        self.update_progress(90, "Création des boutons Focal Spot...")
        
        # Créer le layout horizontal pour le Focal Spot
        hbox_fs = QHBoxLayout()
        
        # Bouton IN (rouge)
        self.butFS_IN = QPushButton('⬇️ IN')
        self.butFS_IN.setMinimumHeight(50)
        self.butFS_IN.setMinimumWidth(100)
        self.butFS_IN.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #333;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.butFS_IN.clicked.connect(self.move_focal_spot_IN)
        
        # Bouton d'affichage de l'état (centre)
        self.butWarning = QPushButton('Focal Spot Mirror : ?')
        self.butWarning.setMinimumHeight(50)
        self.butWarning.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid #333;
                border-radius: 5px;
                background-color: transparent;
            }
        """)
        self.butWarning.clicked.connect(lambda: self.open_widget(self.motFS))
        
        # Bouton OUT (vert)
        self.butFS_OUT = QPushButton('⬆️ OUT')
        self.butFS_OUT.setMinimumHeight(50)
        self.butFS_OUT.setMinimumWidth(100)
        self.butFS_OUT.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                border: 2px solid #333;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4caf50;
            }
            QPushButton:pressed {
                background-color: #2e7d32;
            }
        """)
        self.butFS_OUT.clicked.connect(self.move_focal_spot_OUT)
        
        # Ajouter les boutons au layout horizontal
        hbox_fs.addWidget(self.butFS_IN)
        hbox_fs.addWidget(self.butWarning, stretch=3)
        hbox_fs.addWidget(self.butFS_OUT)
        
        # Animation pour le clignotement (quand IN)
        self.effect = QGraphicsColorizeEffect()
        
        self.butWarning.setGraphicsEffect(self.effect)
    
        self.anim = QPropertyAnimation(self.effect, b"color", self)
        self.anim.setDuration(1000)  # Plus rapide : 500ms
        self.anim.setLoopCount(-1)
        
        # ⭐ Utiliser setKeyValueAt pour un clignotement plus visible
        self.anim.setKeyValueAt(0, QColor("#ff0000"))    # Rouge vif
        self.anim.setKeyValueAt(0.5, QColor("#8b0000"))    # Rouge sombre
        self.anim.setKeyValueAt(1, QColor("#ff0000"))    # Retour rouge vif
        
        # Insérer dans le layout principal
        main_layout = self.layout()
        main_layout.insertLayout(2, hbox_fs)
        
        self.update_progress(95, "Démarrage du monitoring...")
        
        # Démarrer le thread de lecture de position
        try:
            self.thread = PositionThread(self, mot=self.motFS.MOT[0])
            self.thread.POS.connect(self.Position)
            self.thread.ThreadINIT()
            self.thread.start()
            print("✅ Monitoring Focal Spot démarré")
        except Exception as e:
            print(f"❌ Erreur démarrage monitoring Focal Spot: {e}")
    
    def move_focal_spot_IN(self):
        """Déplace le Focal Spot Mirror vers la position IN (ref0)"""
        try:
            print(f"🔴 Déplacement Focal Spot → IN (position {self.ref0})")
            self.motFS.MOT[0].move(int(self.ref0))
            self.butWarning.setText('⏳ Moving to IN...')
        except Exception as e:
            print(f"❌ Erreur déplacement IN: {e}")
    
    def move_focal_spot_OUT(self):
        """Déplace le Focal Spot Mirror vers la position OUT (ref1)"""
        try:
            print(f"🟢 Déplacement Focal Spot → OUT (position {self.ref1})")
            self.motFS.MOT[0].move(int(self.ref1))
            self.butWarning.setText('⏳ Moving to OUT...')
        except Exception as e:
            print(f"❌ Erreur déplacement OUT: {e}")
    
    @pyqtSlot(object)
    def Position(self, Posi):
        """
        Mise à jour de la position du Focal Spot
        Change la couleur selon la position
        """
        try:
            self.Posi = Posi
            Pos = Posi[0]
            self.etat = str(Posi[1])
            
            # Vérifier la position par rapport aux références
            if self.ref0 - 100 < Pos < self.ref0 + 100:
                # Position IN (rouge clignotant)
                self.butWarning.setStyleSheet("""
                    QPushButton {
                        background-color: red;
                        font-weight: bold;
                        font-size: 12pt;
                        border: 2px solid #333;
                        border-radius: 5px;
                        color: white;
                    }
                """)
                self.butWarning.setText('⚠️ Focal Spot Mirror : IN')
                if self.anim.state() == QPropertyAnimation.Stopped:  # Si pas déjà en cours
                    self.anim.start()
                    
            
            elif self.ref1 - 100 < Pos < self.ref1 + 100:
                # Position OUT (vert)
                self.butWarning.setStyleSheet("""
                    QPushButton {
                        background-color: green;
                        font-weight: bold;
                        font-size: 12pt;
                        border: 2px solid #333;
                        border-radius: 5px;
                        color: white;
                    }
                """)
                self.butWarning.setText('✅ Focal Spot Mirror : OUT')
                if self.anim.state()== QPropertyAnimation.Running:
                    self.anim.stop()
                self.effect.setColor(QColor("green"))
                
            
            else:
                # Position intermédiaire
                if self.anim.state() == QPropertyAnimation.Running:
                    self.anim.stop()
                self.butWarning.setStyleSheet("""
                    QPushButton {
                        background-color: orange;
                        font-weight: bold;
                        font-size: 12pt;
                        border: 2px solid #333;
                        border-radius: 5px;
                        color: white;
                    }
                """)
                self.effect.setColor(QColor("orange"))
                self.butWarning.setText(f' ❓ Focal Spot(Pos: {int(Pos)})')
        
        except Exception as e:
            print(f"❌ Erreur mise à jour position: {e}")
    
    def closeEvent(self, event):
        """Fermeture propre avec arrêt du thread"""
        print("🔒 Fermeture de DANAMOTOR...")
        
        # Fermer l'écran de progression s'il est encore ouvert
        if hasattr(self, 'progressScreen') and self.progressScreen:
            self.progressScreen.close()
        
        # Arrêter le thread de monitoring Focal Spot
        if hasattr(self, 'thread'):
            self.thread.stop()
            self.thread.wait(2000)
        
        # Appeler le closeEvent du parent
        super().closeEvent(event)


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    
    # Créer l'interface DANA avec écran de progression
    s = DANAMOTOR()
    s.show()
    
    sys.exit(appli.exec())