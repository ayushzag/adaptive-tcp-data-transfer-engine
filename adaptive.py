LOW_RTT_THRESHOLD_MS = 50.0

NORMAL_CHUNK_SIZE = 4096
HIGH_RTT_CHUNK_SIZE = 256 * 1024


def choose_chunk_size(rtt_ms: float) -> int:
    """Choose one application-level chunk size from a single RTT probe."""
    if rtt_ms < 0:
        raise ValueError("RTT cannot be negative")

    if rtt_ms < LOW_RTT_THRESHOLD_MS:
        return NORMAL_CHUNK_SIZE

    return HIGH_RTT_CHUNK_SIZE