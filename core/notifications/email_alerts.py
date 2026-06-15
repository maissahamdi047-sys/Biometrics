"""
core/notifications/email_alerts.py
Alertes email SMTP avec images jointes.
"""
import smtplib
import os
import tempfile
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.image     import MIMEImage

from config.settings import ENCRYPTION_KEY_PATH
from core.securite.chiffrement import GestionnaireChiffrement


class GestionnaireNotifications:

    def __init__(self, smtp_host: str, smtp_port: int,
                 email: str, password: str,
                 alert_email: str, enabled: bool = False):
        self.smtp_host   = smtp_host
        self.smtp_port   = smtp_port
        self.email       = email
        self.password    = password
        self.alert_email = alert_email
        self.enabled     = enabled

    # ── Test de connexion ──────────────────────────────────────────────────────
    def tester_connexion(self):
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as s:
                s.starttls()
                s.login(self.email, self.password)
            return True, "✅ Connexion SMTP réussie"
        except Exception as e:
            return False, f"❌ {e}"

    # ── Envoi générique ────────────────────────────────────────────────────────
    def envoyer_alerte(self, sujet: str, corps_html: str, image_path: str = None):
        if not self.enabled:
            return False, "Notifications désactivées dans settings.py"
        try:
            msg            = MIMEMultipart()
            msg['From']    = self.email
            msg['To']      = self.alert_email
            msg['Subject'] = sujet
            msg.attach(MIMEText(corps_html, 'html'))

            temp_file = None
            if image_path and os.path.exists(image_path):
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ('.jpg', '.jpeg', '.png', '.gif'):
                    with open(image_path, 'rb') as f:
                        img = MIMEImage(f.read(), _subtype=ext.lstrip('.'))
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path))
                    msg.attach(img)
                elif ext == '.enc':
                    try:
                        chiffreur = GestionnaireChiffrement(ENCRYPTION_KEY_PATH)
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            temp_file = tmp.name
                        chiffreur.dechiffrer_fichier(image_path, temp_file)
                        with open(temp_file, 'rb') as f:
                            img = MIMEImage(f.read(), _subtype='png')
                        img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(image_path).replace('.enc', '.png'))
                        msg.attach(img)
                    except Exception as exc:
                        print(f"⚠️  Impossible de déchiffrer l'image {image_path} : {exc}")
                else:
                    print(f"⚠️  Fichier joint ignoré (format non pris en charge) : {image_path}")

            try:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as s:
                    s.starttls()
                    s.login(self.email, self.password)
                    s.send_message(msg)
                return True, "Email envoyé"
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
        except Exception as e:
            print(f"❌ Erreur SMTP : {e}")
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return False, str(e)

    # ── Alertes prédéfinies ───────────────────────────────────────────────────
    def _html_base(self, titre: str, couleur: str, contenu: str) -> str:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""<html><body style="font-family:Arial,sans-serif;">
            <h2 style="color:{couleur};">{titre}</h2>
            {contenu}
            <p><b>Horodatage :</b> {ts}</p>
        </body></html>"""

    def alerte_autorise(self, nom: str, image_path: str = None):
        html = self._html_base(
            "✅ Accès Autorisé", "#28a745",
            f"<p><b>Utilisateur :</b> {nom}</p><p>Accès accordé.</p>"
        )
        return self.envoyer_alerte(f"✅ Accès Autorisé – {nom}", html, image_path)

    def alerte_refuse(self, nom: str, image_path: str = None):
        html = self._html_base(
            "🚫 Accès Refusé", "#dc3545",
            f"<p><b>Utilisateur :</b> {nom}</p><p>Accès révoqué.</p>"
        )
        return self.envoyer_alerte(f"🚫 Accès Refusé – {nom}", html, image_path)

    def alerte_imposteur(self, image_path: str = None):
        html = self._html_base(
            "⚠️ ALERTE – Imposteur Détecté", "#ff6600",
            "<p>Un visage <b>non reconnu</b> a tenté d'accéder au système.</p>"
        )
        return self.envoyer_alerte("⚠️ ALERTE – Imposteur Détecté", html, image_path)
