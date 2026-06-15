"""
Script de test pour vérifier que tous les modules s'importent correctement
"""
print("🧪 Test des imports...")

try:
    print("  ✓ Config...")
    from config.settings import *
    
    print("  ✓ Database...")
    from core.database import get_db_manager, get_db_users, get_db_logs
    
    print("  ✓ Biométrie...")
    from core.biometrie import CaptureVideo, DetecteurVisage, ReconnaisseurVisage, EntraineurModele
    
    print("  ✓ Sécurité...")
    from core.securite import TatouageNumerique, ChiffrementAES
    
    print("  ✓ Notifications...")
    from core.notifications import EmailAlert
    
    print("  ✓ Interface...")
    from interface.app import ApplicationPrincipale
    from interface.onglet_enregistrement import OngletEnregistrement
    from interface.onglet_acces import OngletAcces
    from interface.onglet_logs import OngletLogs
    from interface.onglet_admin import OngletAdmin
    # Onglet Sécurité supprimé
    
    print("\n✅ Tous les imports ont réussi!")
    print("\n📋 Résumé:")
    print("  - Configuration: OK")
    print("  - Base de données: OK")
    print("  - Biométrie: OK")
    print("  - Sécurité: OK")
    print("  - Notifications: OK")
    print("  - Interface graphique: OK")
    print("\n🚀 L'application est prête à être lancée avec: python main.py")
    
except ImportError as e:
    print(f"\n❌ Erreur d'import: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
