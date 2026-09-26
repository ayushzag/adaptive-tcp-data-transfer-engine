import socket

HOST = "127.0.0.1"
PORT = 5050


# Ye function exact number of bytes receive karne ke liye use hoga.
# TCP byte stream hai, isliye ek recv() mein poora data milna guaranteed nahi hai.
def recv_exact(sock, size):
    data = bytearray()

    # Jab tak expected size ka data receive nahi ho jata tab tak receive karte raho.
    while len(data) < size:
        chunk = sock.recv(size - len(data))

        # Agar server ne connection close kar diya before complete data,
        # to connection properly complete nahi hua.
        if not chunk:
            raise ConnectionError("Server closed connection early")

        data.extend(chunk)

    return bytes(data)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Ek socket object create kar raha hai.
# IPv4 use karenge. --> AF_INET
# socket.SOCK_STREAM --> TCP socket.
# "IPv4 TCP socket bana do."


client.settimeout(5)
# Agar connection/operation allowed time mein complete nahi hota,
# timeout exception aa sakta hai.
# Yahan 5 seconds ke baad wait karna band kar denge.


try:
    client.connect((HOST, PORT))
    # Client server se connection establish kar raha.
    # Yahin conceptually TCP 3-way handshake hota hai:
    # SYN → SYN-ACK → ACK

    print("Connected to server")


    message = b"Hello from client"

    client.sendall(message)
    # Client server ko bytes bhej raha hai.
    # sendall() poora data send karne ki koshish karta hai.


    expected_ack = b"ACK: Message received"

    data = recv_exact(client, len(expected_ack))
    # Ab client server ka response receive kar raha hai.
    # Ek recv() mein poora ACK milna guaranteed nahi hai,
    # isliye recv_exact() loop karke poora ACK receive karega.


    print(f"Server: {data.decode()}")
    # Socket se data bytes mein aata hai.
    # decode() converts bytes → normal string.


except ConnectionRefusedError:
    # Agar server running nahi hai ya given port par listen nahi kar raha.
    print("Connection refused: Is the server running?")


except socket.timeout:
    # Agar 5 seconds ke andar socket operation complete nahi hua.
    print("Connection timed out")


except ConnectionError as e:
    # Agar connection beech mein close/error ho jaye.
    print(f"Connection error: {e}")


finally:
    client.close()
    # Communication complete hone ke baad client socket close kar rahe hain.

    print("Client closed")