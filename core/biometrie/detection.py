"""
Détection de visages avec amélioration d'image pour faible lumière
"""
import cv2
import numpy as np
from config.settings import (
    FACE_CASCADE_PATH,
    MIN_FACE_SIZE,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID_SIZE,
    BRIGHTNESS_BOOST,
    CONTRAST_BOOST
)


class DetecteurVisage:
    """Détecteur de visages avec amélioration d'image"""
    
    def __init__(self):
        """Initialise le détecteur"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + '/' + FACE_CASCADE_PATH
        )
        
        # CLAHE pour égalisation d'histogramme
        self.clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=CLAHE_TILE_GRID_SIZE
        )
    
    def ameliorer_image(self, image):
        """
        Améliore une image pour la détection en faible lumière
        
        Args:
            image: Image à améliorer
            
        Returns:
            Image améliorée
        """
        # Convertir en niveaux de gris si nécessaire
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Augmenter la luminosité et le contraste
        gray = cv2.convertScaleAbs(gray, alpha=CONTRAST_BOOST, beta=int(BRIGHTNESS_BOOST * 30))
        
        # Égalisation d'histogramme adaptative (CLAHE)
        gray = self.clahe.apply(gray)
        
        # Réduction du bruit
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        
        return gray
    
    def detecter_visages(self, image, ameliorer=True):
        """
        Détecte les visages dans une image
        
        Args:
            image: Image à analyser
            ameliorer: Si True, améliore l'image avant détection
            
        Returns:
            Liste de rectangles (x, y, w, h) des visages détectés
        """
        # Améliorer l'image si demandé
        if ameliorer:
            gray = self.ameliorer_image(image)
        else:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
        
        # Détecter les visages
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=MIN_FACE_SIZE,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        return faces
    
    def extraire_visage(self, image, rect, ameliorer=True):
        """
        Extrait un visage d'une image
        
        Args:
            image: Image source
            rect: Rectangle (x, y, w, h) du visage
            ameliorer: Si True, améliore l'image
            
        Returns:
            Image du visage extrait
        """
        x, y, w, h = rect
        
        # Extraire la région du visage
        face = image[y:y+h, x:x+w]
        
        # Améliorer si demandé
        if ameliorer:
            face = self.ameliorer_image(face)
        else:
            if len(face.shape) == 3:
                face = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        
        return face
    
    def dessiner_rectangles(self, image, faces, couleur=(0, 255, 0), epaisseur=2):
        """
        Dessine des rectangles autour des visages détectés
        
        Args:
            image: Image sur laquelle dessiner
            faces: Liste de rectangles (x, y, w, h)
            couleur: Couleur BGR du rectangle
            epaisseur: Épaisseur du trait
            
        Returns:
            Image avec les rectangles dessinés
        """
        image_copy = image.copy()
        
        for (x, y, w, h) in faces:
            cv2.rectangle(image_copy, (x, y), (x+w, y+h), couleur, epaisseur)
        
        return image_copy


# Instance globale
_detecteur = None

def get_detecteur():
    """Retourne l'instance unique du détecteur"""
    global _detecteur
    if _detecteur is None:
        _detecteur = DetecteurVisage()
    return _detecteur
