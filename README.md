# 🔐 Recon

Complete facial recognition system with AES-256 encryption, digital watermarking, and email notifications.

## ✨ Features

### 🎯 Facial Recognition
- **LBPH algorithm** (Local Binary Patterns Histograms)
- **Optimized detection** for low-light conditions (CLAHE, brightness/contrast enhancement)
- **Adjustable confidence threshold**
- **Automatic model training**

### 🔒 Security
- **AES-256 encryption** of the database and images
- **LSB digital watermarking** of access logs
- **SHA-256 hashing** for data integrity
- **GDPR compliance** (right to erasure)

### 📧 Notifications
- **Automatic email alerts** (SMTP)
- **Configurable notifications** (authorized, unauthorized, impersonator)
- **Images attached** to alerts

### 🖥️ Graphical Interface
- **4 tabs**: Registration, Access Control, Logs, Administration
- **Real-time monitoring**
- **Complete user management**
- **Log integrity verification**

## 📋 Requirements

- **Python 3.8+**
- **Webcam** (for video capture)
- **Windows / Linux / macOS**

## 🚀 Installation

### 1. Clone or download the project

```bash
cd systeme_biometrique_v2
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

**Important:** Use `opencv-contrib-python` instead of `opencv-python` to enable the LBPH module.

### 3. SMTP Configuration (Optional)

Edit `config/settings.py`:

```python
SMTP_EMAIL = 'your_email@gmail.com'
SMTP_PASSWORD = 'your_app_password'  # Not your Gmail password!
ALERT_EMAIL = 'recipient@example.com'
```

**For Gmail:**

1. Enable 2FA on your Google account.
2. Create an App Password.
3. Use the generated App Password instead of your regular Gmail password.

### 4. Run the application

```bash
python main.py
```

## 📖 User Guide

### Register a User

1. Go to the **📝 Registration** tab.
2. Fill in the form (name, user code, email).
3. Click **Start Registration**.
4. Look at the camera during the capture process (50 images).
5. The model is trained automatically.

### Control Access

1. Go to the **🎥 Access Control** tab.
2. Click **Start Monitoring**.
3. The system automatically recognizes faces.
4. Access attempts are recorded in the logs.

### View Access Logs

1. Go to the **📋 Access Logs** tab.
2. Filter by result (all, authorized, unauthorized, impersonator).
3. Click on a log to view the associated image.
4. Verify log integrity using the digital watermark.

### Manage Users

1. Go to the **⚙️ Administration** tab.
2. Select a user.
3. Grant or revoke access.
4. Delete a user (GDPR).

### Security Management

1. **Watermarking:** Verify log integrity through the administration tools.
2. **SMTP:** Test the email connection through the configuration settings.
3. **Encryption:** Manage image encryption through the security settings.

## 🏗️ Architecture

```text
systeme_biometrique_v2/
├── core/                    # Business logic
│   ├── biometrie/          # Capture, detection, recognition
│   ├── database/           # Database management
│   ├── securite/           # Encryption, watermarking, hashing
│   └── notifications/      # Email alerts
├── interface/              # Tkinter graphical interface
├── config/                 # Centralized configuration
├── data/                   # Data (database, images, logs)
├── tests/                  # Automated tests
├── docs/                   # Documentation
└── main.py                 # Entry point
```

## 🔧 Advanced Configuration

### Adjust the Recognition Threshold

Edit `config/settings.py`:

```python
RECOGNITION_THRESHOLD = 0.35  # Lower = more permissive
```

### Improve Low-Light Detection

```python
CLAHE_CLIP_LIMIT = 4.0       # Histogram equalization
BRIGHTNESS_BOOST = 1.5       # Brightness enhancement
CONTRAST_BOOST = 1.3         # Contrast enhancement
```

### Number of Images per Registration

```python
NUM_IMAGES_ENROLL = 50       # 50 images by default
```

## 🔐 Security and GDPR

### Collected Data

- Facial images (encrypted with AES-256)
- User name, user code, and email
- Access logs with timestamps

### Protection

- **Encryption:** All sensitive data is encrypted.
- **Watermarking:** Logs are protected against tampering.
- **Local processing:** No data is sent to third parties.

### GDPR Rights

- **Right of access:** View your data through the Administration tab.
- **Right to erasure:** Delete a user (irreversible).
- **Right to rectification:** Modify user permissions.

### Encryption Key Backup

⚠️ **CRITICAL:** Store `data/encryption.key` in a secure location.

Without this key, encrypted data can no longer be decrypted.

```bash
# Copy the key to a USB drive
copy data\encryption.key E:\backup_encryption_key.key

# Or to OneDrive
copy data\encryption.key %USERPROFILE%\OneDrive\backup_encryption_key.key
```

## 🧪 Tests

```bash
# Run the complete system test
python tests/test_complet.py
```

## ❓ Troubleshooting

### The Camera Does Not Work

- Make sure no other application is using the camera.
- Try changing the camera index in the code (`0`, `1`, `2`, etc.).

### The Face Is Not Detected

- Improve the lighting.
- Look directly at the camera.
- Adjust the detection parameters in `config/settings.py`.

### Face Recognition Fails

- Retrain the model from the Administration tab.
- Adjust `RECOGNITION_THRESHOLD` (lower = more permissive).
- Make sure you have at least 50 images per user.

### SMTP Error

- Check your Internet connection.
- Use an App Password instead of your regular Gmail password.
- Make sure 2FA is enabled on your Gmail account.

## 📝 License

This project is provided for **educational purposes only**.


