"""
Envoi d'alertes email via SMTP
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import os
from config.settings import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_EMAIL,
    SMTP_PASSWORD,
    ALERT_EMAIL,
    SEND_ALERT_ON_UNAUTHORIZED,
    SEND_ALERT_ON_IMPOSTOR,
    SEND_ALERT_ON_AUTHORIZED,
    is_smtp_configured
)


class GestionnaireEmail:
    """Gestionnaire d'envoi d'emails"""
    
    def __init__(self):
        """Initialise le gestionnaire"""
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_email = SMTP_EMAIL
        self.smtp_password = SMTP_PASSWORD
        self.alert_email = ALERT_EMAIL
    
    def tester_connexion(self):
        """
        Teste la connexion SMTP
        
        Returns:
            True si succès, False sinon
        """
        if not is_smtp_configured():
            print("⚠️  SMTP non configuré")
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
            print("✅ Connexion SMTP réussie")
            return True
        except Exception as e:
            print(f"❌ Échec de la connexion SMTP: {e}")
            return False
    
    def envoyer_alerte(self, user_code, resultat, score, image_path=None):
        """
        Envoie une alerte email
        
        Args:
            user_code: Code utilisateur
            resultat: AUTORISE, NON_AUTORISE ou IMPOSTEUR
            score: Score de confiance
            image_path: Chemin de l'image (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        # Vérifier si on doit envoyer une alerte
        if resultat == "AUTORISE" and not SEND_ALERT_ON_AUTHORIZED:
            return True
        if resultat == "NON_AUTORISE" and not SEND_ALERT_ON_UNAUTHORIZED:
            return True
        if resultat == "IMPOSTEUR" and not SEND_ALERT_ON_IMPOSTOR:
            return True
        
        if not is_smtp_configured():
            print("⚠️  SMTP non configuré - Alerte non envoyée")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_email
            msg['To'] = self.alert_email
            msg['Subject'] = self._obtenir_sujet(resultat)
            
            # Corps du message
            body = self._creer_corps_email(user_code, resultat, score)
            msg.attach(MIMEText(body, 'html'))
            
            # Attacher l'image si fournie
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', 
                                 filename=os.path.basename(image_path))
                    msg.attach(img)
            
            # Envoyer
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Alerte email envoyée à {self.alert_email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email: {e}")
            return False
    
    def envoyer_alerte_intrusion(self, image):
        """
        Envoie une alerte d'intrusion avec image
        
        Args:
            image: Image numpy array (BGR)
            
        Returns:
            True si succès, False sinon
        """
        import cv2
        import tempfile
        
        # Sauvegarder temporairement l'image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            tmp_path = tmp.name
        
        try:
            result = self.envoyer_alerte("INCONNU", "IMPOSTEUR", 100.0, tmp_path)
            return result
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _obtenir_sujet(self, resultat):
        """Génère le sujet de l'email"""
        if resultat == "IMPOSTEUR":
            return "🚨 ALERTE SÉCURITÉ - Tentative d'intrusion détectée"
        elif resultat == "NON_AUTORISE":
            return "⚠️ Alerte - Accès non autorisé"
        else:
            return "ℹ️ Notification d'accès autorisé"
    
    def _creer_corps_email(self, user_code, resultat, score):
        """Crée le corps HTML de l'email"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Couleur selon le résultat
        if resultat == "IMPOSTEUR":
            color = "#d32f2f"
            icon = "🚨"
            message = "Une tentative d'intrusion par un individu inconnu a été détectée."
        elif resultat == "NON_AUTORISE":
            color = "#f57c00"
            icon = "⚠️"
            message = f"L'utilisateur {user_code} a tenté d'accéder au système mais n'est pas autorisé."
        else:
            color = "#388e3c"
            icon = "✅"
            message = f"L'utilisateur {user_code} a accédé au système avec succès."
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f5f5f5; }}
                .info-box {{ background-color: white; border-left: 4px solid {color}; padding: 15px; margin: 10px 0; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; display: inline-block; width: 150px; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{icon} Recon</h1>
            </div>
            <div class="content">
                <p>{message}</p>
                
                <div class="info-box">
                    <h3>Détails de l'événement</h3>
                    <div class="info-row">
                        <span class="label">Horodatage:</span>
                        <span>{timestamp}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Utilisateur:</span>
                        <span>{user_code}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Résultat:</span>
                        <span style="color: {color}; font-weight: bold;">{resultat}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Score:</span>
                        <span>{score:.4f}</span>
                    </div>
                </div>
                
                <p><strong>Actions recommandées:</strong></p>
                <ul>
                    <li>Vérifier l'image capturée en pièce jointe</li>
                    <li>Consulter le journal d'accès complet</li>
                    <li>Prendre les mesures de sécurité appropriées si nécessaire</li>
                </ul>
            </div>
            <div class="footer">
                <p>Cet email a été généré automatiquement par Recon.</p>
                <p>Ne pas répondre à cet email.</p>
            </div>
        </body>
        </html>
        """
        
        return html


# Instance globale
_gestionnaire_email = None

def get_gestionnaire_email():
    """Retourne l'instance unique du gestionnaire d'email"""
    global _gestionnaire_email
    if _gestionnaire_email is None:
        _gestionnaire_email = GestionnaireEmail()
    return _gestionnaire_email
