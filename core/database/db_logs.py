"""
core/database/db_logs.py
Fonctions utilitaires pour la gestion des logs d'accès.
Wrappent GestionnaireDB (table 'logs').
"""
from core.database.db_manager import get_db_manager


def ajouter_log(timestamp, user_code, resultat, score, image_path, hash_sha256):
    """Ajoute un log. Adapte la signature vers GestionnaireDB.ajouter_log()."""
    db = get_db_manager()
    # Normalisation des résultats vers le schéma interne
    map_resultat = {
        'AUTORISE': 'autorisé',
        'NON_AUTORISE': 'non autorisé',
        'IMPOSTEUR': 'imposteur',
    }
    resultat_interne = map_resultat.get(resultat, resultat)
    return db.ajouter_log(
        nom_detecte=user_code,
        resultat=resultat_interne,
        confiance=score,
        image_path=image_path or '',
        utilisateur_id=None
    )


def obtenir_tous_logs():
    db = get_db_manager()
    return db.obtenir_logs('tous')


def obtenir_logs_par_resultat(resultat):
    map_resultat = {
        'AUTORISE': 'autorisé',
        'NON_AUTORISE': 'non autorisé',
        'IMPOSTEUR': 'imposteur',
    }
    resultat_interne = map_resultat.get(resultat, resultat)
    db = get_db_manager()
    return db.obtenir_logs(resultat_interne)


def obtenir_logs_par_utilisateur(user_code):
    db = get_db_manager()
    with db._conn() as c:
        rows = c.execute(
            'SELECT * FROM logs WHERE nom_detecte=? ORDER BY timestamp DESC',
            (user_code,)
        ).fetchall()
        return [dict(r) for r in rows]


def obtenir_log_par_id(log_id):
    db = get_db_manager()
    with db._conn() as c:
        row = c.execute('SELECT * FROM logs WHERE id=?', (log_id,)).fetchone()
        return dict(row) if row else None


def supprimer_logs_utilisateur(user_code):
    db = get_db_manager()
    with db._conn() as c:
        c.execute('DELETE FROM logs WHERE nom_detecte=?', (user_code,))
        c.commit()
    return True


def obtenir_statistiques_logs():
    db = get_db_manager()
    s = db.stats()
    return {
        'total': s['total'],
        'autorises': s['autorise'],
        'non_autorises': s['refuse'],
        'imposteurs': s['imposteur'],
        'taux_imposteurs': (s['imposteur'] / s['total'] * 100) if s['total'] > 0 else 0.0,
    }


def obtenir_derniers_logs(limite=10):
    db = get_db_manager()
    with db._conn() as c:
        rows = c.execute(
            'SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?', (limite,)
        ).fetchall()
        return [dict(r) for r in rows]
