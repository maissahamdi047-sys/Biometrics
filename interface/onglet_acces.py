"""
Onglet de contrôle d'accès en temps réel
"""
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from datetime import datetime

from config.settings import (
    RECONNAISSANCE_SEUIL_CONFIANCE,
    ALERT_EMAIL_ENABLED, ALERT_EMAIL_RECIPIENT
)
from core.biometrie import CaptureVideo, DetecteurVisage, ReconnaisseurVisage
from core.database import get_db_users, get_db_logs
from core.notifications import EmailAlert


class OngletAcces:
    """Onglet pour le contrôle d'accès en temps réel"""
    
    def __init__(self, parent):
        """
        Initialise l'onglet
        
        Args:
            parent: Widget parent
        """
        self.parent = parent
        
        self.capture = None
        self.detecteur = DetecteurVisage()
        self.reconnaisseur = ReconnaisseurVisage()
        self.db_users = get_db_users()
        self.db_logs = get_db_logs()
        
        self.surveillance_active = False
        self.dernier_acces = {}  # Pour éviter les doublons
        
        self.creer_interface()
    
    def creer_interface(self):
        """Crée l'interface de l'onglet"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        titre = ttk.Label(
            main_frame,
            text="🎥 Contrôle d'Accès en Temps Réel",
            font=('Arial', 14, 'bold')
        )
        titre.pack(pady=10)
        
        # Frame vidéo
        video_frame = ttk.LabelFrame(main_frame, text="Flux vidéo", padding="10")
        video_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.label_video = ttk.Label(video_frame)
        self.label_video.pack()
        
        # Frame informations
        info_frame = ttk.LabelFrame(main_frame, text="Dernière reconnaissance", padding="10")
        info_frame.pack(fill='x', padx=20, pady=10)
        
        self.label_info = ttk.Label(
            info_frame,
            text="En attente...",
            font=('Arial', 12),
            justify='left'
        )
        self.label_info.pack()
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.btn_demarrer = ttk.Button(
            btn_frame,
            text="▶️ Démarrer la surveillance",
            command=self.demarrer_surveillance
        )
        self.btn_demarrer.pack(side='left', padx=5)
        
        self.btn_arreter = ttk.Button(
            btn_frame,
            text="⏹️ Arrêter",
            command=self.arreter_surveillance,
            state='disabled'
        )
        self.btn_arreter.pack(side='left', padx=5)
    
    def demarrer_surveillance(self):
        """Démarre la surveillance"""
        # Charger le modèle
        if not self.reconnaisseur.charger_modele():
            messagebox.showerror(
                "Erreur",
                "Aucun modèle trouvé. Veuillez d'abord enregistrer des utilisateurs."
            )
            return
        
        # Initialiser la capture
        self.capture = CaptureVideo()
        if not self.capture.ouvrir():
            messagebox.showerror("Erreur", "Impossible d'ouvrir la webcam")
            return
        
        self.surveillance_active = True
        self.btn_demarrer.config(state='disabled')
        self.btn_arreter.config(state='normal')
        
        # Lancer la surveillance
        self.surveiller()
    
    def arreter_surveillance(self):
        """Arrête la surveillance"""
        self.surveillance_active = False
        
        if self.capture:
            self.capture.fermer()
            self.capture = None
        
        self.btn_demarrer.config(state='normal')
        self.btn_arreter.config(state='disabled')
        
        # Effacer la vidéo
        self.label_video.configure(image='')
        self.label_info.config(text="Surveillance arrêtée")
    
    def surveiller(self):
        """Boucle de surveillance"""
        if not self.surveillance_active:
            return
        
        frame = self.capture.lire_frame()
        if frame is None:
            self.arreter_surveillance()
            messagebox.showerror("Erreur", "Erreur de lecture de la webcam")
            return
        
        # Détecter les visages
        visages = self.detecteur.detecter(frame)
        
        # Reconnaître chaque visage
        for (x, y, w, h) in visages:
            visage = frame[y:y+h, x:x+w]
            user_id, confiance = self.reconnaisseur.reconnaitre(visage)
            
            if user_id is not None and confiance < RECONNAISSANCE_SEUIL_CONFIANCE:
                # Utilisateur reconnu
                user = self.db_users.get_user_by_id(user_id)
                
                if user:
                    # Vérifier si autorisé
                    if user['autorise']:
                        couleur = (0, 255, 0)  # Vert
                        texte = f"{user['nom']} - ACCES AUTORISE"
                        resultat = "autorise"
                    else:
                        couleur = (0, 165, 255)  # Orange
                        texte = f"{user['nom']} - ACCES REFUSE"
                        resultat = "refuse"
                    
                    # Enregistrer le log (éviter les doublons)
                    maintenant = datetime.now()
                    cle_acces = f"{user_id}_{resultat}"
                    
                    if cle_acces not in self.dernier_acces or \
                       (maintenant - self.dernier_acces[cle_acces]).seconds > 5:
                        
                        self.db_logs.add_log(
                            user_id=user_id,
                            resultat=resultat,
                            confiance=confiance,
                            image=visage
                        )
                        self.dernier_acces[cle_acces] = maintenant
                        
                        # Mettre à jour l'affichage
                        info_text = f"👤 {user['nom']}\n"
                        info_text += f"🔑 Code: {user['code']}\n"
                        info_text += f"📊 Confiance: {confiance:.1f}%\n"
                        info_text += f"✅ Statut: {resultat.upper()}\n"
                        info_text += f"🕐 {maintenant.strftime('%H:%M:%S')}"
                        self.label_info.config(text=info_text)
                else:
                    couleur = (0, 0, 255)  # Rouge
                    texte = "INCONNU"
            else:
                # Inconnu
                couleur = (0, 0, 255)  # Rouge
                texte = "INCONNU"
                
                # Enregistrer le log
                maintenant = datetime.now()
                if 'inconnu' not in self.dernier_acces or \
                   (maintenant - self.dernier_acces['inconnu']).seconds > 5:
                    
                    self.db_logs.add_log(
                        user_id=None,
                        resultat="inconnu",
                        confiance=confiance if user_id is not None else 100.0,
                        image=visage
                    )
                    self.dernier_acces['inconnu'] = maintenant
                    
                    # Envoyer une alerte email
                    if ALERT_EMAIL_ENABLED and ALERT_EMAIL_RECIPIENT:
                        try:
                            email_alert = EmailAlert()
                            email_alert.envoyer_alerte_intrusion(visage)
                        except Exception as e:
                            print(f"Erreur envoi email: {e}")
                    
                    # Mettre à jour l'affichage
                    info_text = "⚠️ PERSONNE INCONNUE DÉTECTÉE\n"
                    info_text += f"📊 Confiance: {confiance if user_id is not None else 100.0:.1f}%\n"
                    info_text += f"🕐 {maintenant.strftime('%H:%M:%S')}"
                    self.label_info.config(text=info_text)
            
            # Dessiner le rectangle et le texte
            cv2.rectangle(frame, (x, y), (x+w, y+h), couleur, 2)
            cv2.putText(frame, texte, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, couleur, 2)
        
        # Afficher la frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        self.label_video.imgtk = imgtk
        self.label_video.configure(image=imgtk)
        
        # Continuer la surveillance
        self.parent.after(100, self.surveiller)
