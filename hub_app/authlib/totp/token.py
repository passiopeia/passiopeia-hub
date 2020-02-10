"""
Creation and handling of OTPs and their secrets
"""
import hmac
import struct
import hashlib
import time
from random import SystemRandom
from typing import List

from hub_app.authlib.crypt import SymmetricCrypt


def get_otp(secret: bytes, offset: int = 0) -> str:
    """
    Get an OTP by the secret

    :param bytes secret: The secret to generate the OTP
    :param int offset: The time offset (in 30 seconds steps) - 0 means no offset
    :rtype: str
    :returns: The OTP
    """
    base_secret = secret
    if isinstance(base_secret, memoryview):  # pragma: no coverage
        base_secret = base_secret.tobytes()
    time_struct = struct.pack('>Q', int(time.time() + (offset * 30)) // 30)
    digest = hmac.new(base_secret, time_struct, hashlib.sha1).digest()
    ordinal = digest[-1] & 0x0f
    token = (struct.unpack('>I', digest[ordinal:ordinal + 4])[0] & 0x7fffffff) % 1000000
    return '{:06d}'.format(token)


def get_possible_otps(secret: bytes, start_offset: int = -1, end_offset: int = 1) -> List[str]:
    """
    Get a list of possible OTPs based on an start and end offset

    :param bytes secret: The secret to generate the otp
    :param start_offset: The time offset (in 30 seconds steps) where to start
    :param end_offset: The time offset (in 30 seconds steps) where to end
    :rtype: List[str]
    :returns: A list of valid OTPs within the given offsets
    """
    possible_tokens = []
    current_offset = start_offset
    while current_offset <= end_offset:
        possible_tokens.append(get_otp(secret, current_offset))
        current_offset += 1
    return possible_tokens


def create_random_totp_secret(secret_length: int = 72) -> bytes:
    """
    Generate a random TOTP secret

    :param int secret_length: How long should the secret be?
    :rtype: bytes
    :returns: A random secret
    """
    random = SystemRandom()
    return bytes(random.getrandbits(8) for _ in range(secret_length))


def create_encrypted_random_totp_secret(secret_length: int = 72):
    """
    Generate a random TOTP secret, encrypted

    :param int secret_length: How long should the unencrypted secret be?
    :rtype: bytes
    :returns: A random secret, but encrypted
    """
    return SymmetricCrypt().encrypt(create_random_totp_secret(secret_length))
