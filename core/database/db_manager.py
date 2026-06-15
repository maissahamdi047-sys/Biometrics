"""
core/database/db_manager.py
Adaptateur – réutilise GestionnaireDB comme backend unique.
"""
from config.settings import DB_PATH
from core.database.gestionnaire import GestionnaireDB

# Instance globale
_db_manager = None


def get_db_manager() -> GestionnaireDB:
    """Retourne l'instance unique du gestionnaire de base de données."""
    global _db_manager
    if _db_manager is None:
        _db_manager = GestionnaireDB(DB_PATH)
    return _db_manager


# Classe alias pour rétrocompatibilité
DatabaseManager = GestionnaireDB
