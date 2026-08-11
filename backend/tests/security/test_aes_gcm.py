import pytest

from app.modules.security.encryption.aes_gcm import (
    AESGCMEncryptionService,
)


def test_encrypt_decrypt():

    plaintext = b"ExamShield confidential question paper"

    key = AESGCMEncryptionService.generate_key()

    ciphertext, nonce = AESGCMEncryptionService.encrypt(
        plaintext,
        key,
    )

    decrypted = AESGCMEncryptionService.decrypt(
        ciphertext,
        key,
        nonce,
    )

    assert decrypted == plaintext


def test_wrong_key_fails():

    plaintext = b"Confidential paper"

    key = AESGCMEncryptionService.generate_key()
    wrong_key = AESGCMEncryptionService.generate_key()

    ciphertext, nonce = AESGCMEncryptionService.encrypt(
        plaintext,
        key,
    )

    with pytest.raises(ValueError):
        AESGCMEncryptionService.decrypt(
            ciphertext,
            wrong_key,
            nonce,
        )


def test_tampered_ciphertext_fails():

    plaintext = b"ExamShield confidential paper"

    key = AESGCMEncryptionService.generate_key()

    ciphertext, nonce = AESGCMEncryptionService.encrypt(
        plaintext,
        key,
    )

    tampered = bytearray(ciphertext)
    tampered[0] ^= 1

    with pytest.raises(ValueError):
        AESGCMEncryptionService.decrypt(
            bytes(tampered),
            key,
            nonce,
        )


def test_tampered_nonce_fails():

    plaintext = b"ExamShield confidential paper"

    key = AESGCMEncryptionService.generate_key()

    ciphertext, nonce = AESGCMEncryptionService.encrypt(
        plaintext,
        key,
    )

    tampered_nonce = bytearray(nonce)
    tampered_nonce[0] ^= 1

    with pytest.raises(ValueError):
        AESGCMEncryptionService.decrypt(
            ciphertext,
            key,
            bytes(tampered_nonce),
        )


def test_each_encryption_gets_new_nonce():

    plaintext = b"Same paper"

    key = AESGCMEncryptionService.generate_key()

    ciphertext1, nonce1 = AESGCMEncryptionService.encrypt(
        plaintext,
        key,
    )

    ciphertext2, nonce2 = AESGCMEncryptionService.encrypt(
        plaintext,
        key,
    )

    assert nonce1 != nonce2
    assert ciphertext1 != ciphertext2