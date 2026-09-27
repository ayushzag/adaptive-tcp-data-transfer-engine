import asyncio
import hashlib

from protocol import unpack_header


HOST = "127.0.0.1"
PORT = 5050


async def handle_client(reader, writer):
    peer = writer.get_extra_info("peername") #Ye client ka address/port nikal raha hai.
    print(f"Client connected: {peer}")

    try:
        # -----------------------------------------
        # STEP 1: Receive exact 8-byte header
        # -----------------------------------------

        header = await reader.readexactly(8) #8 bytes ka header receive kar rahe hain.

        # Header -> actual file size
        file_size = unpack_header(header) #Header ke 8 bytes ke andar jo file size encoded tha, usko normal integer bana rahe hain.

        print(f"[{peer}] Incoming file size: {file_size} bytes")

        # -----------------------------------------
        # STEP 2: Receive file
        # -----------------------------------------

        received = 0 #Ab tak kitne bytes aa chuke hain?

        file_hash = hashlib.sha256() #Jo bytes aaye hain unka SHA-256 continuously calculate karo.
        output_file = f"received_{peer[1]}.txt" #Ye humne multiple clients ke test ke liye add kiya. Warna sab clients same received.txt ko overwrite kar sakte the.

        with open(output_file, "wb") as f: #wb = write binary mode. Kyunki file binary data ho sakta hai.

            while received < file_size: #Jab tak poori expected file nahi aa jaati, receive karte raho.

                remaining = file_size - received #Kitne bytes abhi bache hain?

                chunk = await reader.read( #4096 bytes ka chunk receive karo, ya jo bhi remaining hain, whichever is smaller.
                    min(4096, remaining)
                )

                if not chunk:
                    raise ConnectionError(
                        "Client closed connection during file transfer"
                    )

                f.write(chunk) #Jo chunk network se aaya, disk par write kar diya.

                file_hash.update(chunk) #Same data SHA-256 calculation mein bhi add kar diya.

                received += len(chunk) # Total received bytes update kar diya.

                print(
                    f"[{peer}] Received: "
                    f"{received}/{file_size} bytes"
                )

        # -----------------------------------------
        # STEP 3: Final checksum
        # -----------------------------------------

        server_hash = file_hash.hexdigest() #Transfer complete hone ke baad final hash.

        print(f"[{peer}] Server SHA-256: {server_hash}")
        print(f"[{peer}] File received successfully")

    except asyncio.IncompleteReadError: #Asyncio mein agar client ne connection close kar diya aur expected bytes receive nahi hue, to ye exception aayega.
        print(f"[{peer}] Client closed connection early")

    except ConnectionError as e: #Agar connection mein koi problem aaye, jaise client ne beech mein connection close kar diya.
        print(f"[{peer}] Connection error: {e}")

    finally:
        writer.close()
        await writer.wait_closed()

        print(f"[{peer}] Connection closed")


async def main(): #main function

    server = await asyncio.start_server( #"5050 par server start karo, aur jab client aaye to handle_client use karo."
        handle_client,
        HOST,
        PORT
    )

    print(f"Async server listening on {HOST}:{PORT}")

    async with server:
        await server.serve_forever() #Server chalta rahe aur incoming clients handle karta rahe.


asyncio.run(main())