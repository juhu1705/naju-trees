import random
from typing import SupportsInt, Union

SYSTEM_RANDOM = random.SystemRandom()
URI_SAFE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890-_'
EMAIL_RE = r'^[a-zA-Z0-9!#$%&‘*+–/=?^_`{|}~](\.?[a-zA-Z0-9!#$%&‘*+–/=?^_`{|}~])*@[a-zA-Z0-9-](\.?[a-zA-Z0-9-])*$'


def random_uri_safe_string(length: int) -> str:
    return ''.join(SYSTEM_RANDOM.choice(URI_SAFE_CHARS) for _ in range(length))


def check_email(email):
    import re
    return re.search(EMAIL_RE, email)


def nbit_int(x: Union[str, bytes, SupportsInt], base=10, maxbits=32) -> int:
    result = int(x, base)
    if result.bit_length() > maxbits:
        raise ValueError(f"integer exceeds {maxbits}-bit limit")

    return result
