from datetime import datetime
import socket
import threading

def main():
    clients = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clients.bind(('0.0.0.0', 12345))
    clients.listen(5    )
    # add logs leiter
    print("server is run and listening on port 12345 \n ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    while True:
        client_socket, addr = clients.accept()
        # add logs leiter
        print(f"Connection from {addr} has been established.")
        threading.Thread(target=handle_client, args=(client_socket,)).start()


def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                client_socket.send("goodbye".encode('utf-8'))
                # add logs leiter
                print("Client disconnected.")
                break
            print(f"Received message: {message}")
            client_socket.sendall(f"Echo: {message}")
        except ConnectionResetError:
            # add logs leiter
            print("Client disconnected abruptly.")
            break

    print("Client disconnected.")
    client_socket.close()


main()