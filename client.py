import socket

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.settimeout(5) #Agar connection/operation allowed time mein complete nahi hota, timeout exception aa sakta hai.

try: 
    client.connect((HOST, PORT)) #client server se connection establish kr rha, Yahin conceptually TCP 3-way handshake hota hai:
    print("Connected to server")

    client.sendall(b"Hello from client") #Client server ko bytes bhej raha hai:

    data = client.recv(1024) #Ab client server ka response wait/read kar raha hai.

    print(f"Server: {data.decode()}")

except ConnectionRefusedError:
    print("Connection refused: Is the server running?")

except socket.timeout: #5 seconds ke timeout ko handle kar rahe hain.
    print("Connection timed out")

finally:
    client.close()
    print("Client closed")