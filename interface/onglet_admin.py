"""
Onglet d'administration des utilisateurs
"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil

from config.settings import DATA_FACES_DIR
from core.database import get_db_users
from core.biometrie import EntraineurModele


class OngletAdmin:
    """Onglet d'administration des utilisateurs"""
    
    def __init__(self, parent, callback_rafraichir=None):
        """
        Initialise l'onglet
        
        Args:
            parent: Widget parent
            callback_rafraichir: Fonction à appeler après modification
        """
        self.parent = parent
        self.callback_rafraichir = callback_rafraichir
        
        self.db_users = get_db_users()
        
        self.creer_interface()
        self.rafraichir_utilisateurs()
    
    def creer_interface(self):
        """Crée l'interface de l'onglet"""
        # Frame principal
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        titre = ttk.Label(
            main_frame,
            text="⚙️ Administration des Utilisateurs",
            font=('Arial', 14, 'bold')
        )
        titre.pack(pady=10)
        
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
            columns=('id', 'nom', 'code', 'email', 'autorise', 'date'),
            show='headings',
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Colonnes
        self.tree.heading('id', text='ID')
        self.tree.heading('nom', text='Nom')
        self.tree.heading('code', text='Code')
        self.tree.heading('email', text='Email')
        self.tree.heading('autorise', text='Autorisé')
        self.tree.heading('date', text='Date création')
        
        self.tree.column('id', width=50)
        self.tree.column('nom', width=200)
        self.tree.column('code', width=100)
        self.tree.column('email', width=200)
        self.tree.column('autorise', width=80)
        self.tree.column('date', width=150)
        
        self.tree.pack(fill='both', expand=True)
        
        # Frame boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="✅ Autoriser l'accès",
            command=self.autoriser_acces
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="❌ Révoquer l'accès",
            command=self.revoquer_acces
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Supprimer (RGPD)",
            command=self.supprimer_utilisateur
        ).pack(side='left', padx=5)
        
        ttk.Button(
            btn_frame,
            text="🔄 Réentraîner le modèle",
            command=self.reentrainer_modele
        ).pack(side='left', padx=5)
        
        # Frame statistiques
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding="10")
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        self.label_stats = ttk.Label(stats_frame, text="", justify='left')
        self.label_stats.pack()
    
    def rafraichir_utilisateurs(self):
        """Rafraîchit la liste des utilisateurs"""
        # Effacer le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Récupérer les utilisateurs
        users = self.db_users.get_all_users()
        
        # Remplir le tableau
        for user in users:
            self.tree.insert('', 'end', values=(
                user['id'],
                user['nom'],
                user['code'],
                user['email'] or 'N/A',
                '✅' if user['autorise'] else '❌',
                user['date_creation'].strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        # Mettre à jour les statistiques
        self.mettre_a_jour_stats()
    
    def mettre_a_jour_stats(self):
        """Met à jour les statistiques"""
        users = self.db_users.get_all_users()
        total = len(users)
        autorises = sum(1 for u in users if u['autorise'])
        revoques = total - autorises
        
        texte = f"Total: {total} utilisateurs | "
        texte += f"✅ Autorisés: {autorises} | "
        texte += f"❌ Révoqués: {revoques}"
        
        self.label_stats.config(text=texte)
    
    def get_selected_user_id(self):
        """Récupère l'ID de l'utilisateur sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
            return None
        
        item = self.tree.item(selection[0])
        return item['values'][0]
    
    def autoriser_acces(self):
        """Autorise l'accès pour un utilisateur"""
        user_id = self.get_selected_user_id()
        if user_id is None:
            return
        
        try:
            self.db_users.set_access(user_id, True)
            messagebox.showinfo("Succès", "Accès autorisé")
            self.rafraichir_utilisateurs()
            
            if self.callback_rafraichir:
                self.callback_rafraichir()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")
    
    def revoquer_acces(self):
        """Révoque l'accès pour un utilisateur"""
        user_id = self.get_selected_user_id()
        if user_id is None:
            return
        
        try:
            self.db_users.set_access(user_id, False)
            messagebox.showinfo("Succès", "Accès révoqué")
            self.rafraichir_utilisateurs()
            
            if self.callback_rafraichir:
                self.callback_rafraichir()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {e}")
    
    def supprimer_utilisateur(self):
        """Supprime un utilisateur (RGPD)"""
        user_id = self.get_selected_user_id()
        if user_id is None:
            return
        
        # Récupérer l'utilisateur
        user = self.db_users.get_user_by_id(user_id)
        if not user:
            return
        
        # Confirmation
        reponse = messagebox.askyesno(
            "⚠️ Confirmation RGPD",
            f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{user['nom']}' ?\n\n"
            "Cette action supprimera:\n"
            "- Les données biométriques\n"
            "- Les images capturées\n"
            "- L'historique d'accès\n\n"
            "Cette action est IRRÉVERSIBLE.",
            icon='warning'
        )
        
        if not reponse:
            return
        
        try:
            # Supprimer le dossier d'images
            user_dir = os.path.join(DATA_FACES_DIR, f"user_{user_id}")
            if os.path.exists(user_dir):
                shutil.rmtree(user_dir)
            
            # Supprimer de la base de données
            self.db_users.delete_user(user_id)
            
            messagebox.showinfo(
                "Succès",
                f"Utilisateur '{user['nom']}' supprimé.\n\n"
                "N'oubliez pas de réentraîner le modèle."
            )
            
            self.rafraichir_utilisateurs()
            
            if self.callback_rafraichir:
                self.callback_rafraichir()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
    
    def reentrainer_modele(self):
        """Réentraîne le modèle de reconnaissance"""
        reponse = messagebox.askyesno(
            "Confirmation",
            "Voulez-vous réentraîner le modèle de reconnaissance ?\n\n"
            "Cela peut prendre quelques secondes."
        )
        
        if not reponse:
            return
        
        try:
            entraineur = EntraineurModele()
            entraineur.entrainer()
            
            messagebox.showinfo("Succès", "Modèle réentraîné avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'entraînement: {e}")
