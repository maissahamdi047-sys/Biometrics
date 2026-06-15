"""
core/database/gestionnaire.py
Gestion de la base de données SQLite (utilisateurs + logs d'accès).
"""
import sqlite3
import os
from datetime import datetime
from core.securite.hash_utils import calculer_hash


class GestionnaireDB:

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._initialiser()

    # ── Initialisation ────────────────────────────────────────────────────────
    def _initialiser(self):
        with sqlite3.connect(self.db_path) as c:
            c.execute('''CREATE TABLE IF NOT EXISTS utilisateurs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nom           TEXT    NOT NULL,
                code          TEXT    UNIQUE NOT NULL,
                email         TEXT    DEFAULT '',
                autorise      INTEGER DEFAULT 1,
                date_creation TEXT,
                hash_donnees  TEXT
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                utilisateur_id INTEGER,
                nom_detecte   TEXT,
                resultat      TEXT,
                confiance     REAL,
                image_path    TEXT    DEFAULT '',
                timestamp     TEXT,
                hash_log      TEXT
            )''')
            c.commit()

    # ── Connexion helper ──────────────────────────────────────────────────────
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Utilisateurs ──────────────────────────────────────────────────────────
    def ajouter_utilisateur(self, nom: str, code: str, email: str = '') -> int:
        date      = datetime.now().isoformat()
        hash_data = calculer_hash(f"{nom}{code}{email}{date}")
        with self._conn() as c:
            cur = c.execute(
                'INSERT INTO utilisateurs (nom, code, email, date_creation, hash_donnees) VALUES (?,?,?,?,?)',
                (nom, code, email, date, hash_data)
            )
            c.commit()
            return cur.lastrowid

    def obtenir_utilisateur(self, code: str):
        with self._conn() as c:
            row = c.execute('SELECT * FROM utilisateurs WHERE code=?', (code,)).fetchone()
            return dict(row) if row else None

    def obtenir_utilisateur_par_id(self, user_id: int):
        with self._conn() as c:
            row = c.execute('SELECT * FROM utilisateurs WHERE id=?', (user_id,)).fetchone()
            return dict(row) if row else None

    def lister_utilisateurs(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM utilisateurs ORDER BY nom').fetchall()]

    def modifier_autorisation(self, code: str, autorise: bool):
        with self._conn() as c:
            c.execute('UPDATE utilisateurs SET autorise=? WHERE code=?', (int(autorise), code))
            c.commit()

    def supprimer_utilisateur(self, code: str):
        with self._conn() as c:
            c.execute('DELETE FROM utilisateurs WHERE code=?', (code,))
            c.commit()

    def code_existe(self, code: str) -> bool:
        with self._conn() as c:
            return c.execute('SELECT 1 FROM utilisateurs WHERE code=?', (code,)).fetchone() is not None

    # ── Logs ──────────────────────────────────────────────────────────────────
    def ajouter_log(self, nom_detecte: str, resultat: str, confiance: float,
                    image_path: str = '', utilisateur_id=None) -> int:
        ts       = datetime.now().isoformat()
        hash_log = calculer_hash(f"{nom_detecte}{resultat}{confiance}{ts}")
        with self._conn() as c:
            cur = c.execute(
                'INSERT INTO logs (utilisateur_id,nom_detecte,resultat,confiance,image_path,timestamp,hash_log) VALUES (?,?,?,?,?,?,?)',
                (utilisateur_id, nom_detecte, resultat, round(confiance, 4), image_path, ts, hash_log)
            )
            c.commit()
            return cur.lastrowid

    def obtenir_logs(self, filtre: str = 'tous'):
        with self._conn() as c:
            if filtre and filtre != 'tous':
                rows = c.execute('SELECT * FROM logs WHERE resultat=? ORDER BY timestamp DESC', (filtre,)).fetchall()
            else:
                rows = c.execute('SELECT * FROM logs ORDER BY timestamp DESC').fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute('SELECT COUNT(*) FROM logs').fetchone()[0]
            autorise = c.execute("SELECT COUNT(*) FROM logs WHERE resultat='autorisé'").fetchone()[0]
            refuse   = c.execute("SELECT COUNT(*) FROM logs WHERE resultat='non autorisé'").fetchone()[0]
            imposteur= c.execute("SELECT COUNT(*) FROM logs WHERE resultat='imposteur'").fetchone()[0]
            users    = c.execute('SELECT COUNT(*) FROM utilisateurs').fetchone()[0]
        return {'total': total, 'autorise': autorise, 'refuse': refuse,
                'imposteur': imposteur, 'utilisateurs': users}
