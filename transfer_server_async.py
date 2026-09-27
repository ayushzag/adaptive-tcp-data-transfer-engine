import asyncio
import os
from pathlib import Path

from protocol import (
    PING,
    PONG,
    START_TRANSFER,
    read_transfer_start,
    pack_resume_offset,
    read_final_hash,
    pack_status,
    pack_pong,
    STATUS_OK,
    STATUS_CHECKSUM_MISMATCH,
    STATUS_INVALID_REQUEST,
)

from integrity import (
    create_hasher,
    update_hash,
    get_digest,
)


HOST = "127.0.0.1"
PORT = 5050

CHUNK_SIZE = 4096

TRANSFER_DIR = Path("transfers")
TRANSFER_DIR.mkdir(exist_ok=True)


# ============================================================
# Transfer ID safety
# ============================================================

def sanitize_transfer_id(transfer_id):

    safe_id = "".join(
        c
        for c in transfer_id
        if c.isalnum() or c in "-_"
    )

    if not safe_id:
        raise ValueError(
            "Invalid transfer ID"
        )

    return safe_id[:64]


def get_paths(transfer_id):

    safe_id = sanitize_transfer_id(
        transfer_id
    )

    part_path = (
        TRANSFER_DIR
        / f"{safe_id}.part"
    )

    final_path = (
        TRANSFER_DIR
        / f"{safe_id}.bin"
    )

    return part_path, final_path


# ============================================================
# Handle client
# ============================================================

async def handle_client(reader, writer):

    peer = writer.get_extra_info(
        "peername"
    )

    print(
        f"[{peer}] Client connected"
    )

    try:

        # ====================================================
        # STEP 1: Read first message type
        # ====================================================

        first_byte = await reader.readexactly(1)

        message_type = first_byte[0]

        # ====================================================
        # DAY 5: RTT PING
        # ====================================================

        if message_type == PING:

            writer.write(
                pack_pong()
            )

            await writer.drain()

            print(
                f"[{peer}] PING -> PONG"
            )

            # Keep same TCP connection alive.
            first_byte = await reader.readexactly(1)

            message_type = first_byte[0]

        # ====================================================
        # STEP 2: Validate START_TRANSFER
        # ====================================================

        if message_type != START_TRANSFER:

            raise ConnectionError(
                "Expected START_TRANSFER message"
            )

        # Reconstruct complete START_TRANSFER header.
        transfer_id, file_size = (
            await read_transfer_start(
                reader,
                first_byte=first_byte,
            )
        )

        print(
            f"[{peer}] Transfer ID: "
            f"{transfer_id}"
        )

        print(
            f"[{peer}] Expected size: "
            f"{file_size} bytes"
        )

        part_path, final_path = get_paths(
            transfer_id
        )

        # ====================================================
        # STEP 3: Find existing partial transfer
        # ====================================================

        if part_path.exists():

            existing_size = (
                part_path.stat().st_size
            )

        else:

            existing_size = 0

        if existing_size > file_size:

            print(
                f"[{peer}] Existing .part file "
                f"is larger than requested "
                f"file. Resetting."
            )

            part_path.unlink()

            existing_size = 0

        print(
            f"[{peer}] Resume offset: "
            f"{existing_size} bytes"
        )

        # Tell client how many bytes we already have.
        writer.write(
            pack_resume_offset(
                existing_size
            )
        )

        await writer.drain()

        # ====================================================
        # STEP 4: Prepare SHA-256
        # ====================================================

        hasher = create_hasher()

        # Existing partial file must be part of
        # final SHA-256 calculation.

        if existing_size > 0:

            print(
                f"[{peer}] Hashing existing "
                f"partial file..."
            )

            with open(
                part_path,
                "rb",
            ) as f:

                while chunk := f.read(
                    CHUNK_SIZE
                ):

                    update_hash(
                        hasher,
                        chunk,
                    )

        # ====================================================
        # STEP 5: Receive remaining data
        # ====================================================

        received = existing_size

        with open(
            part_path,
            "ab",
        ) as f:

            while received < file_size:

                remaining = (
                    file_size - received
                )

                chunk = await reader.read(
                    min(
                        CHUNK_SIZE,
                        remaining,
                    )
                )

                if not chunk:

                    raise ConnectionError(
                        "Client disconnected "
                        "during transfer"
                    )

                f.write(chunk)

                update_hash(
                    hasher,
                    chunk,
                )

                received += len(chunk)

                print(
                    f"[{peer}] "
                    f"Received "
                    f"{received}/{file_size} "
                    f"bytes"
                )

        # ====================================================
        # STEP 6: Receive client SHA-256
        # ====================================================

        server_hash = get_digest(
            hasher
        )

        client_hash = (
            await read_final_hash(
                reader
            )
        )

        print(
            f"[{peer}] Server SHA-256: "
            f"{server_hash}"
        )

        print(
            f"[{peer}] Client SHA-256: "
            f"{client_hash}"
        )

        # ====================================================
        # STEP 7: Verify checksum
        # ====================================================

        if server_hash != client_hash:

            print(
                f"[{peer}] "
                f"CHECKSUM MISMATCH"
            )

            if part_path.exists():
                part_path.unlink()

            writer.write(
                pack_status(
                    STATUS_CHECKSUM_MISMATCH
                )
            )

            await writer.drain()

            return

        # ====================================================
        # STEP 8: Transfer successful
        # ====================================================

        os.replace(
            part_path,
            final_path,
        )

        print(
            f"[{peer}] "
            f"Transfer completed successfully"
        )

        print(
            f"[{peer}] Saved to: "
            f"{final_path}"
        )

        writer.write(
            pack_status(
                STATUS_OK
            )
        )

        await writer.drain()

    # ========================================================
    # Expected incomplete transfer
    # ========================================================

    except asyncio.IncompleteReadError:

        # Keep .part file so next connection can resume.

        print(
            f"[{peer}] "
            f"Client disconnected early"
        )

    # ========================================================
    # Connection errors
    # ========================================================

    except ConnectionError as e:

        print(
            f"[{peer}] "
            f"Connection error: {e}"
        )

    # ========================================================
    # Invalid request
    # ========================================================

    except ValueError as e:

        print(
            f"[{peer}] "
            f"Invalid request: {e}"
        )

        try:

            writer.write(
                pack_status(
                    STATUS_INVALID_REQUEST
                )
            )

            await writer.drain()

        except Exception:
            pass

    # ========================================================
    # Unexpected error
    # ========================================================

    except Exception as e:

        print(
            f"[{peer}] "
            f"Unexpected error: {e}"
        )

    # ========================================================
    # Cleanup
    # ========================================================

    finally:

        writer.close()

        await writer.wait_closed()

        print(
            f"[{peer}] "
            f"Connection closed"
        )


# ============================================================
# Main server
# ============================================================

async def main():

    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT,
    )

    print(
        f"Reliable async server listening "
        f"on {HOST}:{PORT}"
    )

    async with server:

        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())