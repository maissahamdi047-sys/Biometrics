"""
Onglet de consultation des journaux d'accès
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

from core.database import get_db_logs, get_db_users
from core.securite import TatouageNumerique


class OngletLogs:
    """Onglet pour consulter les logs d'accès"""
    
    def __init__(self, parent):
        """
        Initialise l'onglet
        
        Args:
            parent: Widget parent
        """
        self.parent = parent
        
        self.db_logs = get_db_logs()
        self.db_users = get_db_users()
        self.tatouage = TatouageNumerique()
        
        self.creer_interface()
        self.rafraichir_logs()
    
    def creer_interface(self):
        """Crée l'interface de l'onglet"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        titre = ttk.Label(
            main_frame,
            text="📋 Journaux d'Accès",
            font=('Arial', 14, 'bold')
        )
        titre.pack(pady=10)
        
        # Frame filtres
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Label(filter_frame, text="Filtrer par:").pack(side='left', padx=5)
        
        self.filtre_var = tk.StringVar(value="tous")
        ttk.Radiobutton(filter_frame, text="Tous", variable=self.filtre_var, 
                       value="tous", command=self.rafraichir_logs).pack(side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="Autorisés", variable=self.filtre_var,
                       value="autorise", command=self.rafraichir_logs).pack(side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="Refusés", variable=self.filtre_var,
                       value="refuse", command=self.rafraichir_logs).pack(side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="Inconnus", variable=self.filtre_var,
                       value="inconnu", command=self.rafraichir_logs).pack(side='left', padx=5)
        
        ttk.Button(filter_frame, text="🔄 Rafraîchir",
                  command=self.rafraichir_logs).pack(side='right', padx=5)
        
        # Frame tableau
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(table_frame, orient='vertical')
        scroll_y.pack(side='right', fill='y')
        
        scroll_x = ttk.Scrollbar(table_frame, orient='horizontal')
        scroll_x.pack(side='bottom', fill='x')
        
        # TreeView
        self.tree = ttk.Treeview(
            table_frame,
            columns=('id', 'date', 'heure', 'utilisateur', 'resultat', 'confiance'),
            show='headings',
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Colonnes
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Date')
        self.tree.heading('heure', text='Heure')
        self.tree.heading('utilisateur', text='Utilisateur')
        self.tree.heading('resultat', text='Résultat')
        self.tree.heading('confiance', text='Confiance')
        
        self.tree.column('id', width=50)
        self.tree.column('date', width=100)
        self.tree.column('heure', width=100)
        self.tree.column('utilisateur', width=200)
        self.tree.column('resultat', width=100)
        self.tree.column('confiance', width=100)
        
        self.tree.pack(fill='both', expand=True)
        
        # Bind double-clic
        self.tree.bind('<Double-1>', self.afficher_details)
        
        # Frame statistiques
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding="10")
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        self.label_stats = ttk.Label(stats_frame, text="", justify='left')
        self.label_stats.pack()
    
    def rafraichir_logs(self):
        """Rafraîchit la liste des logs"""
        # Effacer le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Récupérer les logs
        filtre = self.filtre_var.get()
        if filtre == "tous":
            logs = self.db_logs.get_all_logs()
        else:
            logs = self.db_logs.get_logs_by_result(filtre)
        
        # Remplir le tableau
        for log in logs:
            # Récupérer le nom de l'utilisateur
            if log['user_id']:
                user = self.db_users.get_user_by_id(log['user_id'])
                nom = user['nom'] if user else "Utilisateur supprimé"
            else:
                nom = "INCONNU"
            
            # Formater la date
            date_obj = log['timestamp']
            date_str = date_obj.strftime('%Y-%m-%d')
            heure_str = date_obj.strftime('%H:%M:%S')
            
            # Ajouter la ligne
            self.tree.insert('', 'end', values=(
                log['id'],
                date_str,
                heure_str,
                nom,
                log['resultat'].upper(),
                f"{log['confiance']:.1f}%"
            ))
        
        # Mettre à jour les statistiques
        self.mettre_a_jour_stats()
    
    def mettre_a_jour_stats(self):
        """Met à jour les statistiques"""
        stats = self.db_logs.get_statistics()
        
        texte = f"Total: {stats['total']} | "
        texte += f"✅ Autorisés: {stats['autorises']} | "
        texte += f"❌ Refusés: {stats['refuses']} | "
        texte += f"⚠️ Inconnus: {stats['inconnus']}"
        
        self.label_stats.config(text=texte)
    
    def afficher_details(self, event):
        """Affiche les détails d'un log"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # Récupérer l'ID du log
        item = self.tree.item(selection[0])
        log_id = item['values'][0]
        
        # Récupérer le log complet
        log = self.db_logs.get_log_by_id(log_id)
        if not log:
            return
        
        # Créer une fenêtre de détails
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Détails du log #{log_id}")
        details_window.geometry("600x700")
        
        # Frame principal
        main_frame = ttk.Frame(details_window, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Informations
        info_frame = ttk.LabelFrame(main_frame, text="Informations", padding="10")
        info_frame.pack(fill='x', pady=10)
        
        # Récupérer le nom
        if log['user_id']:
            user = self.db_users.get_user_by_id(log['user_id'])
            nom = user['nom'] if user else "Utilisateur supprimé"
        else:
            nom = "INCONNU"
        
        info_text = f"ID: {log['id']}\n"
        info_text += f"Date/Heure: {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        info_text += f"Utilisateur: {nom}\n"
        info_text += f"Résultat: {log['resultat'].upper()}\n"
        info_text += f"Confiance: {log['confiance']:.1f}%"
        
        ttk.Label(info_frame, text=info_text, justify='left').pack()
        
        # Image
        if log['image_path']:
            img_frame = ttk.LabelFrame(main_frame, text="Image capturée", padding="10")
            img_frame.pack(fill='both', expand=True, pady=10)
            
            try:
                # Charger l'image
                img = cv2.imread(log['image_path'])
                if img is not None:
                    # Redimensionner
                    img = cv2.resize(img, (300, 300))
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(img_rgb)
                    img_tk = ImageTk.PhotoImage(img_pil)
                    
                    label_img = ttk.Label(img_frame, image=img_tk)
                    label_img.image = img_tk
                    label_img.pack()
                    
                    # Vérifier le tatouage
                    btn_verif = ttk.Button(
                        img_frame,
                        text="🔍 Vérifier l'intégrité (tatouage)",
                        command=lambda: self.verifier_tatouage(log['image_path'])
                    )
                    btn_verif.pack(pady=10)
            except Exception as e:
                ttk.Label(img_frame, text=f"Erreur: {e}").pack()
        
        # Bouton fermer
        ttk.Button(main_frame, text="Fermer", command=details_window.destroy).pack(pady=10)
    
    def verifier_tatouage(self, image_path):
        """Vérifie l'intégrité du tatouage numérique"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                messagebox.showerror("Erreur", "Impossible de charger l'image")
                return
            
            # Extraire le tatouage
            tatouage_extrait = self.tatouage.extraire(img)
            
            # Vérifier
            if self.tatouage.verifier(tatouage_extrait):
                messagebox.showinfo(
                    "✅ Intégrité vérifiée",
                    "Le tatouage numérique est valide.\nL'image n'a pas été modifiée."
                )
            else:
                messagebox.showwarning(
                    "⚠️ Intégrité compromise",
                    "Le tatouage numérique est invalide.\nL'image a peut-être été modifiée."
                )
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la vérification: {e}")
