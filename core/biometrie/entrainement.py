"""
Entraînement du modèle de reconnaissance faciale
"""
import cv2
import os
import numpy as np
from config.settings import FACES_DIR, FACE_SIZE, get_user_faces_dir
from core.securite import get_chiffrement_manager
from core.biometrie.reconnaissance import get_reconnaisseur


def charger_images_utilisateur(user_id):
    """
    Charge toutes les images d'un utilisateur
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        Liste d'images (numpy arrays)
    """
    user_dir = get_user_faces_dir(user_id)
    
    if not os.path.exists(user_dir):
        return []
    
    images = []
    chiffrement = get_chiffrement_manager()
    
    for filename in os.listdir(user_dir):
        filepath = os.path.join(user_dir, filename)
        
        # Si l'image est chiffrée (.enc)
        if filename.endswith('.enc'):
            try:
                # Déchiffrer temporairement
                temp_path = filepath.replace('.enc', '.temp')
                if chiffrement.dechiffrer_fichier(filepath, temp_path):
                    image = cv2.imread(temp_path, cv2.IMREAD_GRAYSCALE)
                    os.remove(temp_path)
                    
                    if image is not None:
                        images.append(image)
            except Exception as e:
                print(f"⚠️  Erreur lors du déchiffrement de {filename}: {e}")
        
        # Si l'image est en clair
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            if image is not None:
                images.append(image)
    
    return images


def entrainer_modele():
    """
    Entraîne le modèle avec toutes les images disponibles
    
    Returns:
        True si succès, False sinon
    """
    print("\n" + "=" * 70)
    print("ENTRAÎNEMENT DU MODÈLE")
    print("=" * 70 + "\n")
    
    faces = []
    labels = []
    
    # Parcourir tous les dossiers d'utilisateurs
    if not os.path.exists(FACES_DIR):
        print("❌ Aucun dossier d'images trouvé")
        return False
    
    user_dirs = [d for d in os.listdir(FACES_DIR) 
                 if os.path.isdir(os.path.join(FACES_DIR, d))]
    
    if not user_dirs:
        print("❌ Aucun utilisateur enregistré")
        return False
    
    print(f"📁 {len(user_dirs)} utilisateur(s) trouvé(s)\n")
    
    for user_dir_name in user_dirs:
        try:
            user_id = int(user_dir_name)
        except ValueError:
            continue
        
        print(f"📸 Chargement des images de l'utilisateur {user_id}...")
        images = charger_images_utilisateur(user_id)
        
        if not images:
            print(f"⚠️  Aucune image trouvée pour l'utilisateur {user_id}")
            continue
        
        print(f"   {len(images)} image(s) chargée(s)")
        
        # Redimensionner et ajouter aux données d'entraînement
        for image in images:
            face_resized = cv2.resize(image, FACE_SIZE)
            faces.append(face_resized)
            labels.append(user_id)
    
    if not faces:
        print("\n❌ Aucune image disponible pour l'entraînement")
        return False
    
    print(f"\n📊 Total: {len(faces)} images pour {len(set(labels))} utilisateur(s)")
    print("\n⏳ Entraînement en cours...")
    
    # Entraîner le modèle
    try:
        reconnaisseur = get_reconnaisseur()
        reconnaisseur.recognizer.train(faces, np.array(labels))
        reconnaisseur.is_trained = True
        
        # Sauvegarder le modèle
        if reconnaisseur.sauvegarder_modele():
            print("\n✅ Entraînement terminé avec succès!")
            print("=" * 70 + "\n")
            return True
        else:
            print("\n❌ Erreur lors de la sauvegarde du modèle")
            return False
    except Exception as e:
        print(f"\n❌ Erreur lors de l'entraînement: {e}")
        import traceback
        traceback.print_exc()
        return False


def reentrainer_modele():
    """
    Réentraîne le modèle (alias pour entrainer_modele)
    
    Returns:
        True si succès, False sinon
    """
    return entrainer_modele()


def entrainement_incrementiel(user_id):
    """
    Entraînement incrémentiel pour un nouvel utilisateur
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        True si succès, False sinon
    """
    print(f"\n⏳ Entraînement incrémentiel pour l'utilisateur {user_id}...")
    
    # Pour LBPH, on doit réentraîner complètement
    # (pas d'entraînement incrémentiel natif)
    return entrainer_modele()


class EntraineurModele:
    """Wrapper de compatibilité pour l'interface graphique."""

    def __init__(self, images_dir: str = FACES_DIR):
        self.images_dir = images_dir

    def entrainer(self):
        return entrainer_modele()

    def reentrainer(self):
        return reentrainer_modele()
