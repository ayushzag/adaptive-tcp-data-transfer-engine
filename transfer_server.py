import socket
import hashlib

from protocol import unpack_header


HOST = "127.0.0.1"  # local host - isi computer pr server chalega
PORT = 5050


# Ye function tab use hoga jab hume exact number of bytes receive karne hain.
# TCP byte stream hai, isliye ek recv() mein poora data milna guaranteed nahi hai.
def recv_exact(sock, size):
    data = bytearray()

    # Jab tak expected size ka data receive nahi ho jata tab tak receive karte raho.
    while len(data) < size:
        chunk = sock.recv(size - len(data))

        # Agar client ne connection close kar diya before complete data,
        # to connection properly complete nahi hua.
        if not chunk:
            raise ConnectionError("Client closed connection early")

        data.extend(chunk)

    return bytes(data)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Ek socket object create kar raha hai.
# IPv4 use karenge. --> AF_INET
# socket.SOCK_STREAM --> TCP socket.
# "IPv4 TCP socket bana do."


server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Ye server ko quickly restart karne mein help karta hai.
# SO_REUSEADDR = allow appropriate reuse of local address


server.bind((HOST, PORT))
# "Mera server is IP + port par available hoga."
# Ab socket ko address assign kar rahe hain.


server.listen(5)
# Ab server incoming connections ke liye listen karna start karta hai.
# 5 backlog hai — roughly kitni pending connection requests queue mein wait kar sakti hain.
# listen() client se baat nahi kar raha.
# Bas bol raha hai: "Main incoming connection accept karne ke liye ready hoon"


print(f"Server listening on {HOST}:{PORT}")


client_socket, address = server.accept()
# accept() incoming client connection ka wait karta hai.
# Jab client:
# client.connect(("127.0.0.1", 5000)) karta hai,
# server ka accept() return karta hai.
# client_socket → is particular client ke saath communication socket
# address → client ka address


print(f"Connected by {address}")


try:

    # -----------------------------------------
    # STEP 1: Client ka 8-byte header receive karo
    # -----------------------------------------

    header = recv_exact(client_socket, 8)

    # Header khud bhi TCP stream mein split ho sakta hai,
    # isliye direct recv(8) par depend nahi kar rahe.
    # recv_exact() ensure karega ki exactly 8 bytes milen.


    # -----------------------------------------
    # STEP 2: Header se file size nikalo
    # -----------------------------------------

    file_size = unpack_header(header)

    print(f"Incoming file size: {file_size} bytes")


    # -----------------------------------------
    # STEP 3: File receive karo
    # -----------------------------------------

    received = 0

    file_hash = hashlib.sha256()
    # Server bhi received file ka SHA-256 calculate karega.
    # Baad mein client ke hash se compare kar sakte hain.


    with open("received.txt", "wb") as f:
        # "wb" = write binary
        # Received data ko binary file ke form mein save kar rahe hain.

        while received < file_size:

            # Ab kitne bytes remaining hain?
            remaining = file_size - received

            # Maximum 4096 bytes ek baar mein receive karo.
            chunk = client_socket.recv(min(4096, remaining))


            # Agar client ne file complete hone se pehle connection close kar diya.
            if not chunk:
                raise ConnectionError(
                    "Client closed connection during file transfer"
                )


            # Received chunk ko disk par write karo.
            f.write(chunk)


            # Received chunk ko SHA-256 hash mein add karo.
            file_hash.update(chunk)


            # Total received bytes update karo.
            received += len(chunk)


            print(f"Received: {received}/{file_size} bytes")


    # -----------------------------------------
    # STEP 4: Final checksum nikalo
    # -----------------------------------------

    server_hash = file_hash.hexdigest()

    print(f"Server SHA-256: {server_hash}")


    # Day 2 mein checksum sirf calculate + log kar rahe hain.
    # Actual integrity enforcement later Day 4 mein karenge.

    print("File received successfully")


except ConnectionError as e:
    # Agar client beech mein connection close kar de ya connection mein problem aaye.
    print(f"Connection error: {e}")


finally:
    client_socket.close()
    server.close()

    print("Server closed")