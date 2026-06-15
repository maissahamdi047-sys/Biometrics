"""
core/securite/hash_utils.py
Utilitaires de hachage SHA-256 pour l'intégrité des données.
"""
import hashlib
import json
from typing import Union


def calculer_hash(data: Union[str, bytes, dict]) -> str:
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')
    elif isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def verifier_hash(data: Union[str, bytes, dict], hash_attendu: str) -> bool:
    return calculer_hash(data) == hash_attendu
