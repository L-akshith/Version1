import pytest

from app.modules.security.encryption.hybrid_encryption import (
    EncryptedPackage,
    HybridEncryptionService,
)
from app.modules.security.encryption.rsa_oaep import (
    RSAOAEPKeyWrapper,
)


def test_hybrid_encrypt_decrypt():

    plaintext = (
        b"ExamShield confidential question paper "
        b"for testing hybrid encryption."
    )

    private_key, public_key = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    package = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    decrypted = HybridEncryptionService.decrypt(
        package=package,
        rsa_private_key=private_key,
    )

    assert decrypted == plaintext


def test_hybrid_encryption_produces_different_ciphertext():

    plaintext = b"Same question paper."

    private_key, public_key = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    package1 = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    package2 = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    assert package1.ciphertext != package2.ciphertext
    assert package1.nonce != package2.nonce
    assert package1.wrapped_aes_key != package2.wrapped_aes_key


def test_wrong_private_key_fails():

    plaintext = b"Confidential examination paper."

    private_key, public_key = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    wrong_private_key, _ = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    package = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    with pytest.raises(Exception):
        HybridEncryptionService.decrypt(
            package=package,
            rsa_private_key=wrong_private_key,
        )


def test_tampered_ciphertext_fails():

    plaintext = b"ExamShield secure paper."

    private_key, public_key = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    package = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    tampered = bytearray(package.ciphertext)
    tampered[0] ^= 1

    tampered_package = EncryptedPackage(
        ciphertext=bytes(tampered),
        nonce=package.nonce,
        wrapped_aes_key=package.wrapped_aes_key,
    )

    with pytest.raises(ValueError):
        HybridEncryptionService.decrypt(
            package=tampered_package,
            rsa_private_key=private_key,
        )


def test_tampered_nonce_fails():

    plaintext = b"ExamShield secure paper."

    private_key, public_key = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    package = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    tampered_nonce = bytearray(package.nonce)
    tampered_nonce[0] ^= 1

    tampered_package = EncryptedPackage(
        ciphertext=package.ciphertext,
        nonce=bytes(tampered_nonce),
        wrapped_aes_key=package.wrapped_aes_key,
    )

    with pytest.raises(ValueError):
        HybridEncryptionService.decrypt(
            package=tampered_package,
            rsa_private_key=private_key,
        )


def test_tampered_wrapped_key_fails():

    plaintext = b"ExamShield secure paper."

    private_key, public_key = (
        RSAOAEPKeyWrapper.generate_key_pair()
    )

    package = HybridEncryptionService.encrypt(
        plaintext=plaintext,
        rsa_public_key=public_key,
    )

    tampered_key = bytearray(package.wrapped_aes_key)
    tampered_key[0] ^= 1

    tampered_package = EncryptedPackage(
        ciphertext=package.ciphertext,
        nonce=package.nonce,
        wrapped_aes_key=bytes(tampered_key),
    )

    with pytest.raises(Exception):
        HybridEncryptionService.decrypt(
            package=tampered_package,
            rsa_private_key=private_key,
        )