"""
main.py
Point d'entrée de Recon
"""
import sys
import os
import tkinter as tk

# S'assurer que le dossier racine est dans le path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verifier_dependances():
    manquants = []
    for pkg in ['cv2', 'numpy', 'PIL', 'cryptography']:
        try:
            __import__(pkg)
        except ImportError:
            manquants.append(pkg)
    # Vérifier le module LBPH d'OpenCV
    try:
        import cv2
        cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        manquants.append('opencv-contrib-python  (LBPH manquant — remplacez opencv-python par opencv-contrib-python)')
    return manquants


def creer_dossiers():
    from config import settings
    for d in [settings.DATA_DIR, settings.IMAGES_DIR,
              settings.LOGS_DIR, settings.MODEL_DIR]:
        os.makedirs(d, exist_ok=True)


def main():
    print("=" * 60)
    print("  🔐  Recon  –  Démarrage")
    print("=" * 60)

    # Vérification dépendances
    manquants = verifier_dependances()
    if manquants:
        print("\n❌  Dépendances manquantes :")
        for m in manquants:
            print(f"   • {m}")
        print("\n→  Installez-les avec :  pip install -r requirements.txt\n")
        sys.exit(1)

    creer_dossiers()
    print("✅  Dépendances OK")
    print("✅  Dossiers de données prêts")
    print("   Lancement de l'interface graphique...\n")

    from interface.app import ApplicationBiometrique

    root = tk.Tk()
    app  = ApplicationBiometrique(root)   # noqa: F841
    root.mainloop()


if __name__ == '__main__':
    main()
