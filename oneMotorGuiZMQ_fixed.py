# Voici les modifications à apporter à votre fichier oneMotorGuiZMQ.py

# PROBLÈME 1 : Widget trop grand
# SOLUTION : Réduire les marges et l'espacement, utiliser un QScrollArea

# PROBLÈME 2 : Label position devient énorme
# SOLUTION : Ajouter des contraintes de taille et réduire la police

"""
=============================================================================
MODIFICATIONS À APPORTER DANS LA MÉTHODE setup()
=============================================================================
"""

# 1. RÉDUIRE LES MARGES ET L'ESPACEMENT au début de setup()
def setup(self):
    """Interface modernisée avec QGroupBox style ConfigWidget"""
    
    mainLayout = QVBoxLayout()
    mainLayout.setSpacing(8)  # CHANGÉ de 12 à 8
    mainLayout.setContentsMargins(10, 10, 10, 10)  # CHANGÉ de 15 à 10


# 2. RÉDUIRE LA TAILLE DU TITRE
    titleLabel = QLabel("🎛️ Contrôle Moteur")
    titleLabel.setStyleSheet("font: bold 14pt; color: #4a9eff;")  # CHANGÉ de 16pt à 14pt
    titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
    mainLayout.addWidget(titleLabel)


# 3. CORRIGER LE LABEL POSITION (ligne ~440)
    self.position = QLabel('0.00')
    self.position.setStyleSheet("""
        QLabel {
            font: bold 24pt;  /* CHANGÉ de 36pt à 24pt */
            color: #00ff00;
            background-color: #1e1e1e;
            padding: 10px;  /* CHANGÉ de 15px à 10px */
            border: 2px solid #00ff00;
            border-radius: 8px;
        }
    """)
    self.position.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.position.setMinimumHeight(60)  # CHANGÉ de 80 à 60
    self.position.setMaximumHeight(80)  # AJOUTÉ pour limiter la hauteur


# 4. RÉDUIRE LA TAILLE DES BOUTONS JOG (ligne ~520)
    self.moins = QToolButton()
    self.moins.setStyleSheet(
        f"QToolButton:!pressed{{border-image: url({self.iconMoins});background-color: transparent;}}"
        f"QToolButton:pressed{{image: url({self.iconMoins});background-color: gray;}}"
    )
    self.moins.setMinimumSize(60, 60)  # CHANGÉ de 80 à 60
    self.moins.setAutoRepeat(True)
    self.moins.setToolTip('Déplacer dans le sens négatif')
    
    jogCenterLabel = QLabel('←  Jog  →')
    jogCenterLabel.setStyleSheet("font: bold 11pt; color: #4a9eff;")  # CHANGÉ de 12pt à 11pt
    jogCenterLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    self.plus = QToolButton()
    self.plus.setStyleSheet(
        f"QToolButton:!pressed{{border-image: url({self.iconPlus});background-color: transparent;}}"
        f"QToolButton:pressed{{image: url({self.iconPlus});background-color: gray;}}"
    )
    self.plus.setMinimumSize(60, 60)  # CHANGÉ de 80 à 60
    self.plus.setAutoRepeat(True)
    self.plus.setToolTip('Déplacer dans le sens positif')


# 5. RÉDUIRE LA TAILLE DU BOUTON STOP (ligne ~560)
    self.stopButton = QToolButton()
    self.stopButton.setStyleSheet(
        f"QToolButton:!pressed{{border-image: url({self.iconStop});background-color: transparent;}}"
        f"QToolButton:pressed{{image: url({self.iconStop});background-color: gray;}}"
    )
    self.stopButton.setMinimumSize(60, 60)  # CHANGÉ de 80 à 60
    self.stopButton.setMaximumSize(60, 60)  # CHANGÉ de 80 à 60
    self.stopButton.setToolTip('Arrêt d\'urgence')


# 6. AJOUTER UNE POLITIQUE DE TAILLE à la fin de setup()
    self.setLayout(mainLayout)
    self.jogStep.setFocus()
    self.refShow()
    self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    # Taille de fenêtre
    self.setMinimumWidth(450)  # CHANGÉ de 500 à 450
    self.setMaximumWidth(600)  # AJOUTÉ pour limiter la largeur
    self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)  # AJOUTÉ


# 7. MODIFIER Position() pour garder la même taille (ligne ~770)
    @pyqtSlot(object)
    def Position(self, Posi):
        self.Posi = Posi
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        b = a
        a = a * self.unitChange

        self.position.setText(str(round(a, 2)) + f" {self.unitName}")
        # GARDER LE MÊME STYLE (ne pas changer à chaque update)
        # La police reste à 24pt


"""
=============================================================================
SOLUTION ALTERNATIVE : UTILISER UN QScrollArea
=============================================================================
Si même avec ces modifications le widget est trop grand, enveloppez 
mainLayout dans un QScrollArea :
"""

def setup_with_scroll(self):
    """Version avec scroll si nécessaire"""
    
    # Créer le widget principal
    mainWidget = QWidget()
    mainLayout = QVBoxLayout()
    mainLayout.setSpacing(8)
    mainLayout.setContentsMargins(10, 10, 10, 10)
    
    # ... tout votre code setup() normal ...
    
    mainWidget.setLayout(mainLayout)
    
    # Envelopper dans un QScrollArea
    scrollArea = QScrollArea()
    scrollArea.setWidget(mainWidget)
    scrollArea.setWidgetResizable(True)
    scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    # Layout final
    finalLayout = QVBoxLayout()
    finalLayout.setContentsMargins(0, 0, 0, 0)
    finalLayout.addWidget(scrollArea)
    self.setLayout(finalLayout)
    
    self.setMinimumWidth(450)
    self.setMaximumWidth(600)
    self.setMinimumHeight(600)
    self.setMaximumHeight(800)


"""
=============================================================================
RÉSUMÉ DES CHANGEMENTS
=============================================================================

1. Titre principal : 16pt → 14pt
2. Label position : 36pt → 24pt, padding 15px → 10px, hauteur max 80px
3. Boutons jog : 80x80 → 60x60
4. Bouton stop : 80x80 → 60x60
5. Marges layout : 15 → 10
6. Espacement layout : 12 → 8
7. Largeur min : 500 → 450, largeur max : 600 (nouveau)
8. SizePolicy : Maximum en hauteur (nouveau)

Ces modifications réduiront significativement la taille du widget et 
empêcheront le label position de devenir énorme.
"""
