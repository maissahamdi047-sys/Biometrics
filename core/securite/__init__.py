"""
core/securite/__init__.py
Exports des utilitaires de sécurité.
"""
from core.securite.chiffrement import GestionnaireChiffrement
from config import settings

_chiffrement_instance = None

def get_chiffrement_manager():
    """Retourne l'instance unique du gestionnaire de chiffrement."""
    global _chiffrement_instance
    if _chiffrement_instance is None:
        _chiffrement_instance = GestionnaireChiffrement(settings.ENCRYPTION_KEY_PATH)
    return _chiffrement_instance
