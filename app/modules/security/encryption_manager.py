import base64
import logging
from cryptography.fernet import Fernet
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Encryption Key
ENCRYPTION_KEY = Config.ENCRYPTION_KEY  # Ensure this key is stored securely
fernet = Fernet(ENCRYPTION_KEY)

class EncryptionManager:
    """
    Handles AES-256 encryption and decryption of sensitive data.
    """

    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypts sensitive information using AES-256 encryption."""
        try:
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logging.error(f"❌ Encryption failed: {e}")
            return None

    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Decrypts AES-256 encrypted data back to plaintext."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data).decode()
            return decrypted_data
        except Exception as e:
            logging.error(f"❌ Decryption failed: {e}")
            return None

# Example Usage
if __name__ == "__main__":
    sensitive_info = "SuperSecretAPIKey123!"
    encrypted = EncryptionManager.encrypt_data(sensitive_info)
    print(f"🔒 Encrypted: {encrypted}")
    
    decrypted = EncryptionManager.decrypt_data(encrypted)
    print(f"🔑 Decrypted: {decrypted}")
