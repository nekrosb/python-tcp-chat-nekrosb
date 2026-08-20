import logging
import socket
import threading

from config import pars_conf
from utilities import helpers
from utilities.logging_conf import setup_logging

setup_logging("client")


def main():
    args = pars_conf()
    host = args.host
    port = args.port
    log = logging.getLogger(__name__)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    stop_event = threading.Event()
    try:
        client_socket.connect((host, port))
        log.info(f"Connected to server at {host}:{port}")

        receive_thread = threading.Thread(
            target=receive_messages, args=(client_socket, stop_event, log)
        )
        receive_thread.start()

        while not stop_event.is_set():
            message = input("Enter message (or '/exit' to quit): ")
            if message.lower().strip() == "/exit":
                log.info("Exiting client...")
                helpers.shutdown_server(client_socket, stop_event)
                break

            client_socket.sendall(message.encode())
    except ConnectionRefusedError as e:
        log.error(f"Could not connect to server at {host}:{port} \n {e}")
        helpers.shutdown_server(client_socket, stop_event)
    except OSError as e:
        log.error(f"An error occurred: {e}")
        helpers.shutdown_server(client_socket, stop_event)
    except KeyboardInterrupt:
        log.info("Client shutting down...")
        helpers.shutdown_server(client_socket, stop_event)

    client_socket.close()


def receive_messages(client_socket, stop_event, log):
    while not stop_event.is_set():
        client_socket.settimeout(1.0)
        try:
            data = client_socket.recv(1024)
            if not data:
                log.info("Server closed the connection")
                stop_event.set()
                break
            print(f"Received: {data.decode()}")

        except TimeoutError:
            continue
        except ConnectionResetError:
            log.warning("Connection reset by server")
            stop_event.set()
            break
        except OSError as e:
            log.error(f"Error receiving data: {e}")
            stop_event.set()
            break


main()
