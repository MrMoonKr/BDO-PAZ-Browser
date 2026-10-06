from __future__ import annotations

import os
import struct

import pytest

from paz.bdo_ice import BDO_ICE_KEY, IceCipher
from paz.bdo_payload_reader import bdo_decompress, ice_decrypt_bytes, ice_decrypt_many

# Two blocks, 00 01 .. 0F. The expected outputs were taken from the original
# block-at-a-time port of kukdh1/PAZ-Unpacker, before the loop was rewritten.
_BLOCKS = bytes(range(16))
_KEY_16 = bytes(range(0x10, 0x20))


def test_ice_decrypt_matches_the_reference_port() -> None:
    assert IceCipher(BDO_ICE_KEY).decrypt(_BLOCKS).hex() == "544e03c9383e92252d9b5234571c54ab"


def test_ice_encrypt_matches_the_reference_port() -> None:
    assert IceCipher(BDO_ICE_KEY).encrypt(_BLOCKS).hex() == "c3bdf28b3c7dde63bccdf2d6ce3ace8e"


def test_ice_16_byte_key_matches_the_reference_port() -> None:
    assert IceCipher(_KEY_16).decrypt(_BLOCKS).hex() == "38f5d62086d7bc4011c87f1c9c9f0497"


@pytest.mark.parametrize("key", [BDO_ICE_KEY, _KEY_16], ids=["bdo-key", "16-byte-key"])
def test_ice_round_trips(key: bytes) -> None:
    data = os.urandom(4096)
    cipher = IceCipher(key)

    assert cipher.decrypt(cipher.encrypt(data)) == data


def test_ice_decrypts_each_block_on_its_own() -> None:
    data = os.urandom(64 * 1024)
    cipher = IceCipher(BDO_ICE_KEY)
    block_by_block = b"".join(cipher.decrypt(data[i : i + 8]) for i in range(0, len(data), 8))

    assert cipher.decrypt(data) == block_by_block


def test_ice_decrypts_empty_input() -> None:
    assert IceCipher(BDO_ICE_KEY).decrypt(b"") == b""


def test_ice_rejects_a_partial_block() -> None:
    with pytest.raises(ValueError, match="multiple of 8"):
        IceCipher(BDO_ICE_KEY).decrypt(bytes(7))


def test_ice_decrypt_bytes_keeps_the_input_length() -> None:
    data = os.urandom(13)
    padded = data + bytes(3)

    assert ice_decrypt_bytes(data) == IceCipher(BDO_ICE_KEY).decrypt(padded)[:13]


def test_ice_decrypt_many_matches_one_call_per_input() -> None:
    inputs = [os.urandom(size) for size in (13, 0, 8, 4096, 1, 63)]

    assert ice_decrypt_many(inputs) == [ice_decrypt_bytes(data) for data in inputs]


# A hand-built short-mode stream: 8 literals, a back-reference that copies
# them, one whose source overlaps its output (repeat 3, length 10), then the
# byte-at-a-time tail.
_GROUP_HEADER = 0x80000000 | 0b011 << 8  # bits 0-7 literal, 8-9 back-reference
_COPY_8_FROM_8 = (8 << 6) | ((8 - 3) << 2) | 0x02
_COPY_10_FROM_3 = (3 << 6) | ((10 - 3) << 2) | 0x02
_DECOMPRESSED = b"ABCDEFGH" + b"ABCDEFGH" + b"FGHFGHFGHF" + b"WXYZ"


def _short_stream(decompressed_length: int) -> bytes:
    body = (
        struct.pack("<I", _GROUP_HEADER)
        + b"ABCDEFGH"
        + struct.pack("<HH", _COPY_8_FROM_8, _COPY_10_FROM_3)
        + b"WXYZ"
    )
    return bytes([0x01, 3 + len(body), decompressed_length]) + body


def test_decompress_literals_and_back_references() -> None:
    assert bdo_decompress(_short_stream(len(_DECOMPRESSED))) == _DECOMPRESSED


def test_decompress_rejects_a_back_reference_past_the_end() -> None:
    with pytest.raises(ValueError, match="error code -3"):
        bdo_decompress(_short_stream(18))


def test_decompress_returns_a_stored_payload_as_is() -> None:
    stored = bytes([0x00, 3 + 5, 5]) + b"plain"

    assert bdo_decompress(stored) == b"plain"
