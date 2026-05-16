from cryptography.fernet import Fernet

from app.config import settings


fernet = Fernet(
    settings.ENCRYPTION_KEY.encode()
)


def encrypt_value(
    value: str
) -> str:

    encrypted = fernet.encrypt(
        value.encode()
    )

    return encrypted.decode()


def decrypt_value(
    encrypted_value: str
) -> str:

    decrypted = fernet.decrypt(
        encrypted_value.encode()
    )

    return decrypted.decode()