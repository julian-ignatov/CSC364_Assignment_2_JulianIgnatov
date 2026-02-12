import struct

# Client -> Server
LOGIN = 0
LOGOUT = 1
JOIN = 2
LEAVE = 3
SAY_REQ = 4
LIST_REQ = 5
WHO_REQ = 6
KEEPALIVE = 7

# Server -> Client
SAY_RESP = 0
LIST_RESP = 1
WHO_RESP = 2
ERROR_RESP = 3

USERNAME_SIZE = 32
CHANNEL_SIZE = 32
TEXT_SIZE = 64

def pad_string(text: str, size: int) -> bytes:
    b = text.encode("utf-8")[:size]
    return b.ljust(size, b'\0')


def pack_login(username: str) -> bytes:
    header = struct.pack("!I", LOGIN)
    username_bytes = pad_string(username, USERNAME_SIZE)
    return header + username_bytes


def parse_login(data: bytes) -> str:
    username_bytes = data[4:4 + USERNAME_SIZE]
    return username_bytes.rstrip(b'\0').decode("utf-8", errors="replace")


def pack_join(channel: str) -> bytes:
    header = struct.pack("!I", JOIN)
    channel_bytes = pad_string(channel, CHANNEL_SIZE)
    return header + channel_bytes


def parse_join(data: bytes) -> str:
    channel_bytes = data[4:4 + CHANNEL_SIZE]
    return channel_bytes.rstrip(b'\0').decode("utf-8", errors="replace")


def pack_say(channel: str, text: str) -> bytes:
    header = struct.pack("!I", SAY_REQ)
    channel_bytes = pad_string(channel, CHANNEL_SIZE)
    text_bytes = pad_string(text, TEXT_SIZE)
    return header + channel_bytes + text_bytes


def parse_say(data: bytes) -> tuple[str, str]:
    channel = data[4:4+CHANNEL_SIZE].rstrip(b'\0').decode()
    text = data[4+CHANNEL_SIZE:4+CHANNEL_SIZE+TEXT_SIZE].rstrip(b'\0').decode()
    return channel, text


def pack_say_response(channel: str, username: str, text: str) -> bytes:
    header = struct.pack("!I", SAY_RESP)
    channel_bytes = pad_string(channel, 32)
    username_bytes = pad_string(username, 32)
    text_bytes = pad_string(text, 64)
    return header + channel_bytes + username_bytes + text_bytes


def pack_leave(channel: str) -> bytes:
    header = struct.pack("!I", LEAVE)
    channel_bytes = pad_string(channel, 32)
    return header + channel_bytes


def parse_leave(data: bytes) -> str:
    channel_bytes = data[4:36]
    return channel_bytes.rstrip(b'\0').decode("utf-8", errors="replace")


def pack_list() -> bytes:
    return struct.pack("!I", LIST_REQ)


def pack_who(channel: str) -> bytes:
    header = struct.pack("!I", WHO_REQ)
    channel_bytes = pad_string(channel, 32)
    return header + channel_bytes


def pack_keepalive() -> bytes:
    return struct.pack("!I", KEEPALIVE)
