"""
config/settings.py
Configuration centrale - Recon
"""
import os

# ─── Répertoires ──────────────────────────────────────────────────────────────
BASE_DIR          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR          = os.path.join(BASE_DIR, 'data')
IMAGES_DIR        = os.path.join(DATA_DIR, 'images')
LOGS_DIR          = os.path.join(DATA_DIR, 'logs')
MODEL_DIR         = os.path.join(DATA_DIR, 'models')

# ─── Fichiers ──────────────────────────────────────────────────────────────────
DB_PATH              = os.path.join(DATA_DIR, 'biometrie.db')
ENCRYPTION_KEY_PATH  = os.path.join(DATA_DIR, 'encryption.key')

# ─── Reconnaissance faciale ────────────────────────────────────────────────────
RECOGNITION_THRESHOLD = 0.40     # 0.0 – 1.0  (plus bas = plus permissif)
NUM_IMAGES_ENROLL     = 50       # Images capturées par enregistrement

# ─── Amélioration image (faible lumière) ──────────────────────────────────────
CLAHE_CLIP_LIMIT  = 4.0          # Égalisation CLAHE
BRIGHTNESS_BOOST  = 1.5          # Facteur de luminosité
CONTRAST_BOOST    = 1.3          # Facteur de contraste

# ─── Caméra ───────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0                 # 0 = caméra par défaut

# Backwards-compatible aliases used by the UI
CAPTURE_IMAGES_COUNT = NUM_IMAGES_ENROLL
CAPTURE_DELAY_MS = 120
DATA_FACES_DIR = IMAGES_DIR

# Augmentation during enrollment: number of synthetic variants per captured image
AUGMENTATIONS_PER_IMAGE = 3

# Messages
MSG_ENREGISTREMENT_REUSSI = "Utilisateur {nom} enregistré avec succès."

# ─── SMTP / Notifications ──────────────────────────────────────────────────────
SMTP_HOST     = 'smtp.gmail.com'
SMTP_PORT     = 587
SMTP_EMAIL    = 'maissahamdi047@gmail.com'       
SMTP_PASSWORD = 'pjtk oiul sshv gmbh'
ALERT_EMAIL   = 'maissahamdi72@gmail.com'    
SMTP_ENABLED  = True                       

# Aliases rétro-compatibles (anciens modules / tests)
SMTP_SERVER           = SMTP_HOST
ALERT_EMAIL_ENABLED   = SMTP_ENABLED
ALERT_EMAIL_RECIPIENT = ALERT_EMAIL
RECONNAISSANCE_SEUIL_CONFIANCE = RECOGNITION_THRESHOLD * 100  # en %

SEND_ALERT_ON_AUTHORIZED   = False
SEND_ALERT_ON_UNAUTHORIZED = True
SEND_ALERT_ON_IMPOSTOR     = True


def is_smtp_configured():
    """Vérifie que les paramètres SMTP sont renseignés et activés."""
    return bool(
        SMTP_ENABLED and SMTP_HOST and SMTP_EMAIL and SMTP_PASSWORD and ALERT_EMAIL
    )

# ─── Détection faciale ─────────────────────────────────────────────────────────
FACE_CASCADE_PATH   = 'haarcascade_frontalface_default.xml'
MIN_FACE_SIZE       = (60, 60)
CLAHE_TILE_GRID_SIZE = (8, 8)
FACE_SIZE           = (200, 200)
FACES_DIR           = os.path.join(DATA_DIR, 'images')


def get_user_faces_dir(user_id):
    return os.path.join(FACES_DIR, str(user_id))
