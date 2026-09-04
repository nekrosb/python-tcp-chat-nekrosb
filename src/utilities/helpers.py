import json

from classes.client.console import Console

MAX_NICKNAME_SIZE = 32
MAX_MESSAGE_SIZE = 4096


def shutdown_server(socket, stop_event):
    stop_event.set()
    socket.close()


def users_table(users: dict):
    new_list_of_users = {}

    for nik, client_info in users.items():
        host, port = client_info[1]
        new_list_of_users[nik] = f"{host}:{port}"

    return new_list_of_users


def build_msg(message_type, data):
    msg = {"type": message_type, "data": data}

    return (json.dumps(msg) + "\n").encode("utf-8")


def decode_message(data):
    return json.loads(data)


def writer_msg(data):
    msg = decode_message(data)

    if msg["type"] == "broadcast":
        Console.brotcast_msg(msg["data"])
    elif msg["type"] == "users":
        Console.users_table(msg["data"])


def send_broadcast_msg(socket, msg, list_users, clients_lock):
    disconnected_users = []

    with clients_lock:
        users = list(list_users.items())

    for username, user in users:
        user_socket = user[0]

        if user_socket == socket:
            continue

        try:
            user_socket.sendall(build_msg("broadcast", msg))

        except (ConnectionResetError, BrokenPipeError, OSError):
            disconnected_users.append(username)

    with clients_lock:
        for username in disconnected_users:
            user = list_users.get(username)
            if user is None or user[0] is socket:
                continue

            user_socket = user[0]

            try:
                user_socket.close()
            except OSError:
                pass

            del list_users[username]
