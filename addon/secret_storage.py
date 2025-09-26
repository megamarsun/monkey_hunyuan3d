# -*- coding: utf-8 -*-
"""Secret management utilities for Monkey hunyuan3D."""

from __future__ import annotations

import json
import os
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from . import get_logger

logger = get_logger()

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

    _HAS_CRYPTOGRAPHY = True
except Exception:  # pragma: no cover - optional dependency
    AESGCM = None  # type: ignore
    _HAS_CRYPTOGRAPHY = False


_MAGIC = b"FOON"
_VERSION = 1
_FLAG_AES_GCM = 1
_FLAG_XOR = 2

_CONFIG_DIR = Path(os.path.expanduser("~/.config/fooni"))
_SECRET_FILE = _CONFIG_DIR / "secret.enc"
_PWD_FILE = _CONFIG_DIR / ".pwd"
_PWD_KEY_FILE = _CONFIG_DIR / ".pwd.key"


@dataclass
class StoredSecret:
    """Container for decrypted secrets."""

    secret_id: str
    secret_key: str


class SecretStorageError(RuntimeError):
    """Raised when secret operations fail."""


_session_secret_lock = threading.Lock()
_session_secret: Optional[StoredSecret] = None
_session_password: Optional[str] = None


def _ensure_config_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(_CONFIG_DIR, stat.S_IRWXU)
    except Exception:  # pragma: no cover - platform dependent
        logger.debug("Failed to chmod config dir", exc_info=True)


def _write_secure_file(path: Path, data: bytes) -> None:
    _ensure_config_dir()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(data)
    try:
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:  # pragma: no cover - platform dependent
        logger.debug("Failed to chmod temp file", exc_info=True)
    tmp_path.replace(path)
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:  # pragma: no cover - platform dependent
        logger.debug("Failed to chmod target file", exc_info=True)


def _derive_key(password: str, salt: bytes, length: int = 32) -> bytes:
    import hashlib

    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2 ** 14,
        r=8,
        p=1,
        dklen=length,
    )


def _xor_stream(key: bytes, nonce: bytes, data_len: int) -> bytes:
    import hashlib
    import hmac

    block_size = hashlib.sha256().digest_size
    stream = bytearray()
    counter = 0
    while len(stream) < data_len:
        counter_bytes = counter.to_bytes(4, "big")
        block = hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest()
        stream.extend(block)
        counter += 1
    return bytes(stream[:data_len])


def _encrypt_aes_gcm(plaintext: bytes, password: str, salt: bytes, nonce: bytes) -> Tuple[int, bytes, bytes]:
    key = _derive_key(password, salt)
    if not _HAS_CRYPTOGRAPHY:
        raise SecretStorageError("cryptography module is unavailable for AES-GCM.")
    assert AESGCM is not None
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, plaintext, None)
    return _FLAG_AES_GCM, ciphertext[:-16], ciphertext[-16:]


def _decrypt_aes_gcm(ciphertext: bytes, tag: bytes, password: str, salt: bytes, nonce: bytes) -> bytes:
    if not _HAS_CRYPTOGRAPHY:
        raise SecretStorageError("cryptography module is unavailable for AES-GCM.")
    assert AESGCM is not None
    key = _derive_key(password, salt)
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext + tag, None)


def _encrypt_xor(plaintext: bytes, password: str, salt: bytes, nonce: bytes) -> Tuple[int, bytes, bytes]:
    import hashlib
    import hmac

    key = _derive_key(password, salt)
    stream = _xor_stream(key, nonce, len(plaintext))
    cipher = bytes(a ^ b for a, b in zip(plaintext, stream))
    tag = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    return _FLAG_XOR, cipher, tag


def _decrypt_xor(ciphertext: bytes, tag: bytes, password: str, salt: bytes, nonce: bytes) -> bytes:
    import hashlib
    import hmac

    key = _derive_key(password, salt)
    expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, tag):
        raise SecretStorageError("Integrity check failed. Incorrect password or corrupted file.")
    stream = _xor_stream(key, nonce, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream))


def set_session_secret(secret_id: str, secret_key: str) -> None:
    global _session_secret
    with _session_secret_lock:
        _session_secret = StoredSecret(secret_id=secret_id, secret_key=secret_key)
        logger.info("Session secret stored in memory.")


def clear_session_secret() -> None:
    global _session_secret
    with _session_secret_lock:
        _session_secret = None
        logger.info("Session secret cleared.")


def get_session_secret() -> Optional[StoredSecret]:
    with _session_secret_lock:
        return _session_secret


def set_session_password(password: Optional[str]) -> None:
    global _session_password
    if password:
        _session_password = password
        logger.info("Session password stored in memory.")
    else:
        _session_password = None
        logger.info("Session password cleared.")


def get_session_password() -> Optional[str]:
    return _session_password


def clear_disk_secret() -> None:
    for path in (_SECRET_FILE,):
        try:
            if path.exists():
                path.unlink()
        except Exception:  # pragma: no cover - best effort cleanup
            logger.debug("Failed to remove %s", path, exc_info=True)


def save_encrypted_secret(secret_id: str, secret_key: str, password: str) -> None:
    payload = json.dumps({"secret_id": secret_id, "secret_key": secret_key}).encode("utf-8")
    salt = os.urandom(16)
    nonce = os.urandom(12)

    try:
        if _HAS_CRYPTOGRAPHY:
            flag, cipher, tag = _encrypt_aes_gcm(payload, password, salt, nonce)
        else:
            flag, cipher, tag = _encrypt_xor(payload, password, salt, nonce)
    except SecretStorageError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        raise SecretStorageError(f"Failed to encrypt secrets: {exc}") from exc

    data = bytearray()
    data.extend(_MAGIC)
    data.append(_VERSION)
    data.append(flag)
    data.extend(salt)
    data.extend(nonce)
    data.extend(cipher)
    data.extend(tag)
    _write_secure_file(_SECRET_FILE, bytes(data))
    logger.info("Encrypted secret written to disk at %s", _SECRET_FILE)


def load_encrypted_secret(password: str) -> StoredSecret:
    if not _SECRET_FILE.exists():
        raise SecretStorageError("Encrypted secret not found.")

    data = _SECRET_FILE.read_bytes()
    if len(data) < len(_MAGIC) + 1 + 1 + 16 + 12 + 16:
        raise SecretStorageError("Encrypted secret file is corrupted.")

    if data[:4] != _MAGIC:
        raise SecretStorageError("Invalid secret file magic header.")

    version = data[4]
    if version != _VERSION:
        raise SecretStorageError("Unsupported secret file version.")

    flag = data[5]
    salt = data[6:22]
    nonce = data[22:34]
    ciphertext = data[34:-16]
    tag = data[-16:]

    try:
        if flag == _FLAG_AES_GCM:
            plaintext = _decrypt_aes_gcm(ciphertext, tag, password, salt, nonce)
        elif flag == _FLAG_XOR:
            plaintext = _decrypt_xor(ciphertext, tag, password, salt, nonce)
        else:
            raise SecretStorageError("Unknown encryption flag in secret file.")
    except SecretStorageError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected
        raise SecretStorageError(f"Failed to decrypt secrets: {exc}") from exc

    try:
        payload = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise SecretStorageError(f"Failed to decode secret payload: {exc}") from exc

    secret_id = payload.get("secret_id", "").strip()
    secret_key = payload.get("secret_key", "").strip()
    if not secret_id or not secret_key:
        raise SecretStorageError("Decrypted payload is missing secret data.")
    logger.info("Encrypted secret loaded from disk.")
    return StoredSecret(secret_id=secret_id, secret_key=secret_key)


def save_password_to_disk(password: str) -> None:
    key = os.urandom(32)
    obfuscated = bytes(a ^ b for a, b in zip(password.encode("utf-8"), key * ((len(password) // len(key)) + 1)))[: len(password)]
    _write_secure_file(_PWD_KEY_FILE, key)
    _write_secure_file(_PWD_FILE, obfuscated)
    logger.info("Password persisted to disk with obfuscation.")


def load_password_from_disk() -> Optional[str]:
    if not (_PWD_FILE.exists() and _PWD_KEY_FILE.exists()):
        return None
    password_bytes = _PWD_FILE.read_bytes()
    key = _PWD_KEY_FILE.read_bytes()
    if not password_bytes or not key:
        return None
    expanded_key = (key * ((len(password_bytes) // len(key)) + 1))[: len(password_bytes)]
    recovered = bytes(a ^ b for a, b in zip(password_bytes, expanded_key))
    try:
        password = recovered.decode("utf-8")
    except UnicodeDecodeError:
        raise SecretStorageError("Stored password could not be decoded.")
    logger.info("Password loaded from disk obfuscation store.")
    return password


def clear_disk_password() -> None:
    for path in (_PWD_FILE, _PWD_KEY_FILE):
        try:
            if path.exists():
                path.unlink()
        except Exception:  # pragma: no cover - best effort cleanup
            logger.debug("Failed to remove %s", path, exc_info=True)


def has_encrypted_secret() -> bool:
    return _SECRET_FILE.exists()
