import socket

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
    # Hume pata hai client Day 1 mein kitne bytes bhej raha hai.
    # Isliye exact utne hi bytes receive karenge.
    message = b"Hello from client"

    data = recv_exact(client_socket, len(message))
    # TCP mein ek send() = ek recv() guaranteed nahi hota.
    # Isliye recv_exact() loop karke poora message receive karega.

    print(f"Client: {data.decode()}")
    # Socket se data bytes mein aata hai.
    # decode() converts bytes → normal string.


    client_socket.sendall(b"ACK: Message received")
    # b means Python bytes.
    # sendall() poora data send karne ki koshish karta hai.


except ConnectionError as e:
    # Agar client beech mein connection close kar de ya connection mein problem aaye.
    print(f"Connection error: {e}")


finally:
    client_socket.close()
    server.close()
    print("Server closed")