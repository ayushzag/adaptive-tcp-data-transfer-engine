import struct


# ============================================================
# Message types
# ============================================================

START_TRANSFER = 1
RESUME_OFFSET = 2
FINAL_HASH = 3
TRANSFER_STATUS = 4

# Day 5
PING = 5
PONG = 6


# ============================================================
# Status codes
# ============================================================

STATUS_OK = 0
STATUS_CHECKSUM_MISMATCH = 1
STATUS_INVALID_REQUEST = 2


# ============================================================
# Struct definitions
# ============================================================

# START_TRANSFER:
# 1 byte  -> message type
# 2 bytes -> transfer ID length
# 8 bytes -> file size
START_FIXED_STRUCT = struct.Struct("!BHQ")


# RESUME_OFFSET:
# 1 byte -> message type
# 8 bytes -> offset
RESUME_STRUCT = struct.Struct("!BQ")


# FINAL_HASH:
# 1 byte -> message type
HASH_HEADER_STRUCT = struct.Struct("!B")


# TRANSFER_STATUS:
# 1 byte -> message type
# 1 byte -> status code
STATUS_STRUCT = struct.Struct("!BB")


# PING / PONG:
# 1 byte -> message type
PING_STRUCT = struct.Struct("!B")
PONG_STRUCT = struct.Struct("!B")


# ============================================================
# START_TRANSFER
# ============================================================

def pack_transfer_start(transfer_id, file_size):
    transfer_id_bytes = transfer_id.encode("utf-8")

    if len(transfer_id_bytes) > 65535:
        raise ValueError("Transfer ID is too long")

    if file_size < 0:
        raise ValueError("File size cannot be negative")

    return (
        START_FIXED_STRUCT.pack(
            START_TRANSFER,
            len(transfer_id_bytes),
            file_size,
        )
        + transfer_id_bytes
    )


async def read_transfer_start(reader, first_byte=None):
    """
    Read START_TRANSFER message.

    If first_byte is already consumed by the caller,
    use it here to reconstruct the fixed header.
    """

    if first_byte is None:
        fixed_header = await reader.readexactly(
            START_FIXED_STRUCT.size
        )
    else:
        if len(first_byte) != 1:
            raise ValueError("first_byte must contain exactly 1 byte")

        remaining = await reader.readexactly(
            START_FIXED_STRUCT.size - 1
        )

        fixed_header = first_byte + remaining

    message_type, id_length, file_size = (
        START_FIXED_STRUCT.unpack(fixed_header)
    )

    if message_type != START_TRANSFER:
        raise ConnectionError(
            "Expected START_TRANSFER message"
        )

    transfer_id_bytes = await reader.readexactly(id_length)

    transfer_id = transfer_id_bytes.decode("utf-8")

    return transfer_id, file_size


# ============================================================
# RESUME_OFFSET
# ============================================================

def pack_resume_offset(offset):
    if offset < 0:
        raise ValueError("Offset cannot be negative")

    return RESUME_STRUCT.pack(
        RESUME_OFFSET,
        offset
    )


def unpack_resume_offset(data):
    if len(data) != RESUME_STRUCT.size:
        raise ValueError("Invalid resume message")

    message_type, offset = RESUME_STRUCT.unpack(data)

    if message_type != RESUME_OFFSET:
        raise ValueError("Expected RESUME_OFFSET message")

    return offset


# ============================================================
# FINAL_HASH
# ============================================================

def pack_final_hash(digest_hex):
    digest_bytes = bytes.fromhex(digest_hex)

    if len(digest_bytes) != 32:
        raise ValueError(
            "SHA-256 digest must be exactly 32 bytes"
        )

    return (
        HASH_HEADER_STRUCT.pack(FINAL_HASH)
        + digest_bytes
    )


async def read_final_hash(reader):
    message_type_bytes = await reader.readexactly(
        HASH_HEADER_STRUCT.size
    )

    message_type = HASH_HEADER_STRUCT.unpack(
        message_type_bytes
    )[0]

    if message_type != FINAL_HASH:
        raise ConnectionError(
            "Expected FINAL_HASH message"
        )

    digest_bytes = await reader.readexactly(32)

    return digest_bytes.hex()


# ============================================================
# TRANSFER_STATUS
# ============================================================

def pack_status(status_code):
    return STATUS_STRUCT.pack(
        TRANSFER_STATUS,
        status_code
    )


def unpack_status(data):
    if len(data) != STATUS_STRUCT.size:
        raise ValueError("Invalid status message")

    message_type, status_code = STATUS_STRUCT.unpack(data)

    if message_type != TRANSFER_STATUS:
        raise ValueError(
            "Expected TRANSFER_STATUS message"
        )

    return status_code


# ============================================================
# PING / PONG - Day 5 RTT measurement
# ============================================================

def pack_ping():
    return PING_STRUCT.pack(PING)


def pack_pong():
    return PONG_STRUCT.pack(PONG)


def unpack_pong(data):
    if len(data) != PONG_STRUCT.size:
        raise ValueError("Invalid PONG message")

    message_type = PONG_STRUCT.unpack(data)[0]

    if message_type != PONG:
        raise ConnectionError("Expected PONG message")

    return True