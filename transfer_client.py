import argparse
import asyncio
import os
import time
import uuid

from protocol import (
    pack_ping,
    unpack_pong,
    pack_transfer_start,
    unpack_resume_offset,
    pack_final_hash,
    unpack_status,
    STATUS_OK,
)

from integrity import (
    create_hasher,
    update_hash,
    get_digest,
)

from retry import retry

from metrics import (
    calculate_throughput_mbps,
    append_result,
)


HOST = "127.0.0.1"
PORT = 5050

CHUNK_SIZE = 4096


# ============================================================
# RTT measurement
# ============================================================

async def measure_rtt(reader, writer):
    """
    Application-level RTT probe.

    The TCP connection is already established.

    We send:
        PING

    Server replies:
        PONG

    RTT is measured between those two application messages.
    """

    start = time.perf_counter()

    writer.write(pack_ping())
    await writer.drain()

    pong = await asyncio.wait_for(
        reader.readexactly(1),
        timeout=5,
    )

    unpack_pong(pong)

    end = time.perf_counter()

    return (end - start) * 1000


# ============================================================
# One transfer attempt
# ============================================================

async def transfer_once(
    file_path,
    transfer_id,
    fail_after_chunks=0,
    corrupt=False,
    condition="baseline",
):
    file_size = os.path.getsize(file_path)

    print(f"Connecting to {HOST}:{PORT}...")

    reader, writer = await asyncio.open_connection(
        HOST,
        PORT,
    )

    print("Connected")

    try:

        # ====================================================
        # STEP 1: Measure RTT
        # ====================================================

        rtt_ms = await measure_rtt(
            reader,
            writer,
        )

        print(
            f"Application RTT: {rtt_ms:.3f} ms"
        )

        # ====================================================
        # STEP 2: Send transfer information
        # ====================================================

        start_message = pack_transfer_start(
            transfer_id,
            file_size,
        )

        writer.write(start_message)
        await writer.drain()

        print(f"Transfer ID: {transfer_id}")
        print(f"File size: {file_size} bytes")

        # ====================================================
        # STEP 3: Receive resume offset
        # ====================================================

        resume_message = await reader.readexactly(9)

        offset = unpack_resume_offset(
            resume_message
        )

        if offset > file_size:
            raise ConnectionError(
                "Server resume offset is larger "
                "than local file size"
            )

        print(
            f"Server already has: {offset} bytes"
        )

        print(
            f"Resuming from: {offset} bytes"
        )

        # ====================================================
        # STEP 4: Create SHA-256 hasher
        # ====================================================

        hasher = create_hasher()

        # Hash bytes that server already has.
        if offset > 0:

            with open(file_path, "rb") as f:

                remaining = offset

                while remaining > 0:

                    chunk = f.read(
                        min(
                            CHUNK_SIZE,
                            remaining,
                        )
                    )

                    if not chunk:
                        raise ConnectionError(
                            "Unexpected EOF while "
                            "hashing resume prefix"
                        )

                    update_hash(
                        hasher,
                        chunk,
                    )

                    remaining -= len(chunk)

        # ====================================================
        # STEP 5: Send remaining file
        # ====================================================

        sent = offset
        chunks_sent = 0
        corruption_done = False

        transfer_start = None
        transfer_end = None

        with open(file_path, "rb") as f:

            f.seek(offset)

            # Start performance measurement
            # immediately before payload transfer.
            if offset < file_size:
                transfer_start = time.perf_counter()

            while chunk := f.read(CHUNK_SIZE):

                original_chunk = chunk
                chunk_to_send = chunk

                # --------------------------------------------
                # DEBUG: Corrupt one byte
                # --------------------------------------------

                if corrupt and not corruption_done:

                    corrupted = bytearray(chunk)

                    corrupted[0] ^= 0xFF

                    chunk_to_send = bytes(corrupted)

                    corruption_done = True

                    print(
                        "\nDEBUG: Corrupted one byte "
                        "before sending"
                    )

                writer.write(chunk_to_send)

                await writer.drain()

                # IMPORTANT:
                # Hash ORIGINAL data, not corrupted data.
                update_hash(
                    hasher,
                    original_chunk,
                )

                sent += len(chunk)
                chunks_sent += 1

                print(
                    f"Sent: {sent}/{file_size} bytes"
                )

                # --------------------------------------------
                # DEBUG: Intentional interruption
                # --------------------------------------------

                if (
                    fail_after_chunks > 0
                    and chunks_sent >= fail_after_chunks
                ):

                    print(
                        "\nDEBUG: Simulating "
                        "client interruption"
                    )

                    writer.close()
                    await writer.wait_closed()

                    raise ConnectionError(
                        "Intentional transfer interruption"
                    )

            if transfer_start is not None:
                transfer_end = time.perf_counter()

        # ====================================================
        # STEP 6: Calculate transfer metrics
        # ====================================================

        bytes_transferred = file_size - offset

        if (
            transfer_start is not None
            and transfer_end is not None
        ):
            transfer_duration = (
                transfer_end - transfer_start
            )
        else:
            transfer_duration = 0.0

        throughput_mbps = (
            calculate_throughput_mbps(
                bytes_transferred,
                transfer_duration,
            )
        )

        print(
            f"\nTransfer duration: "
            f"{transfer_duration:.6f} seconds"
        )

        print(
            f"Application throughput: "
            f"{throughput_mbps:.3f} Mbps"
        )

        # ====================================================
        # STEP 7: Calculate final SHA-256
        # ====================================================

        final_hash = get_digest(hasher)

        print(
            f"Client SHA-256: {final_hash}"
        )

        # ====================================================
        # STEP 8: Send final hash
        # ====================================================

        writer.write(
            pack_final_hash(final_hash)
        )

        await writer.drain()

        # ====================================================
        # STEP 9: Receive server result
        # ====================================================

        status_message = await reader.readexactly(2)

        status = unpack_status(
            status_message
        )

        if status != STATUS_OK:

            raise ValueError(
                f"Server rejected transfer. "
                f"Status={status}"
            )

        print(
            "\nTransfer completed successfully!"
        )

        # ====================================================
        # STEP 10: Save metrics
        # ====================================================

        append_result(
            condition=condition,
            transfer_id=transfer_id,
            file_size=file_size,
            resume_offset=offset,
            bytes_transferred=bytes_transferred,
            duration_seconds=transfer_duration,
            throughput_mbps=throughput_mbps,
            rtt_ms=rtt_ms,
        )

        print(
            f"Metrics saved to {condition} result."
        )

    finally:

        if not writer.is_closing():

            writer.close()

            await writer.wait_closed()


# ============================================================
# Retry wrapper
# ============================================================

async def transfer_with_retry(
    file_path,
    retries,
    fail_after_chunks,
    transfer_id,
    corrupt,
    condition,
):

    print(
        f"Using transfer ID: {transfer_id}"
    )

    async def operation():

        return await transfer_once(
            file_path,
            transfer_id,
            fail_after_chunks,
            corrupt,
            condition,
        )

    return await retry(
        operation,
        retries=retries,
        base_delay=1,
        max_delay=8,
    )


# ============================================================
# Main
# ============================================================

async def main():

    parser = argparse.ArgumentParser(
        description="Reliable TCP file transfer client"
    )

    parser.add_argument(
        "file",
        help="File to transfer",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=4,
        help="Maximum number of attempts",
    )

    parser.add_argument(
        "--fail-after",
        type=int,
        default=0,
        help=(
            "Intentionally interrupt after N chunks "
            "for resume testing"
        ),
    )

    parser.add_argument(
        "--transfer-id",
        default=None,
        help="Existing transfer ID to resume",
    )

    parser.add_argument(
        "--corrupt",
        action="store_true",
        help="Corrupt one byte for checksum testing",
    )

    parser.add_argument(
        "--condition",
        choices=[
            "baseline",
            "delay",
            "loss",
            "delay_loss",
        ],
        default="baseline",
        help="Network experiment condition",
    )

    args = parser.parse_args()

    transfer_id = (
        args.transfer_id
        if args.transfer_id
        else uuid.uuid4().hex
    )

    await transfer_with_retry(
        args.file,
        args.retries,
        args.fail_after,
        transfer_id,
        args.corrupt,
        args.condition,
    )


if __name__ == "__main__":
    asyncio.run(main())