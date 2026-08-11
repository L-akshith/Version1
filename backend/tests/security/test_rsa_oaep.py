import pytest

from app.modules.security.encryption.aes_gcm import (
    AESGCMEncryptionService,
)
from app.modules.security.encryption.rsa_oaep import (
    RSAOAEPKeyWrapper,
)


def test_wrap_and_unwrap_aes_key():

    private_key, public_key = RSAOAEPKeyWrapper.generate_key_pair()

    aes_key = AESGCMEncryptionService.generate_key()

    wrapped_key = RSAOAEPKeyWrapper.wrap_key(
        aes_key,
        public_key,
    )

    unwrapped_key = RSAOAEPKeyWrapper.unwrap_key(
        wrapped_key,
        private_key,
    )

    assert unwrapped_key == aes_key


def test_wrong_private_key_fails():

    private_key, public_key = RSAOAEPKeyWrapper.generate_key_pair()

    wrong_private_key, _ = RSAOAEPKeyWrapper.generate_key_pair()

    aes_key = AESGCMEncryptionService.generate_key()

    wrapped_key = RSAOAEPKeyWrapper.wrap_key(
        aes_key,
        public_key,
    )

    with pytest.raises(Exception):
        RSAOAEPKeyWrapper.unwrap_key(
            wrapped_key,
            wrong_private_key,
        )


def test_wrapped_key_is_not_plain_aes_key():

    _, public_key = RSAOAEPKeyWrapper.generate_key_pair()

    aes_key = AESGCMEncryptionService.generate_key()

    wrapped_key = RSAOAEPKeyWrapper.wrap_key(
        aes_key,
        public_key,
    )

    assert wrapped_key != aes_key