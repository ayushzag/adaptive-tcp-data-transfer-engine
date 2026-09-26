import struct


def pack_header(file_size):
    # File size ko 8-byte format mein convert kar rahe hain.
    # Socket/network par actual mein bytes hi send hote hain.
    return struct.pack("!Q", file_size)


def unpack_header(header):
    # Received 8-byte header ko wapas normal integer mein convert kar rahe hain.
    return struct.unpack("!Q", header)[0]