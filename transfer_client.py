import socket
import os
import hashlib

from protocol import pack_header


HOST = "127.0.0.1"
PORT = 5050
FILE = "test.txt"


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Ek IPv4 TCP socket create kar raha hai.
# AF_INET -> IPv4
# SOCK_STREAM -> TCP


client.settimeout(5)
# Agar connection/operation 5 seconds ke andar complete nahi hota,
# to timeout exception aa sakta hai.


try:
    client.connect((HOST, PORT))
    # Client server se connection establish kar raha.
    # Conceptually yahan TCP 3-way handshake hota hai:
    # SYN → SYN-ACK → ACK

    print("Connected to server")


    # -----------------------------------------
    # STEP 1: File ka size nikalo
    # -----------------------------------------

    file_size = os.path.getsize(FILE)

    print(f"File size: {file_size} bytes")


    # -----------------------------------------
    # STEP 2: File size ka header banao
    # -----------------------------------------

    header = pack_header(file_size)

    # File size ko 8-byte bytes format mein convert kiya.
    # Ye header server ko pehle bhejenge.


    # -----------------------------------------
    # STEP 3: Header server ko bhejo
    # -----------------------------------------

    client.sendall(header)

    print("Header sent")


    # -----------------------------------------
    # STEP 4: File ko chunks mein bhejo
    # -----------------------------------------

    file_hash = hashlib.sha256()
    # SHA-256 hash object.
    # Har chunk ke bytes isme add honge.


    with open(FILE, "rb") as f:
        # "rb" = read binary
        # File ko binary mode mein open kar rahe hain.

        while chunk := f.read(4096):
            # File ko 4096 bytes ke small chunks mein read kar rahe hain.
            # Poora file ek saath memory mein load nahi kar rahe.

            client.sendall(chunk)
            # Current chunk server ko bhej rahe hain.

            file_hash.update(chunk)
            # Same chunk ko SHA-256 hash mein add kar rahe hain.


    # -----------------------------------------
    # STEP 5: Final checksum nikalo
    # -----------------------------------------

    client_hash = file_hash.hexdigest()

    print(f"Client SHA-256: {client_hash}")

    print("File sent successfully")


except ConnectionRefusedError:
    # Agar server running nahi hai ya given port par listen nahi kar raha.
    print("Connection refused: Is the server running?")


except socket.timeout:
    # Agar 5 seconds ke andar socket operation complete nahi hua.
    print("Connection timed out")


except ConnectionError as e:
    # Agar connection mein koi problem aaye.
    print(f"Connection error: {e}")


finally:
    client.close()
    # Communication complete hone ke baad client socket close kar rahe hain.

    print("Client closed")