import pytest

from adaptive import (
    HIGH_RTT_CHUNK_SIZE,
    LOW_RTT_THRESHOLD_MS,
    NORMAL_CHUNK_SIZE,
    choose_chunk_size,
)


def test_low_rtt_uses_normal_chunk_size():
    assert choose_chunk_size(5.5) == NORMAL_CHUNK_SIZE


def test_high_rtt_uses_large_chunk_size():
    assert choose_chunk_size(117.0) == HIGH_RTT_CHUNK_SIZE


def test_threshold_uses_large_chunk_size():
    assert choose_chunk_size(
        LOW_RTT_THRESHOLD_MS
    ) == HIGH_RTT_CHUNK_SIZE


def test_negative_rtt_is_rejected():
    with pytest.raises(ValueError):
        choose_chunk_size(-1.0)