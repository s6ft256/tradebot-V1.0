from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

if TYPE_CHECKING:
    pass


@dataclass
class SecureCredentials:
    """Encrypted exchange API credentials."""
    user_id: str
    exchange_id: str
    encrypted_api_key: bytes
    encrypted_api_secret: bytes
    encrypted_passphrase: bytes | None
    key_hash: str  # For verification without decryption
    created_at: str
    last_used: str | None
    access_count: int


class ApiKeyCustody:
    """
    Secure API key custody with encryption at rest.
    Implements industry-standard security practices for key storage.
    """

    def __init__(self, master_key: str | None = None):
        """
        Initialize API key custody.
        
        Args:
            master_key: Base64-encoded encryption key. If None, generates new key.
        """
        if master_key:
            self._master_key = base64.urlsafe_b64decode(master_key.encode())
        else:
            self._master_key = Fernet.generate_key()
        
        self._fernet = Fernet(base64.urlsafe_b64encode(self._master_key))
        self._credentials: dict[str, SecureCredentials] = {}  # user_id + exchange -> credentials
        self._access_log: list[dict] = []

    def _derive_key(self, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def _hash_for_verification(self, plaintext: str) -> str:
        """Create HMAC hash for verification without storing plaintext."""
        return hmac.new(
            self._master_key,
            plaintext.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

    def store_credentials(
        self,
        user_id: str,
        exchange_id: str,
        api_key: str,
        api_secret: str,
        passphrase: str | None = None,
    ) -> SecureCredentials:
        """
        Store exchange API credentials securely.
        
        Args:
            user_id: Unique user identifier
            exchange_id: Exchange identifier (e.g., 'binance', 'coinbase')
            api_key: API key to encrypt
            api_secret: API secret to encrypt
            passphrase: Optional passphrase for exchanges that require it
            
        Returns:
            SecureCredentials object with encrypted data
        """
        # Encrypt credentials
        encrypted_key = self._fernet.encrypt(api_key.encode())
        encrypted_secret = self._fernet.encrypt(api_secret.encode())
        encrypted_pass = self._fernet.encrypt(passphrase.encode()) if passphrase else b""
        
        # Create verification hash (first 16 chars of HMAC)
        key_hash = self._hash_for_verification(api_key)
        
        from datetime import datetime
        credentials = SecureCredentials(
            user_id=user_id,
            exchange_id=exchange_id,
            encrypted_api_key=encrypted_key,
            encrypted_api_secret=encrypted_secret,
            encrypted_passphrase=encrypted_pass if passphrase else None,
            key_hash=key_hash,
            created_at=datetime.utcnow().isoformat(),
            last_used=None,
            access_count=0,
        )
        
        # Store with composite key
        storage_key = f"{user_id}:{exchange_id}"
        self._credentials[storage_key] = credentials
        
        # Log the storage (without sensitive data)
        self._log_access(user_id, exchange_id, "store", success=True)
        
        return credentials

    def retrieve_credentials(
        self,
        user_id: str,
        exchange_id: str,
        request_reason: str,
    ) -> dict | None:
        """
        Retrieve and decrypt exchange credentials.
        
        Args:
            user_id: User identifier
            exchange_id: Exchange identifier
            request_reason: Reason for access (auditing)
            
        Returns:
            Decrypted credentials dict or None if not found
        """
        storage_key = f"{user_id}:{exchange_id}"
        creds = self._credentials.get(storage_key)
        
        if not creds:
            self._log_access(user_id, exchange_id, "retrieve", success=False, reason="not_found")
            return None
        
        try:
            # Decrypt credentials
            api_key = self._fernet.decrypt(creds.encrypted_api_key).decode()
            api_secret = self._fernet.decrypt(creds.encrypted_api_secret).decode()
            passphrase = None
            if creds.encrypted_passphrase:
                passphrase = self._fernet.decrypt(creds.encrypted_passphrase).decode()
            
            # Update access tracking
            from datetime import datetime
            creds.last_used = datetime.utcnow().isoformat()
            creds.access_count += 1
            
            # Log access
            self._log_access(user_id, exchange_id, "retrieve", success=True, reason=request_reason)
            
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "passphrase": passphrase,
            }
        except Exception as e:
            self._log_access(user_id, exchange_id, "retrieve", success=False, reason=f"decryption_error: {e}")
            return None

    def verify_credentials_match(
        self,
        user_id: str,
        exchange_id: str,
        api_key: str,
    ) -> bool:
        """
        Verify if provided API key matches stored credentials without full decryption.
        Useful for validation without exposing secrets.
        """
        storage_key = f"{user_id}:{exchange_id}"
        creds = self._credentials.get(storage_key)
        
        if not creds:
            return False
        
        provided_hash = self._hash_for_verification(api_key)
        return hmac.compare_digest(provided_hash, creds.key_hash)

    def delete_credentials(self, user_id: str, exchange_id: str) -> bool:
        """Permanently delete stored credentials."""
        storage_key = f"{user_id}:{exchange_id}"
        
        if storage_key in self._credentials:
            del self._credentials[storage_key]
            self._log_access(user_id, exchange_id, "delete", success=True)
            return True
        
        self._log_access(user_id, exchange_id, "delete", success=False, reason="not_found")
        return False

    def rotate_encryption_key(self, new_master_key: str | None = None) -> str:
        """
        Rotate encryption key and re-encrypt all credentials.
        
        Returns:
            New master key (base64 encoded)
        """
        # Generate new key if not provided
        if new_master_key:
            new_key = base64.urlsafe_b64decode(new_master_key.encode())
        else:
            new_key = Fernet.generate_key()
        
        new_fernet = Fernet(base64.urlsafe_b64encode(new_key))
        
        # Re-encrypt all credentials
        for storage_key, creds in self._credentials.items():
            try:
                # Decrypt with old key
                api_key = self._fernet.decrypt(creds.encrypted_api_key)
                api_secret = self._fernet.decrypt(creds.encrypted_api_secret)
                passphrase = None
                if creds.encrypted_passphrase:
                    passphrase = self._fernet.decrypt(creds.encrypted_passphrase)
                
                # Re-encrypt with new key
                creds.encrypted_api_key = new_fernet.encrypt(api_key)
                creds.encrypted_api_secret = new_fernet.encrypt(api_secret)
                if passphrase:
                    creds.encrypted_passphrase = new_fernet.encrypt(passphrase)
            except Exception as e:
                # Log but continue with other credentials
                user_id, exchange_id = storage_key.split(":")
                self._log_access(user_id, exchange_id, "key_rotation", success=False, reason=str(e))
        
        # Update master key
        self._master_key = new_key
        self._fernet = new_fernet
        
        return base64.urlsafe_b64encode(new_key).decode()

    def get_custody_report(self, user_id: str | None = None) -> dict:
        """
        Get report of stored credentials (without sensitive data).
        
        Args:
            user_id: Optional filter by user
            
        Returns:
            Report dict with credential metadata
        """
        report = {
            "total_credentials": 0,
            "by_exchange": {},
            "by_user": {},
            "recent_access": [],
        }
        
        for storage_key, creds in self._credentials.items():
            if user_id and creds.user_id != user_id:
                continue
            
            report["total_credentials"] += 1
            
            # Count by exchange
            report["by_exchange"][creds.exchange_id] = report["by_exchange"].get(creds.exchange_id, 0) + 1
            
            # Count by user
            report["by_user"][creds.user_id] = report["by_user"].get(creds.user_id, 0) + 1
        
        # Recent access log (last 100 entries)
        report["recent_access"] = self._access_log[-100:]
        
        return report

    def _log_access(
        self,
        user_id: str,
        exchange_id: str,
        action: str,
        success: bool,
        reason: str | None = None,
    ) -> None:
        """Log access attempt for auditing."""
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "exchange_id": exchange_id,
            "action": action,
            "success": success,
            "reason": reason,
        }
        
        self._access_log.append(entry)
        
        # Keep log size manageable
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-5000:]

    def export_master_key(self) -> str:
        """Export master key for backup (keep secure!)."""
        return base64.urlsafe_b64encode(self._master_key).decode()

    def has_credentials(self, user_id: str, exchange_id: str) -> bool:
        """Check if credentials exist for user/exchange."""
        storage_key = f"{user_id}:{exchange_id}"
        return storage_key in self._credentials

    def list_user_exchanges(self, user_id: str) -> list[str]:
        """List all exchanges with stored credentials for user."""
        exchanges = []
        for storage_key, creds in self._credentials.items():
            if creds.user_id == user_id:
                exchanges.append(creds.exchange_id)
        return exchanges
