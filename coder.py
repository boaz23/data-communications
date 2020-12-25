import config

def encode_int(n, size):
    return n.to_bytes(size, config.INTEGER_ENDIANNESS)

def decode_int(bytes):
    return int.from_bytes(bytes, config.INTEGER_ENDIANNESS)

def encode_string(s):
    return s.encode(config.STRING_ENCODING)

def decode_string(bytes):
    return bytes.decode(config.STRING_ENCODING)