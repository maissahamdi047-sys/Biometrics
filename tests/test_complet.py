"""
tests/test_complet.py
Tests automatisés – modules sécurité, DB, chiffrement et tatouage.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile, shutil, numpy as np
from PIL import Image

# ── Imports modules ────────────────────────────────────────────────────────────
from core.securite.hash_utils   import calculer_hash, verifier_hash
from core.securite.chiffrement  import GestionnaireChiffrement
from core.securite.tatouage     import GestionnaireTatouage
from core.database.gestionnaire import GestionnaireDB


def test_hash():
    print("  [hash]        ", end='')
    h = calculer_hash("bonjour")
    assert len(h) == 64
    assert verifier_hash("bonjour", h)
    assert not verifier_hash("aurevoir", h)
    print("✅")


def test_chiffrement(tmp_path):
    print("  [chiffrement] ", end='')
    tmp = str(tmp_path)
    key_path = os.path.join(tmp, 'test.key')
    g = GestionnaireChiffrement(key_path)
    data = b"donnee secrete"
    assert g.dechiffrer(g.chiffrer(data)) == data
    # Fichier
    f_path = os.path.join(tmp, 'secret.txt')
    with open(f_path, 'wb') as f:
        f.write(data)
    enc = g.chiffrer_fichier(f_path)
    assert enc.endswith('.enc')
    dec = g.dechiffrer_fichier(enc)
    with open(dec, 'rb') as f:
        assert f.read() == data
    print("✅")


def test_tatouage(tmp_path):
    print("  [tatouage]    ", end='')
    tmp = str(tmp_path)
    g = GestionnaireTatouage()
    # Créer une image test 100x100
    arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img_path = os.path.join(tmp, 'test.png')
    Image.fromarray(arr).save(img_path)

    message = "utilisateur:42|résultat:autorisé|2024-01-01"
    g.inserer_tatouage(img_path, message)
    valid, extracted = g.verifier_integrite(img_path)
    assert valid, f"Tatouage invalide : {extracted}"
    assert extracted == message
    print("✅")


def test_database(tmp_path):
    print("  [database]    ", end='')
    tmp = str(tmp_path)
    db_path = os.path.join(tmp, 'test.db')
    db = GestionnaireDB(db_path)

    db.ajouter_utilisateur("Alice", "A001", "alice@test.com")
    u = db.obtenir_utilisateur("A001")
    assert u and u['nom'] == "Alice"

    db.modifier_autorisation("A001", False)
    u = db.obtenir_utilisateur("A001")
    assert u['autorise'] == 0

    db.ajouter_log("Alice", "autorisé", 0.87, "", u['id'])
    logs = db.obtenir_logs()
    assert len(logs) >= 1

    stats = db.stats()
    assert stats['utilisateurs'] >= 1

    db.supprimer_utilisateur("A001")
    assert db.obtenir_utilisateur("A001") is None
    print("✅")


def main():
    print("\n🧪  Tests Recon")
    print("─" * 40)
    tmp = tempfile.mkdtemp()
    try:
        test_hash()
        test_chiffrement(tmp)
        test_tatouage(tmp)
        test_database(tmp)
        print("─" * 40)
        print("✅  Tous les tests passent !\n")
    except AssertionError as e:
        print(f"\n❌  Échec : {e}\n")
        sys.exit(1)
    finally:
        shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
