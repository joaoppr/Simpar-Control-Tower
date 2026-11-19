"""Criptografia de credenciais de conectores (Fernet). Segredos nunca sao devolvidos pela API."""
import json
from cryptography.fernet import Fernet
from .config import settings, ROOT

_KEY_FILE = ROOT / ".secret_key"


def _key() -> bytes:
    if settings.secret_key:
        return settings.secret_key.encode()
    if not _KEY_FILE.exists():
        _KEY_FILE.write_bytes(Fernet.generate_key())
        _KEY_FILE.chmod(0o600)
    return _KEY_FILE.read_bytes()


def encrypt(payload: dict) -> str:
    return Fernet(_key()).encrypt(json.dumps(payload).encode()).decode()


def decrypt(token: str | None) -> dict:
    if not token:
        return {}
    return json.loads(Fernet(_key()).decrypt(token.encode()).decode())
