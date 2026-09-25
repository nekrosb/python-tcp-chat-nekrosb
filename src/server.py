import logging
import socket
import threading
from utilities.commands import server_commands as commands

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
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    log.info(f"Server listening on {host}:{port}")
    stop_event = threading.Event()
    nik_lock = threading.Lock()
    niks = set()
    chat_history = []
    history_lock = threading.Lock()
    list_of_clients = {}

    while not stop_event.is_set():
        server_socket.settimeout(1.0)
        try:
            client, addr = server_socket.accept()
            log.info(f"Connection from {addr} and client {client}")

            


            client_thread = threading.Thread(
                target=handle_client,
                args=(
                    client,
                    addr,
                    stop_event,
                    log,
                    nik_lock,
                    niks,
                    list_of_clients,
                    chat_history,
                    history_lock,
                ),
                daemon=True,
            )
            client_thread.start()
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            log.info("Server shutting down...")
            helpers.shutdown_server(server_socket, stop_event)
            break

        except OSError as e:
            log.error(f"Socket error: {e}")
            helpers.shutdown_server(server_socket, stop_event)
            break



def handle_client(
    client_socket,
    addr,
    stop_event,
    log,
    nik_lock,
    niks,
    list_of_clients,
    chat_history,
    history_lock,
):
    log.info(f"Handling client {addr}")

    with nik_lock:
        users = dict(list_of_clients)

    if users:
        client_socket.sendall(helpers.build_msg("users", helpers.users_table(users)))


    nickname = None

    # Nickname selection
    client_socket.settimeout(30.0)
    buffer = b""

    while not stop_event.is_set():
        try:
            client_socket.sendall(
                helpers.build_msg("broadcast", "Please provide a nickname:")
            )

            while b"\n" not in buffer:
                data = client_socket.recv(1024)
                if not data:
                    client_socket.close()
                    return
                buffer += data
                if b"\n" not in buffer and len(buffer) > helpers.MAX_NICKNAME_SIZE:
                    print(f"baffer {len(buffer)} max {helpers.MAX_NICKNAME_SIZE}")
                    log.warning(f"Client {addr} sent an oversized nickname")
                    client_socket.close()
                    return

            raw_nickname, buffer = buffer.split(b"\n", 1)
            if len(raw_nickname) > helpers.MAX_NICKNAME_SIZE:
                log.warning(f"Client {addr} sent an oversized nickname")
                client_socket.close()
                return
            nickname = raw_nickname.decode("utf-8").strip()

            try:
                nickname_message = helpers.decode_message(nickname)
            except (TypeError, ValueError):
                nickname_message = None
            if (
                isinstance(nickname_message, dict)
                and nickname_message.get("type") == "broadcast"
                and isinstance(nickname_message.get("data"), str)
            ):
                nickname = nickname_message["data"].strip()

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
                list_of_clients[nickname] = [client_socket, addr, threading.Lock()]

            # No lock here — other clients can select nicknames.
            client_socket.sendall(
                helpers.build_msg(
                    "broadcast",
                    "Nickname accepted. Welcome to the chat!"
                )
            )
            # Keep one handler so command state follows nickname changes.
            command_handler = commands.ServerCommand(
                client_socket,
                list_of_clients,
                niks,
                nik_lock,
                log,
                nickname,
                history_lock,
            )
            # Notify other users that this user has joined the chat.
            command_handler.send_broadcast_msg(f"{nickname} has joined the chat.")

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

        except UnicodeDecodeError:
            log.warning(f"Client {addr} sent an invalid nickname")
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

    helpers.send_history(client_socket, chat_history, history_lock)
    # Chat loop
    while not stop_event.is_set():
        try:
            data = client_socket.recv(1024)

            if not data:
                log.info(f"Client {addr} disconnected")
                break

            buffer += data

            should_continue = True
            while b"\n" in buffer:
                raw_message, buffer = buffer.split(b"\n", 1)
                if len(raw_message) > helpers.MAX_MESSAGE_SIZE:
                    log.warning(f"Client {addr} sent an oversized message")
                    should_continue = False
                    break
                message = raw_message.decode("utf-8").strip()
                if not message:
                    continue

                log.info(f"Received data from {addr}: {message}")

                if not command_handler.handle_command(message, chat_history):
                    should_continue = False
                    break

            if not should_continue:
                break
            if len(buffer) > helpers.MAX_MESSAGE_SIZE:
                log.warning(f"Client {addr} sent an oversized message")
                break
        except socket.timeout:
            continue

        except ConnectionResetError:
            log.warning(f"Connection reset by {addr}")
            break

        except UnicodeDecodeError:
            log.warning(f"Client {addr} sent invalid UTF-8 data")
            break

        except OSError as e:
            log.error(f"Error handling client {addr}: {e}")
            break

    # Cleanup
    nickname = command_handler.nickname
    with nik_lock:
        if nickname in niks:
            niks.remove(nickname)

        if nickname in list_of_clients and list_of_clients[nickname][0] is client_socket:
            del list_of_clients[nickname]

    command_handler.send_broadcast_msg(f"{nickname} has left the chat.")

    client_socket.close()
    log.info(f"Connection with {addr} closed")
main()
