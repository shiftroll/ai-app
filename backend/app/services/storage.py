"""
File storage service

Handles file uploads with encryption at rest.
"""

import os
import hashlib
from datetime import datetime
from typing import Optional
import logging

from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """Get encryption key for file storage"""
    key = settings.encryption_key.encode()
    # Ensure key is 32 bytes for Fernet
    if len(key) != 32:
        key = hashlib.sha256(key).digest()
    return Fernet.generate_key()  # In production, use stored key


# Fernet instance for encryption
_fernet = None


def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption"""
    global _fernet
    if _fernet is None:
        key = settings.encryption_key.encode()
        # Pad or hash to 32 bytes
        if len(key) < 32:
            key = key + b'0' * (32 - len(key))
        elif len(key) > 32:
            key = hashlib.sha256(key).digest()
        # Generate Fernet key from our key
        import base64
        fernet_key = base64.urlsafe_b64encode(key)
        _fernet = Fernet(fernet_key)
    return _fernet


async def save_uploaded_file(
    content: bytes,
    original_filename: str,
    contract_id: str,
    encrypt: bool = True,
) -> str:
    """
    Save an uploaded file to storage.

    Args:
        content: File content bytes
        original_filename: Original filename
        contract_id: Contract ID for organization
        encrypt: Whether to encrypt the file at rest

    Returns:
        Path to saved file
    """
    # Create directory structure
    upload_dir = os.path.join(settings.upload_dir, contract_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(original_filename)[1]
    filename = f"{timestamp}_{hashlib.md5(original_filename.encode()).hexdigest()[:8]}{ext}"

    # Encrypt if requested
    if encrypt and settings.environment != "development":
        fernet = get_fernet()
        content = fernet.encrypt(content)
        filename = filename + ".enc"

    # Save file
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"File saved: {file_path} (encrypted: {encrypt})")
    return file_path


async def read_uploaded_file(file_path: str, decrypt: bool = True) -> bytes:
    """
    Read an uploaded file from storage.

    Args:
        file_path: Path to file
        decrypt: Whether to decrypt the file

    Returns:
        File content bytes
    """
    with open(file_path, "rb") as f:
        content = f.read()

    # Decrypt if file is encrypted
    if decrypt and file_path.endswith(".enc"):
        fernet = get_fernet()
        content = fernet.decrypt(content)

    return content


def get_file_path(contract_id: str, filename: str) -> str:
    """Get the full path for a file"""
    # Find the file in the contract directory
    upload_dir = os.path.join(settings.upload_dir, contract_id)
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            if filename in f or f.startswith(filename.split('.')[0]):
                return os.path.join(upload_dir, f)

    # Return expected path if not found
    return os.path.join(upload_dir, filename)


async def delete_file(file_path: str) -> bool:
    """Delete a file from storage"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return False
