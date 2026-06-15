"""
core/biometrie/reconnaissance.py
Reconnaissance faciale via l'algorithme LBPH d'OpenCV.
"""
import cv2
import numpy as np
import os
import pickle
from config.settings import MODEL_DIR, RECOGNITION_THRESHOLD


class GestionnaireReconnaissance:

    def __init__(self, model_dir: str, threshold: float = 0.40):
        self.model_dir    = model_dir
        self.threshold    = threshold
        self.model_path   = os.path.join(model_dir, 'face_model.yml')
        self.labels_path  = os.path.join(model_dir, 'labels.pkl')
        self.labels_map   = {}

        os.makedirs(model_dir, exist_ok=True)
        self.recognizer   = cv2.face.LBPHFaceRecognizer_create()

        if self.modele_entraine():
            self.charger_modele()

    # ── Entraînement ──────────────────────────────────────────────────────────
    def entrainer_modele(self, images_dir: str) -> int:
        """
        Lit toutes les images dans images_dir/<user_id>/*.jpg,
        entraîne le modèle LBPH et le sauvegarde.
        Retourne le nombre d'utilisateurs entraînés.
        """
        faces, labels = [], []

        if not os.path.exists(images_dir):
            raise FileNotFoundError(f"Dossier introuvable : {images_dir}")

        for folder in os.listdir(images_dir):
            folder_path = os.path.join(images_dir, folder)
            if not os.path.isdir(folder_path):
                continue
            try:
                uid = int(folder)
            except ValueError:
                continue

            for fname in os.listdir(folder_path):
                if not fname.lower().endswith(('.jpg', '.png')):
                    continue
                img = cv2.imread(os.path.join(folder_path, fname), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    faces.append(cv2.resize(img, (200, 200)))
                    labels.append(uid)

        if not faces:
            raise ValueError("Aucune image trouvée. Enregistrez d'abord des utilisateurs.")

        self.recognizer.train(faces, np.array(labels))
        self.recognizer.save(self.model_path)

        self.labels_map = {uid: uid for uid in set(labels)}
        with open(self.labels_path, 'wb') as f:
            pickle.dump(self.labels_map, f)

        return len(set(labels))

    # ── Chargement ────────────────────────────────────────────────────────────
    def charger_modele(self):
        if os.path.exists(self.model_path):
            self.recognizer.read(self.model_path)
        if os.path.exists(self.labels_path):
            with open(self.labels_path, 'rb') as f:
                self.labels_map = pickle.load(f)

    def modele_entraine(self) -> bool:
        return os.path.exists(self.model_path)

    # ── Reconnaissance ────────────────────────────────────────────────────────
    def reconnaitre(self, face_gray: np.ndarray):
        """
        Tente de reconnaître un visage (image en niveaux de gris).
        Retourne (user_id | None, score_confiance 0-1).
        LBPH : confidence faible = bonne correspondance.
        """
        if not self.modele_entraine():
            return None, 0.0

        face = cv2.resize(face_gray, (200, 200))
        label, raw_confidence = self.recognizer.predict(face)

        # Normalisation : 0 = parfait, 100+ = mauvais → on inverse sur [0,1]
        score = max(0.0, 1.0 - raw_confidence / 100.0)

        if score >= self.threshold:
            return label, score
        return None, score


_reconnaisseur_instance = None


def get_reconnaisseur(model_dir: str = MODEL_DIR, threshold: float = RECOGNITION_THRESHOLD):
    """Retourne une instance unique de GestionnaireReconnaissance."""
    global _reconnaisseur_instance
    if _reconnaisseur_instance is None:
        _reconnaisseur_instance = GestionnaireReconnaissance(model_dir, threshold)
    return _reconnaisseur_instance
