import csv
import time
from datetime import datetime
from pathlib import Path


RESULTS_FILE = Path("results.csv")


# ============================================================
# Time helpers
# ============================================================

def now():
    """
    High-resolution monotonic timestamp.

    perf_counter() is preferred for measuring durations
    because it is not affected by system clock changes.
    """
    return time.perf_counter()


# ============================================================
# Throughput
# ============================================================

def calculate_throughput_mbps(bytes_transferred, duration_seconds):
    """
    Calculate application throughput in megabits per second.

    Formula:

        bytes * 8
        ---------
         seconds
        ---------
        1,000,000
    """

    if duration_seconds <= 0:
        return 0.0

    return (
        bytes_transferred * 8
        / duration_seconds
        / 1_000_000
    )


# ============================================================
# Result logging
# ============================================================

def append_result(
    condition,
    transfer_id,
    file_size,
    resume_offset,
    bytes_transferred,
    duration_seconds,
    throughput_mbps,
    rtt_ms,
):
    """
    Append one successful experiment to results.csv.
    """

    file_exists = RESULTS_FILE.exists()

    with open(
        RESULTS_FILE,
        "a",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "condition",
                "transfer_id",
                "file_size_bytes",
                "resume_offset_bytes",
                "bytes_transferred",
                "duration_seconds",
                "throughput_mbps",
                "rtt_ms",
            ])

        writer.writerow([
            datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            condition,
            transfer_id,
            file_size,
            resume_offset,
            bytes_transferred,
            f"{duration_seconds:.6f}",
            f"{throughput_mbps:.3f}",
            f"{rtt_ms:.3f}",
        ])