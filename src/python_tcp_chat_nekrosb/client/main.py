import logging
import socket
import threading

from rich import print


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename='client.log', filemode='a')
    server_ip = input("Enter server IP address: ")
    server_port = int(input("Enter server port: "))
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    stop_event = threading.Event()


    try:
        client_socket.connect((server_ip, server_port))
        print(f"[bold green]Connected to server at {server_ip}:{server_port}[/bold green]")
        logging.info(f"Connected to server at {server_ip}:{server_port}")
        resivMsg = threading.Thread(target=receive_messages, args=(client_socket, stop_event))
        resivMsg.start()

        while not stop_event.is_set():
            message = input("Enter message (or type 'exit' to quit): ")
            if message.lower().strip() == '/exit':
                stop_event.set()
                break
            client_socket.sendall(message.encode())
            logging.info(f"Sent message: {message}")



    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"[bold red]Error: {e}[/bold red]")
    except KeyboardInterrupt:
        logging.info("Client interrupted by user")
        print("[bold yellow]Client interrupted by user[/bold yellow]")
    finally:
        client_socket.close()
        logging.info("Client socket closed")
        print("[bold yellow]Disconnected from server[/bold yellow]")

def receive_messages(client_socket, stop_event):
    while not stop_event.is_set():
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"[bold blue]Received: {data.decode()}[/bold blue]")
            logging.info(f"Received message: {data.decode()}")
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            print(f"[bold red]Error receiving message: {e}[/bold red]")
            break   


if __name__ == "__main__":
    main()