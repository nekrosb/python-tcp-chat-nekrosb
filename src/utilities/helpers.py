import json

from classes.client.console import Console

MAX_NICKNAME_SIZE = 320
MAX_MESSAGE_SIZE = 40960


def shutdown_server(socket, stop_event):
    stop_event.set()
    socket.close()


def users_table(users: dict):
    new_list_of_users = {}

    for nik, client_info in users.items():
        host, port = client_info[1]
        new_list_of_users[nik] = f"{host}:{port}"

    return new_list_of_users


def build_msg(message_type, data, command=None, userName=None):
    msg = {"type": message_type, "data": data}
    if command is not None:
        msg["command"] = command
    if userName is not None:
        msg["userName"] = userName
    return (json.dumps(msg) + "\n").encode("utf-8")


def decode_message(data):
    if not isinstance(data, str):
        raise TypeError("Message payload must be a JSON string.")

    try:
        msg = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload.") from exc

    if not isinstance(msg, dict):
        raise ValueError("JSON message must be an object.")

    return msg


def writer_msg(data):
    try:
        msg = decode_message(data)
    except (TypeError, ValueError):
        Console.error_msg("Received invalid message data from the server.")
        return

    message_type = msg.get("type")
    message_data = msg.get("data", "")

    if message_type == "users" and isinstance(message_data, dict):
        
        Console.users_table(message_data)
    elif message_type == "broadcast":
        Console.brotcast_msg(str(message_data))
    elif message_type == "private":
        Console.private_msg(str(message_data), str(msg.get("userName", "")))
    elif message_type == "command":

        Console.error_msg(str(message_data))
    else:
        Console.brotcast_msg(str(message_data))


