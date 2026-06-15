"""
Onglet d'enregistrement de nouveaux utilisateurs
"""
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import os

from config.settings import (
    CAPTURE_IMAGES_COUNT, CAPTURE_DELAY_MS,
    DATA_FACES_DIR, MSG_ENREGISTREMENT_REUSSI
)
from core.database import get_db_users
from core.biometrie import CaptureVideo, DetecteurVisage, EntraineurModele


class OngletEnregistrement:
    """Onglet pour enregistrer de nouveaux utilisateurs"""
    
    def __init__(self, parent, callback_rafraichir=None):
        """
        Initialise l'onglet
        
        Args:
            parent: Widget parent
            callback_rafraichir: Fonction à appeler après enregistrement
        """
        self.parent = parent
        self.callback_rafraichir = callback_rafraichir
        
        self.capture = None
        self.detecteur = DetecteurVisage()
        self.db_users = get_db_users()
        
        self.images_capturees = []
        self.capture_en_cours = False
        
        self.creer_interface()
    
    def creer_interface(self):
        """Crée l'interface de l'onglet"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        titre = ttk.Label(
            main_frame,
            text="📝 Enregistrement d'un nouvel utilisateur",
            font=('Arial', 14, 'bold')
        )
        titre.pack(pady=10)
        
        # Frame formulaire
        form_frame = ttk.LabelFrame(main_frame, text="Informations utilisateur", padding="10")
        form_frame.pack(fill='x', padx=20, pady=10)
        
        # Nom
        ttk.Label(form_frame, text="Nom complet:").grid(row=0, column=0, sticky='w', pady=5)
        self.entry_nom = ttk.Entry(form_frame, width=40)
        self.entry_nom.grid(row=0, column=1, pady=5, padx=10)
        
        # Code d'accès
        ttk.Label(form_frame, text="Code d'accès:").grid(row=1, column=0, sticky='w', pady=5)
        self.entry_code = ttk.Entry(form_frame, width=40)
        self.entry_code.grid(row=1, column=1, pady=5, padx=10)
        
        # Email
        ttk.Label(form_frame, text="Email (optionnel):").grid(row=2, column=0, sticky='w', pady=5)
        self.entry_email = ttk.Entry(form_frame, width=40)
        self.entry_email.grid(row=2, column=1, pady=5, padx=10)
        
        # Frame vidéo
        video_frame = ttk.LabelFrame(main_frame, text="Capture vidéo", padding="10")
        video_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.label_video = ttk.Label(video_frame)
        self.label_video.pack()
        
        # Barre de progression
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(self.progress_frame, text="Progression:").pack(side='left')
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            length=300,
            mode='determinate',
            maximum=CAPTURE_IMAGES_COUNT
        )
        self.progress_bar.pack(side='left', padx=10)
        
        self.label_progression = ttk.Label(self.progress_frame, text="0/50")
        self.label_progression.pack(side='left')
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.btn_demarrer = ttk.Button(
            btn_frame,
            text="▶️ Démarrer la capture",
            command=self.demarrer_capture
        )
        self.btn_demarrer.pack(side='left', padx=5)
        
        self.btn_annuler = ttk.Button(
            btn_frame,
            text="⏹️ Annuler",
            command=self.annuler_capture,
            state='disabled'
        )
        self.btn_annuler.pack(side='left', padx=5)
    
    def demarrer_capture(self):
        """Démarre la capture d'images"""
        # Valider les champs
        nom = self.entry_nom.get().strip()
        code = self.entry_code.get().strip()
        
        if not nom or not code:
            messagebox.showerror("Erreur", "Veuillez remplir le nom et le code d'accès")
            return
        
        # Vérifier si l'utilisateur existe déjà
        if self.db_users.get_user_by_code(code):
            messagebox.showerror("Erreur", f"Le code '{code}' est déjà utilisé")
            return
        
        # Initialiser la capture
        self.capture = CaptureVideo()
        if not self.capture.ouvrir():
            messagebox.showerror("Erreur", "Impossible d'ouvrir la webcam")
            return
        
        # Réinitialiser
        self.images_capturees = []
        self.capture_en_cours = True
        self.progress_bar['value'] = 0
        self.label_progression.config(text="0/50")
        
        # Désactiver/activer boutons
        self.btn_demarrer.config(state='disabled')
        self.btn_annuler.config(state='normal')
        self.entry_nom.config(state='disabled')
        self.entry_code.config(state='disabled')
        self.entry_email.config(state='disabled')
        
        # Lancer la capture
        self.capturer_frame()
    
    def capturer_frame(self):
        """Capture une frame de la webcam"""
        if not self.capture_en_cours:
            return
        
        frame = self.capture.lire_frame()
        if frame is None:
            self.annuler_capture()
            messagebox.showerror("Erreur", "Erreur de lecture de la webcam")
            return
        
        # Détecter les visages
        visages = self.detecteur.detecter(frame)
        
        # Dessiner les rectangles
        for (x, y, w, h) in visages:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Capturer si un visage est détecté
        if len(visages) == 1 and len(self.images_capturees) < CAPTURE_IMAGES_COUNT:
            x, y, w, h = visages[0]
            visage = frame[y:y+h, x:x+w]
            self.images_capturees.append(visage)
            
            # Mettre à jour la progression
            nb_images = len(self.images_capturees)
            self.progress_bar['value'] = nb_images
            self.label_progression.config(text=f"{nb_images}/{CAPTURE_IMAGES_COUNT}")
            
            # Si terminé
            if nb_images >= CAPTURE_IMAGES_COUNT:
                self.finaliser_enregistrement()
                return
        
        # Afficher la frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        self.label_video.imgtk = imgtk
        self.label_video.configure(image=imgtk)
        
        # Continuer la capture
        self.parent.after(CAPTURE_DELAY_MS, self.capturer_frame)
    
    def annuler_capture(self):
        """Annule la capture en cours"""
        self.capture_en_cours = False
        
        if self.capture:
            self.capture.fermer()
            self.capture = None
        
        # Réactiver les champs
        self.btn_demarrer.config(state='normal')
        self.btn_annuler.config(state='disabled')
        self.entry_nom.config(state='normal')
        self.entry_code.config(state='normal')
        self.entry_email.config(state='normal')
        
        # Effacer la vidéo
        self.label_video.configure(image='')
    
    def finaliser_enregistrement(self):
        """Finalise l'enregistrement de l'utilisateur"""
        self.capture_en_cours = False
        
        nom = self.entry_nom.get().strip()
        code = self.entry_code.get().strip()
        email = self.entry_email.get().strip() or None
        
        try:
            # Créer le dossier utilisateur
            user_id = self.db_users.get_next_user_id()
            user_dir = os.path.join(DATA_FACES_DIR, f"user_{user_id}")
            os.makedirs(user_dir, exist_ok=True)
            
            # Sauvegarder les images
            for i, img in enumerate(self.images_capturees):
                img_path = os.path.join(user_dir, f"{i}.jpg")
                cv2.imwrite(img_path, img)
            
            # Ajouter l'utilisateur à la base de données
            self.db_users.add_user(user_id, nom, code, email)
            
            # Entraîner le modèle
            messagebox.showinfo("Entraînement", "Entraînement du modèle en cours...")
            entraineur = EntraineurModele()
            entraineur.entrainer()
            
            # Succès
            messagebox.showinfo("Succès", MSG_ENREGISTREMENT_REUSSI.format(nom=nom))
            
            # Réinitialiser le formulaire
            self.entry_nom.delete(0, tk.END)
            self.entry_code.delete(0, tk.END)
            self.entry_email.delete(0, tk.END)
            self.progress_bar['value'] = 0
            self.label_progression.config(text="0/50")
            
            # Rafraîchir les autres onglets
            if self.callback_rafraichir:
                self.callback_rafraichir()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement: {e}")
        
        finally:
            self.annuler_capture()
