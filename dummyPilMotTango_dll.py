#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dummy version of PilMotTango.dll 
"""

import time
import threading
import ctypes


class DummyPilMotTango:
    """
    Classe simulant le comportement de PilMotTango.dll
    """
    
    def __init__(self):
        print('🔧 DummyPilMotTango initialisé (mode simulation)')
        
        self.racks = {}
        self.num_equipments = 0
        self.is_started = False
        self.connection_states = {}  # État de connexion de chaque rack
        
        # Mutex pour thread-safety
        self.lock = threading.Lock()
    
    def Start(self, nbeqp, IPs_C):
        """
        Démarre la connexion aux racks
        
        Args:
            nbeqp: ctypes.c_int - nombre d'équipements
            IPs_C: pointeur vers tableau d'IPs
            
        Returns:
            1 si succès, 0 si échec
        """
        try:
            self.num_equipments = nbeqp.value if isinstance(nbeqp, ctypes.c_int) else nbeqp
            
            print(f' Démarrage connexion à {self.num_equipments} rack(s) simulé(s)')
            
            with self.lock:
                # Initialiser les racks
                for rack_num in range(self.num_equipments):
                    self.racks[rack_num] = {}
                    self.connection_states[rack_num] = 3  # 3 = connecté
                    
                    # Initialiser 6 moteurs par rack
                    for motor_num in range(1, 7):
                        self.racks[rack_num][motor_num] = {
                            'position': 0,
                            'status': 0x0080,  # 0x0080 = ok
                            'is_moving': False,
                            'target_position': 0,
                            'velocity': 1000,
                            'move_thread': None
                        }
                
                self.is_started = True
            
            print('Connexion simulée établie')
            return 1
            
        except Exception as e:
            print(f'❌ Erreur Start: {e}')
            return 0
    
    def Stop(self):
        """
        Arrête la connexion aux racks
        
        Returns:
            1 si succès, 0 si échec
        """
        try:
            print('🛑 Arrêt de la connexion simulée')
            
            with self.lock:
                # Arrêter tous les mouvements en cours
                for rack_num in self.racks:
                    for motor_num in self.racks[rack_num]:
                        motor = self.racks[rack_num][motor_num]
                        motor['is_moving'] = False
                        if motor['move_thread'] and motor['move_thread'].is_alive():
                            motor['move_thread'].join(timeout=0.5)
                
                self.is_started = False
                self.racks.clear()
                self.connection_states.clear()
            
            print('✅ Connexion simulée arrêtée')
            return 1
            
        except Exception as e:
            print(f'❌ Erreur Stop: {e}')
            return 0
    
    def rEtatConnexion(self, numRack):
        """
        Lit l'état de connexion d'un rack
        
        Args:
            numRack: ctypes.c_int16 - numéro du rack
            
        Returns:
            int - état de connexion (3 = connecté, autres = déconnecté)
        """
        try:
            rack_num = numRack.value if isinstance(numRack, ctypes.c_int16) else numRack
            
            with self.lock:
                if not self.is_started:
                    return 0
                
                if rack_num in self.connection_states:
                    return self.connection_states[rack_num]
                else:
                    return 0
                    
        except Exception as e:
            print(f'❌ Erreur rEtatConnexion: {e}')
            return 0
    
    def rPositionMot(self, numRack, numMotor):
        """
        Lit la position d'un moteur
        
        Args:
            numRack: int - numéro du rack
            numMotor: int - numéro du moteur
            
        Returns:
            int - position du moteur en steps
        """
        try:
            with self.lock:
                if numRack in self.racks and numMotor in self.racks[numRack]:
                    return self.racks[numRack][numMotor]['position']
                else:
                    return 0
                    
        except Exception as e:
            print(f'❌ Erreur rPositionMot: {e}')
            return 0
    
    def rEtatMoteur(self, numRack, numMotor):
        """
        Lit l'état d'un moteur
        
        Args:
            numRack: int - numéro du rack
            numMotor: int - numéro du moteur
            
        Returns:
            int - status word du moteur (bitmap)
        """
        try:
            with self.lock:
                if numRack in self.racks and numMotor in self.racks[numRack]:
                    motor = self.racks[numRack][numMotor]
                    
                    # Si en mouvement, retourner status mvt (0x0020)
                    if motor['is_moving']:
                        return 0x0020
                    else:
                        return motor['status']
                else:
                    return 0
                    
        except Exception as e:
            print(f'❌ Erreur rEtatMoteur: {e}')
            return 0
    
    def wCdeMot(self, numRack, numMotor, regCde, position, velocity):
        """
        Envoie une commande à un moteur
        
        Args:
            numRack: int - numéro du rack
            numMotor: int - numéro du moteur
            regCde: ctypes.c_uint - registre de commande
            position: ctypes.c_int - position ou déplacement
            velocity: ctypes.c_int - vitesse
            
        Returns:
            int - 0 si succès, autre si erreur
        """
        try:
            # Extraire les valeurs
            # cmd = regCde.value if isinstance(regCde, ctypes.c_uint) else regCde
            cmd = regCde.value if hasattr(regCde, 'value') else regCde
            pos = position.value if isinstance(position, ctypes.c_int) else position
            vel = velocity.value if isinstance(velocity, ctypes.c_int) else velocity
            
            with self.lock:
                if numRack not in self.racks or numMotor not in self.racks[numRack]:
                    return 1  # Erreur: moteur non trouvé
                
                motor = self.racks[numRack][numMotor]
            
            # Traiter les différentes commandes
            print('cmd', cmd, pos, vel)
            if cmd == 2:  # Move absolu
                self._start_move(numRack, numMotor, pos, vel, absolute=True)
                print(f'🎯 Rack{numRack} Mot{numMotor}: Move absolu vers {pos}')
                
            elif cmd == 4 or cmd == 3:  # Move relatif
                self._start_move(numRack, numMotor, pos, vel, absolute=False)
                print(f'➡️  Rack{numRack} Mot{numMotor}: Move relatif de {pos}')
                
            elif cmd == 8:  # Stop
                with self.lock:
                    motor['is_moving'] = False
                    if motor['move_thread'] and motor['move_thread'].is_alive():
                        motor['move_thread'].join(timeout=0.1)
                print(f'⏹️  Rack{numRack} Mot{numMotor}: Stop')
                
            elif cmd == 1024 or cmd == 10:  # Set zero
                with self.lock:
                    motor['position'] = 0
                    motor['target_position'] = 0
                print(f'0️⃣  Rack{numRack} Mot{numMotor}: Set zero')
            
            else:
                print(f'⚠️  Commande inconnue: {cmd}')
            
            return 0  # Succès
            
        except Exception as e:
            print(f'❌ Erreur wCdeMot: {e}')
            return 1
    
    def _start_move(self, numRack, numMotor, position, velocity, absolute=True):
        """
        Démarre un mouvement simulé dans un thread séparé
        """
        with self.lock:
            motor = self.racks[numRack][numMotor]
            
            # Arrêter un éventuel mouvement en cours
            if motor['move_thread'] and motor['move_thread'].is_alive():
                motor['is_moving'] = False
                motor['move_thread'].join(timeout=0.1)
            
            # Calculer la position cible
            if absolute:
                target = position
            else:
                target = motor['position'] + position
            
            motor['target_position'] = target
            motor['velocity'] = velocity
            motor['is_moving'] = True
            
            # Démarrer le thread de mouvement
            motor['move_thread'] = threading.Thread(
                target=self._simulate_move,
                args=(numRack, numMotor),
                daemon=True
            )
            motor['move_thread'].start()
    
    def _simulate_move(self, numRack, numMotor):
        """
        Simule un mouvement progressif du moteur
        """
        try:
            with self.lock:
                motor = self.racks[numRack][numMotor]
                current_pos = motor['position']
                target_pos = motor['target_position']
                velocity = motor['velocity']
            
            # Calculer le nombre de steps et le temps de pause
            distance = abs(target_pos - current_pos)
            if distance == 0:
                with self.lock:
                    motor['is_moving'] = False
                return
            
            direction = 1 if target_pos > current_pos else -1
            
            # Simuler le mouvement progressif
            # Vitesse en steps/s, on met à jour toutes les 50ms
            update_interval = 0.05  # 50ms
            steps_per_update = max(1, int(velocity * update_interval))
            
            while True:
                with self.lock:
                    if not motor['is_moving']:
                        break
                    
                    current_pos = motor['position']
                    remaining = abs(target_pos - current_pos)
                    
                    if remaining == 0:
                        motor['is_moving'] = False
                        break
                    
                    # Avancer de steps_per_update ou du reste
                    step = min(steps_per_update, remaining)
                    motor['position'] += direction * step
                
                time.sleep(update_interval)
            
        except Exception as e:
            print(f'❌ Erreur _simulate_move: {e}')
            with self.lock:
                motor['is_moving'] = False