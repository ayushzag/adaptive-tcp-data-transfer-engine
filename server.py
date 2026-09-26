import socket
from xmlrpc import client #python ki built in socket library import

HOST = "127.0.0.1" #local host - isi computer pr server chalega
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Ek socket object create kar raha hai.
#IPv4 use karenge. --> AF.INET
#socket.SOCK_STREAM --> TCP socket.
# Allows quick restart of the server
#"IPv4 TCP socket bana do."


server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Ye server ko quickly restart karne mein help karta hai.
#SO_REUSEADDR = allow appropriate reuse of local address

server.bind((HOST, PORT))#"Mera server is IP + port par available hoga." ---> Ab socket ko address assign kar rahe hain:
server.listen(5)  #Ab server incoming connections ke liye listen karna start karta hai. 
#5 backlog hai — roughly kitni pending connection requests queue mein wait kar sakti hain.
#listen() client se baat nahi kar raha. Bas bol raha hai: "Main incoming connection accept karne ke liye ready hoon"

print(f"Server listening on {HOST}:{PORT}")

client_socket, address = server.accept() #accept() incoming client connection ka wait karta hai.
#Jab client: client.connect(("127.0.0.1", 5000)) karta hai, server ka accept() return karta hai.
#client_socket → is particular client ke saath communication socket address → client ka address

print(f"Connected by {address}")

try: ##Communication code ko exception handling ke andar rakh rahe hain. Agar kuch error aaye, finally phir bhi execute hoga.
    data = client_socket.recv(1024) #Server client se data receive kar raha hai. 1024 bytes maximum recieve kr skta hai.

    if data: #Check kar rahe hain ki actually data mila ya nahi.
        print(f"Client: {data.decode()}") #Socket se data bytes mein aata hai. 
        #decode() converts bytes → normal string.

        client_socket.sendall(b"ACK: Message received") #b means python bytes, sendall() Data ko poora send karne ki koshish karta hai.

finally:
    client_socket.close()
    server.close()
    print("Server closed")