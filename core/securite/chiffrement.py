"""
core/securite/chiffrement.py
Chiffrement AES-256 via la bibliothèque cryptography (Fernet = AES-128-CBC + HMAC-SHA256).
Pour un vrai AES-256-GCM, remplacer par hazmat.primitives.
"""
import os
from cryptography.fernet import Fernet


class GestionnaireChiffrement:
    """Gère la clé Fernet et les opérations de chiffrement/déchiffrement."""

    def __init__(self, key_path: str):
        self.key_path = key_path
        self.key      = self._charger_ou_creer_cle()
        self.fernet   = Fernet(self.key)

    # ── Clé ──────────────────────────────────────────────────────────────────
    def _charger_ou_creer_cle(self) -> bytes:
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as f:
                return f.read()
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
        with open(self.key_path, 'wb') as f:
            f.write(key)
        return key

    # ── Données brutes ────────────────────────────────────────────────────────
    def chiffrer(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

    def dechiffrer(self, data: bytes) -> bytes:
        return self.fernet.decrypt(data)

    # ── Fichiers ──────────────────────────────────────────────────────────────
    def chiffrer_fichier(self, chemin: str) -> str:
        """Chiffre un fichier sur disque, supprime l'original, retourne le chemin .enc."""
        with open(chemin, 'rb') as f:
            data = f.read()
        chemin_enc = chemin + '.enc'
        with open(chemin_enc, 'wb') as f:
            f.write(self.chiffrer(data))
        os.remove(chemin)
        return chemin_enc

    def dechiffrer_fichier(self, chemin: str, chemin_sortie: str = None) -> str:
        """Déchiffre un fichier .enc, retourne le chemin du fichier résultat.
        
        Si chemin_sortie est fourni, écrit à cet emplacement (sans supprimer l'original).
        Sinon, écrit à côté du fichier source (en retirant l'extension .enc).
        """
        with open(chemin, 'rb') as f:
            data = f.read()
        if chemin_sortie is None:
            chemin_sortie = chemin.removesuffix('.enc')
        with open(chemin_sortie, 'wb') as f:
            f.write(self.dechiffrer(data))
        return chemin_sortie

    def cle_existante(self) -> bool:
        return os.path.exists(self.key_path)
