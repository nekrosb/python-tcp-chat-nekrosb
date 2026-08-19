from datetime import datetime
import socket
import threading
from rich import print

def main():
    SERVER_TIMEOUT = 1.0  # seconds
    host = "0.0.0.0"
    port = 12345
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5    )

    stop_event = threading.Event()

    # add logs leiter
    print(
    f"[bold green]Server started[/bold green] \n"
    f"on [cyan]{host}:{port}[/cyan] \n"
    f"at [yellow]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]"
)

    console_thread = threading.Thread(target=console_input, args=(stop_event,), daemon=True)
    console_thread.start()

    try:
        while not stop_event.is_set():
            server.settimeout(SERVER_TIMEOUT)
            try:
                client_socket, addr = server.accept()
                # add logs leiter
                print(f"[bold blue]Connection from {addr} has been established.[/bold blue]")
                threading.Thread(target=handle_client, args=(client_socket,)).start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print(f"[bold red]Server shutting down.[/bold red] from keyboard interrupt at [yellow]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
    finally:
        server.close()

    


def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                client_socket.send(b"goodbye")
                # add logs leiter
                print("[bold red]Client disconnected.[/bold red]")
                break
            print(f"Received message: {message}")
            client_socket.sendall(b"Echo:" + message)
        except ConnectionResetError as e:
            # add logs leiter
            print("[bold red]Client disconnected unexpectedly.[/bold red] \n", e)
            break

    print("Client disconnected.")
    client_socket.close()


def console_input(stop_event):
    while not stop_event.is_set():
        command = input()

        if command.lower().strip() == "/exit":
            stop_event.set()
            print(f"[bold red]Server shutting down correctly.[/bold red] from console input at [yellow]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
            break

main()