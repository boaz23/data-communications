"""Encoding and decoding of data
"""

import config


def encode_int(n, size, byte_order):
    """Enocdes an integer to bytes

    Enocdes an integer to bytes using the byte order
    (endianness from the config)
    """
    return n.to_bytes(size, byte_order)


def decode_int(bytes, start, size, byte_order):
    """Deocdes an integer from bytes

    Deocdes an integer from bytes using the byte order
    (endianness from the config)
    """
    return int.from_bytes(bytes[start:start+size], byte_order)


def encode_string(s):
    """Encodes a string to bytes

    Encodes a string to bytes using the encoding from the config
    (endianness from the config)
    """
    return s.encode(config.STRING_ENCODING)


def decode_string(bytes):
    # TODO: handle errors when decoding
    """Deocdes a string from bytes

    Deocdes a string from bytes using the encoding from the config
    (endianness from the config)
    """
    return bytes.decode(config.STRING_ENCODING)
