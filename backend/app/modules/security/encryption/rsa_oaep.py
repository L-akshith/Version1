from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


class RSAOAEPKeyWrapper:
    """RSA-4096 OAEP wrapper for protecting AES session keys."""

    KEY_SIZE = 4096

    @staticmethod
    def generate_key_pair():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=RSAOAEPKeyWrapper.KEY_SIZE,
        )

        return private_key, private_key.public_key()

    @staticmethod
    def wrap_key(aes_key: bytes, public_key) -> bytes:
        if not aes_key:
            raise ValueError("AES key cannot be empty.")

        return public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def unwrap_key(wrapped_key: bytes, private_key) -> bytes:
        if not wrapped_key:
            raise ValueError("Wrapped key cannot be empty.")

        return private_key.decrypt(
            wrapped_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )