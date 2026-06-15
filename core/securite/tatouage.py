"""
core/securite/tatouage.py
Tatouage numérique LSB (Least Significant Bit) pour protéger l'intégrité des logs.
"""
import hashlib
import numpy as np
from PIL import Image

_END_MARKER = '###END###'
_SEP        = '|||'


class GestionnaireTatouage:
    """Insère et vérifie un message caché dans les bits de poids faible d'une image."""

    # ── Insertion ─────────────────────────────────────────────────────────────
    def inserer_tatouage(self, image_path: str, message: str) -> bool:
        img       = Image.open(image_path).convert('RGB')
        arr       = np.array(img, dtype=np.uint8)
        flat      = arr.flatten()

        msg_hash   = hashlib.sha256(message.encode()).hexdigest()
        full_msg   = message + _SEP + msg_hash + _END_MARKER
        bits       = ''.join(format(ord(c), '08b') for c in full_msg)

        if len(bits) > len(flat):
            raise ValueError("Message trop long pour l'image sélectionnée.")

        for i, bit in enumerate(bits):
            flat[i] = (flat[i] & 0xFE) | int(bit)

        result = Image.fromarray(flat.reshape(arr.shape))
        result.save(image_path)
        return True

    # ── Extraction ────────────────────────────────────────────────────────────
    def extraire_tatouage(self, image_path: str):
        img  = Image.open(image_path).convert('RGB')
        flat = np.array(img, dtype=np.uint8).flatten()

        chars, buf = [], []
        for i in range(len(flat)):
            buf.append(str(flat[i] & 1))
            if len(buf) == 8:
                chars.append(chr(int(''.join(buf), 2)))
                buf = []
            full = ''.join(chars)
            if _END_MARKER in full:
                break

        full = ''.join(chars)
        if _END_MARKER not in full:
            return None, False

        full = full[:full.index(_END_MARKER)]
        if _SEP not in full:
            return full, False

        message, stored_hash = full.rsplit(_SEP, 1)
        computed = hashlib.sha256(message.encode()).hexdigest()
        return message, computed == stored_hash

    # ── Vérification ─────────────────────────────────────────────────────────
    def verifier_integrite(self, image_path: str):
        """Retourne (valide: bool, message: str)."""
        try:
            message, valid = self.extraire_tatouage(image_path)
            return valid, message or "Aucun tatouage trouvé"
        except Exception as e:
            return False, f"Erreur: {e}"
