import logging
import socket
import threading

from config import pars_conf
from utilities import helpers
from utilities.logging_conf import setup_logging

setup_logging("server")


def main():
    args = pars_conf()
    host = args.host
    port = args.port
    log = logging.getLogger(__name__)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    log.info(f"Server listening on {host}:{port}")
    stop_event = threading.Event()
    nik_lock = threading.Lock()
    niks = set()
    list_of_clients = {}

    while not stop_event.is_set():
        server_socket.settimeout(1.0)
        try:
            client, addr = server_socket.accept()
            log.info(f"Connection from {addr} and client {client}")

            client_thread = threading.Thread(
                target=handle_client,
                args=(client, addr, stop_event, log, nik_lock, niks, list_of_clients),
                daemon=True,
            )
            client_thread.start()
        except TimeoutError:
            continue
        except KeyboardInterrupt:
            log.info("Server shutting down...")
            helpers.shutdown_server(server_socket, stop_event)
            break

        except OSError as e:
            logging.log.error(f"Socket error: {e}")
            helpers.shutdown_server(server_socket, stop_event)
            break


def handle_client(
    client_socket, addr, stop_event, log, nik_lock, niks, list_of_clients
):
    log.info(f"Handling client {addr}")

    nickname = None

    # Nickname selection
    client_socket.settimeout(30.0)

    while not stop_event.is_set():
        try:
            client_socket.sendall(
                helpers.build_msg("broadcast", "Please provide a nickname:")
            )

            nickname = client_socket.recv(1024).decode().strip()

            if not nickname:
                log.warning(f"Client {addr} did not provide a nickname")
                continue

            # Lock only protects checking/adding nickname.
            with nik_lock:
                if nickname in niks:
                    client_socket.sendall(
                        helpers.build_msg(
                            "broadcast",
                            "Nickname already taken. Please choose another.",
                        )
                    )
                    nickname = None
                    continue

                niks.add(nickname)
                list_of_clients[nickname] = [client_socket, addr]

            # No lock here — other clients can select nicknames.
            client_socket.sendall(
                helpers.build_msg(
                    "broadcast",
                    "Nickname accepted. Welcome to the chat!"
                )
            )

            helpers.send_broadcast_msg(
                client_socket,
                f"{nickname} has joined the chat.",
                list_of_clients,
            )

            log.info(f"Client {addr} set nickname to {nickname}")
            break

        except socket.timeout:
            log.warning(f"Client {addr} timed out during nickname selection")
            client_socket.close()
            return

        except ConnectionResetError:
            log.warning(f"Connection reset by {addr} during nickname selection")
            client_socket.close()
            return

        except OSError as e:
            log.error(f"Error handling client {addr}: {e}")
            client_socket.close()
            return

    if nickname is None:
        client_socket.close()
        return

    client_socket.settimeout(1.0)

    # Chat loop
    while not stop_event.is_set():
        try:
            data = client_socket.recv(1024)

            if not data:
                log.info(f"Client {addr} disconnected")
                break

            message = data.decode().strip()

            if message:
                log.info(f"Received data from {addr}: {message}")
                helpers.send_broadcast_msg(
                    client_socket,
                    message,
                    list_of_clients,
                )

        except socket.timeout:
            continue

        except ConnectionResetError:
            log.warning(f"Connection reset by {addr}")
            break

        except OSError as e:
            log.error(f"Error handling client {addr}: {e}")
            break

    # Cleanup
    with nik_lock:
        if nickname in niks:
            niks.remove(nickname)

        if nickname in list_of_clients:
            del list_of_clients[nickname]

    helpers.send_broadcast_msg(
        client_socket,
        f"{nickname} has left the chat.",
        list_of_clients,
    )

    client_socket.close()
    log.info(f"Connection with {addr} closed")
main()
