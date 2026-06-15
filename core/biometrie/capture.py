"""
core/biometrie/capture.py
Capture vidéo et extraction de visages pour l'enregistrement et la surveillance.
"""
import cv2
import numpy as np
import os


class GestionnaireCapture:

    def __init__(self, camera_index: int = 0,
                 clahe_clip: float = 4.0,
                 brightness: float = 1.5,
                 contrast: float   = 1.3):
        self.camera_index = camera_index
        self.clahe_clip   = clahe_clip
        self.brightness   = brightness
        self.contrast     = contrast
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    # ── Prétraitement image ───────────────────────────────────────────────────
    def ameliorer_image(self, frame: np.ndarray) -> np.ndarray:
        """Convertit en niveaux de gris, applique CLAHE + ajustement luminosité/contraste."""
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=(8, 8))
        gray  = clahe.apply(gray)
        gray  = cv2.convertScaleAbs(gray, alpha=self.contrast, beta=int(self.brightness * 10))
        return gray

    # ── Détection ─────────────────────────────────────────────────────────────
    def detecter_visages(self, frame: np.ndarray):
        """Retourne (faces: tuple, gray: np.ndarray)."""
        gray  = self.ameliorer_image(frame)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )
        return faces, gray

    # ── Capture vidéo ─────────────────────────────────────────────────────────
    def _ouvrir_capture(self, index: int):
        """Ouvre la caméra en essayant plusieurs backends compatibles Windows."""
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            return cap
        cap.release()

        for backend_name in ('CAP_DSHOW', 'CAP_MSMF', 'CAP_VFW'):
            backend = getattr(cv2, backend_name, None)
            if backend is None:
                continue
            cap = cv2.VideoCapture(index, backend)
            if cap.isOpened():
                return cap
            cap.release()

        return None

    def capturer_visages_enregistrement(self, user_id: int, images_dir: str,
                                        num_images: int = 50,
                                        callback=None) -> list:
        """
        Capture `num_images` images de visage pour l'entraînement.
        callback(count, total, frame_bgr) est appelé à chaque frame.
        Retourne la liste des chemins d'images sauvegardées.
        """
        cap = self._ouvrir_capture(self.camera_index)
        if cap is None:
            raise RuntimeError("Impossible d'ouvrir la caméra. Vérifiez CAMERA_INDEX et que la webcam n'est pas utilisée par une autre application.")

        user_dir = os.path.join(images_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        saved, count = [], 0

        while count < num_images:
            ret, frame = cap.read()
            if not ret:
                break

            faces, gray = self.detecter_visages(frame)
            display     = frame.copy()

            for (x, y, w, h) in faces:
                cv2.rectangle(display, (x, y), (x+w, y+h), (0, 220, 0), 2)
                cv2.putText(display, f'{count}/{num_images}',
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 0), 2)

                face_img = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                path     = os.path.join(user_dir, f'face_{count:03d}.jpg')
                cv2.imwrite(path, face_img)
                saved.append(path)
                count += 1
                break   # un seul visage par frame

            if callback:
                callback(count, num_images, display)

        cap.release()
        return saved

    # ── Frame unique (surveillance) ───────────────────────────────────────────
    def lire_frame(self, cap: cv2.VideoCapture):
        """Lit et retourne (ret, frame) d'une capture déjà ouverte."""
        return cap.read()

    def ouvrir_camera(self) -> cv2.VideoCapture:
        cap = self._ouvrir_capture(self.camera_index)
        if cap is None:
            raise RuntimeError("Impossible d'ouvrir la caméra.")
        return cap


class CaptureVideo(GestionnaireCapture):
    """Wrapper simple pour l'interface graphique Tkinter."""

    def __init__(self, camera_index: int = 0,
                 clahe_clip: float = 4.0,
                 brightness: float = 1.5,
                 contrast: float = 1.3):
        super().__init__(camera_index, clahe_clip, brightness, contrast)
        self.cap = None

    def ouvrir(self) -> bool:
        self.cap = cv2.VideoCapture(self.camera_index)
        return bool(self.cap.isOpened())

    def lire_frame(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def fermer(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
