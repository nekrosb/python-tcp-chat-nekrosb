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

    while not stop_event.is_set():
        server_socket.settimeout(1.0)
        try:
            client, addr = server_socket.accept()
            log.info(f"Connection from {addr} and client {client}")

            client_thread = threading.Thread(
                target=handle_client, args=(client, addr, stop_event, log)
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


def handle_client(client_socket, addr, stop_event, log):
    log.info(f"Handling client {addr}")
    print(f"clint {client_socket} connected from {addr}")

    client_socket.settimeout(1.0)
    while not stop_event.is_set():
        try:
            data = client_socket.recv(1024)
            if not data:
                log.info(f"Client {addr} disconnected")
                break
            log.info(f"Received data from {addr}: {data.decode()}")
            client_socket.sendall(data)

        except TimeoutError:
            continue
        except ConnectionResetError:
            log.warning(f"Connection reset by {addr}")
            break
        except Exception as e:
            log.error(f"Error handling client {addr}: {e}")
            break
    client_socket.close()
    log.info(f"Connection with {addr} closed")


main()
