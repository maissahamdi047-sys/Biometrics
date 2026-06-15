# 🔐 Recon

Recon complet de reconnaissance faciale avec chiffrement AES-256, tatouage numérique et notifications email.

## ✨ Fonctionnalités

### 🎯 Reconnaissance Faciale
- **Algorithme LBPH** (Local Binary Patterns Histograms)
- **Détection optimisée** pour faible lumière (CLAHE, boost luminosité/contraste)
- **Seuil de confiance ajustable**
- **Entraînement automatique** du modèle

### 🔒 Sécurité
- **Chiffrement AES-256** de la base de données et des images
- **Tatouage numérique LSB** des logs d'accès
- **Hash SHA-256** pour l'intégrité des données
- **Conformité RGPD** (droit à l'oubli)

### 📧 Notifications
- **Alertes email automatiques** (SMTP)
- **Notifications configurables** (autorisé, non autorisé, imposteur)
- **Images jointes** aux alertes

-### 🖥️ Interface Graphique
- **4 onglets** : Enregistrement, Accès, Logs, Administration
- **Surveillance en temps réel**
- **Gestion complète des utilisateurs**
- **Vérification d'intégrité des logs**

## 📋 Prérequis

- **Python 3.8+**
- **Webcam** (pour la capture vidéo)
- **Windows / Linux / macOS**

## 🚀 Installation

### 1. Cloner ou télécharger le projet

```bash
cd systeme_biometrique_v2
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Important**: Utilisez `opencv-contrib-python` (pas `opencv-python`) pour avoir le module LBPH.

### 3. Configuration SMTP (optionnel)

Éditez `config/settings.py` :

```python
SMTP_EMAIL = 'votre_email@gmail.com'
SMTP_PASSWORD = 'votre_mot_de_passe_application'  # Pas votre mot de passe Gmail!
ALERT_EMAIL = 'destinataire@example.com'
```

**Pour Gmail** :
1. Activez la 2FA sur votre compte
2. Créez un mot de passe d'application : https://myaccount.google.com → Sécurité → Mots de passe des applications
3. Utilisez ce mot de passe (16 caractères)

### 4. Lancer l'application

```bash
python main.py
```

## 📖 Guide d'utilisation

### Enregistrer un utilisateur

1. Allez dans l'onglet **📝 Enregistrement**
2. Remplissez le formulaire (nom, code, email)
3. Cliquez sur **Démarrer l'enregistrement**
4. Regardez la caméra pendant la capture (50 images)
5. Le modèle s'entraîne automatiquement

### Contrôler l'accès

1. Allez dans l'onglet **🎥 Contrôle d'Accès**
2. Cliquez sur **Démarrer la surveillance**
3. Le système reconnaît automatiquement les visages
4. Les accès sont enregistrés dans les logs

### Consulter les logs

1. Allez dans l'onglet **📋 Journaux d'Accès**
2. Filtrez par résultat (tous, autorisé, non autorisé, imposteur)
3. Cliquez sur un log pour voir l'image
4. Vérifiez l'intégrité avec le tatouage numérique

### Gérer les utilisateurs

1. Allez dans l'onglet **⚙️ Administration**
2. Sélectionnez un utilisateur
3. Autorisez/Révoquez l'accès
4. Supprimez un utilisateur (RGPD)

### Sécurité

1. **Tatouage** : Vérifiez l'intégrité des logs via les outils d'administration
2. **SMTP** : Testez la connexion email via la configuration
3. **Chiffrement** : Gérez le chiffrement des images via les paramètres

## 🏗️ Architecture

```
systeme_biometrique_v2/
├── core/                    # Logique métier
│   ├── biometrie/          # Capture, détection, reconnaissance
│   ├── database/           # Gestion base de données
│   ├── securite/           # Chiffrement, tatouage, hash
│   └── notifications/      # Alertes email
├── interface/              # Interface graphique Tkinter
├── config/                 # Configuration centralisée
├── data/                   # Données (DB, images, logs)
├── tests/                  # Tests automatisés
├── docs/                   # Documentation
└── main.py                 # Point d'entrée
```

## 🔧 Configuration avancée

### Ajuster le seuil de reconnaissance

Éditez `config/settings.py` :

```python
RECOGNITION_THRESHOLD = 0.35  # Plus bas = plus permissif
```

### Améliorer la détection en faible lumière

```python
CLAHE_CLIP_LIMIT = 4.0       # Égalisation d'histogramme
BRIGHTNESS_BOOST = 1.5       # Augmentation luminosité
CONTRAST_BOOST = 1.3         # Augmentation contraste
```

### Nombre d'images par enregistrement

```python
NUM_IMAGES_ENROLL = 50       # 50 images par défaut
```

## 🔐 Sécurité et RGPD

### Données collectées
- Images de visages (chiffrées AES-256)
- Nom, code utilisateur, email
- Logs d'accès avec horodatage

### Protection
- **Chiffrement** : Toutes les données sensibles sont chiffrées
- **Tatouage** : Les logs sont protégés contre la falsification
- **Local** : Aucune donnée n'est envoyée à des tiers

### Droits RGPD
- **Droit d'accès** : Consultez vos données dans l'onglet Administration
- **Droit de suppression** : Supprimez un utilisateur (irréversible)
- **Droit de modification** : Modifiez les autorisations

### Sauvegarde de la clé de chiffrement

⚠️ **CRITIQUE** : Sauvegardez `data/encryption.key` en lieu sûr!

Sans cette clé, vous ne pourrez plus déchiffrer vos données.

```bash
# Copier la clé sur une clé USB
copy data\encryption.key E:\backup_cle_chiffrement.key

# Ou sur OneDrive
copy data\encryption.key %USERPROFILE%\OneDrive\backup_cle_chiffrement.key
```

## 🧪 Tests

```bash
# Test complet du système
python tests/test_complet.py
```

## ❓ Dépannage

### La caméra ne fonctionne pas
- Vérifiez qu'aucune autre application n'utilise la caméra
- Essayez de changer l'index de la caméra dans le code (0, 1, 2...)

### Le visage n'est pas détecté
- Améliorez l'éclairage
- Regardez directement la caméra
- Ajustez les paramètres de détection dans `config/settings.py`

### La reconnaissance échoue
- Réentraînez le modèle (onglet Administration)
- Ajustez `RECOGNITION_THRESHOLD` (plus bas = plus permissif)
- Vérifiez que vous avez au moins 50 images par utilisateur

### Erreur SMTP
- Vérifiez votre connexion Internet
- Utilisez un mot de passe d'application (pas votre mot de passe Gmail)
- Activez la 2FA sur votre compte Gmail

## 📝 Licence

Ce projet est fourni à des fins éducatives.

## 👤 Auteur

Recon

## 🙏 Remerciements

- OpenCV pour la reconnaissance faciale
- Cryptography pour le chiffrement AES-256
- Tkinter pour l'interface graphique
