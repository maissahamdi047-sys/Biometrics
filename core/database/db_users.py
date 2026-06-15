"""
core/database/db_users.py
Fonctions utilitaires pour la gestion des utilisateurs.
Wrappent GestionnaireDB (table 'utilisateurs').
"""
from core.database.db_manager import get_db_manager


def ajouter_utilisateur(nom, user_code, autorise=1, email=None):
    db = get_db_manager()
    try:
        return db.ajouter_utilisateur(nom, user_code, email or '')
    except Exception as e:
        print(f"❌ Erreur ajout utilisateur: {e}")
        return None


def obtenir_tous_utilisateurs():
    db = get_db_manager()
    return db.lister_utilisateurs()


def obtenir_utilisateur_par_code(user_code):
    db = get_db_manager()
    return db.obtenir_utilisateur(user_code)


def obtenir_utilisateur_par_id(user_id):
    db = get_db_manager()
    return db.obtenir_utilisateur_par_id(user_id)


def modifier_autorisation(user_code, autorise):
    db = get_db_manager()
    db.modifier_autorisation(user_code, bool(autorise))
    return True


def supprimer_utilisateur(user_code):
    db = get_db_manager()
    db.supprimer_utilisateur(user_code)
    print(f"✅ Utilisateur supprimé: {user_code}")
    return True


def utilisateur_existe(user_code):
    db = get_db_manager()
    return db.code_existe(user_code)


def obtenir_nombre_utilisateurs():
    db = get_db_manager()
    return len(db.lister_utilisateurs())


def obtenir_utilisateurs_autorises():
    db = get_db_manager()
    return [u for u in db.lister_utilisateurs() if u.get('autorise')]
