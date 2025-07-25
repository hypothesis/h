from binascii import hexlify, unhexlify
from functools import partial
from random import randrange
from secrets import token_bytes, token_hex

import pytest
from passlib.context import CryptContext

from h.security.encryption import derive_key, password_context, token_urlsafe


class TestDeriveKey:
    # For fixed key material and salt, derive_key should give different output
    # for differing info parameters.
    def test_different_info_different_output(self, gen_key, gen_salt, gen_info):
        info_a = gen_info()
        info_b = gen_info()
        key = gen_key()
        salt = gen_salt()

        info_a_bytes = info_a.encode("utf-8")
        info_b_bytes = info_b.encode("utf-8")

        derived_a = derive_key(key, salt, info_a_bytes)
        derived_b = derive_key(key, salt, info_b_bytes)

        assert derived_a != derived_b

    def test_different_key_different_output(self, gen_key, gen_salt, gen_info):
        """If the key is rotated, the output should change."""
        key_a = gen_key()
        key_b = gen_key()
        salt = gen_salt()
        info = gen_info()
        info_bytes = info.encode("utf-8")

        derived_a = derive_key(key_a, salt, info_bytes)
        derived_b = derive_key(key_b, salt, info_bytes)

        assert derived_a != derived_b

    def test_different_salt_different_output(self, gen_key, gen_salt, gen_info):
        """If the salt is changed, the output should change."""

        info = gen_info()
        salt_a = gen_salt()
        salt_b = gen_salt()
        key = gen_key()

        info_bytes = info.encode("utf-8")

        derived_a = derive_key(key, salt_a, info_bytes)
        derived_b = derive_key(key, salt_b, info_bytes)

        assert derived_a != derived_b

    def test_consistent_output(self, gen_key, gen_salt, gen_info):
        """For fixed key, salt, info, the output should be constant."""
        key = gen_key()
        salt = gen_salt()
        info = gen_info()
        info_bytes = info.encode("utf-8")

        derived_a = derive_key(key, salt, info_bytes)
        derived_b = derive_key(key, salt, info_bytes)

        assert derived_a == derived_b

    def test_output(self, gen_key, gen_salt, gen_info):
        key = gen_key()
        salt = gen_salt()
        info = gen_info()
        info_bytes = info.encode("utf-8")

        derived = derive_key(key, salt, info_bytes)

        assert len(derived) == 64

    def test_it_encodes_str_key_material(self):
        derived = derive_key("akey", b"somesalt", b"some-info")
        assert len(derived) == 64

    # Test vectors adapted from the HKDF RFC by:
    # https://www.kullo.net/blog/hkdf-sha-512-test-vectors/
    @pytest.mark.parametrize(
        "info,key,salt,expected",
        [
            (
                "f0f1f2f3f4f5f6f7f8f9",
                "0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b",
                "000102030405060708090a0b0c",
                "832390086cda71fb47625bb5ceb168e4c8e26a1a16ed34d9fc7fe92c1481579338da362cb8d9f925d7cb",
            ),
            (
                "b0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d"
                "2d3d4d5d6d7d8d9dadbdcdddedfe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff",
                "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20212"
                "2232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f404142434445464748494a4b4c4d4e4f",
                "606162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f80818"
                "2838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeaf",
                "ce6c97192805b346e6161e821ed165673b84f400a2b514b2fe23d84cd189ddf1b695b"
                "48cbd1c8388441137b3ce28f16aa64ba33ba466b24df6cfcb021ecff235f6a2056ce3af1de44d572097a8505d9e7a93",
            ),
            (
                "f0f1f2f3f4f5f6f7f8f9",
                "0b0b0b0b0b0b0b0b0b0b0b",
                "000102030405060708090a0b0c",
                "7413e8997e020610fbf6823f2ce14bff01875db1ca55f68cfcf3954dc8aff53559bd5e3028b080f7c068",
            ),
        ],
    )
    def test_it_produces_correct_result(self, info, key, salt, expected):
        info_bytes = unhexlify(info)
        salt_bytes = unhexlify(salt)
        key_bytes = unhexlify(key)

        derived = derive_key(key_bytes, salt_bytes, info_bytes)

        # The test vectors have key lengths above and below the fixed-sized
        # output of `derive_key`. Only compare the corresponding prefixes.
        compare_len = min(len(expected), 64 * 2)
        assert hexlify(derived)[:compare_len] == expected[:compare_len].encode()

    @pytest.fixture
    def gen_key(self):
        """Generate a suitable `key` value for `derive_key`."""
        # HKDF docs don't specify an ideal length for the key, but they do
        # specify that it should be a strong / high-entropy secret.
        key_len = randrange(8, 128)  # noqa: S311
        return partial(token_bytes, key_len)

    @pytest.fixture
    def gen_salt(self):
        """Generate a suitable `salt` value for `derive_key`."""
        # HKDF docs don't specify an ideal length for the key, but they do
        # Length here is 64 bytes to match SHA-512 digest length.
        return partial(token_bytes, 64)

    @pytest.fixture
    def gen_info(self):
        """Generate an `info` value for `derive_key`."""
        # Length is not important here. This is an identifier for the key.
        info_len = randrange(4, 16)  # noqa: S311
        return partial(token_hex, info_len)


def test_password_context():
    assert isinstance(password_context, CryptContext)
    assert len(password_context.schemes()) > 0


def test_token_urlsafe():
    for nbytes in range(1, 64):
        tok = token_urlsafe(nbytes)
        # Always at least nbytes of data
        assert len(tok) > nbytes


def test_token_urlsafe_no_args():
    tok = token_urlsafe()

    assert isinstance(tok, str)
    assert len(tok) > 32
