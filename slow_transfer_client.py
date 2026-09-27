import asyncio
import os
import hashlib

from protocol import pack_header


HOST = "127.0.0.1"
PORT = 5050
FILE = "test_large.bin"


async def main():

    reader, writer = await asyncio.open_connection(
        HOST,
        PORT
    )

    print("Slow client connected")

    file_size = os.path.getsize(FILE)

    print(f"File size: {file_size} bytes")

    # -----------------------------------------
    # STEP 1: Send 8-byte header
    # -----------------------------------------

    header = pack_header(file_size)

    writer.write(header)
    await writer.drain()

    print("Header sent")

    # -----------------------------------------
    # STEP 2: Send file slowly
    # -----------------------------------------

    file_hash = hashlib.sha256()

    with open(FILE, "rb") as f:

        while chunk := f.read(4096):

            writer.write(chunk)
            await writer.drain()

            file_hash.update(chunk)

            # jaan-bujhkar slow
            await asyncio.sleep(0.01)

    client_hash = file_hash.hexdigest()

    print(f"Slow client SHA-256: {client_hash}")
    print("Slow file sent successfully")

    writer.close()
    await writer.wait_closed()

    print("Slow client closed")


asyncio.run(main())