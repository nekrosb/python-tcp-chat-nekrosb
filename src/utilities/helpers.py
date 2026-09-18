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
    msg = {
        "type": message_type, 
        **({"command": command} if command else {}), # add command in dic if provided
        **({"userName": userName} if userName else {}), # add user name in dic if provided
        "data": data
        }

    return (json.dumps(msg) + "\n").encode("utf-8")


def decode_message(data):
    return json.loads(data)


def writer_msg(data):
    msg = decode_message(data)
    message_type = msg.get("type")
    message_data = msg.get("data", "")

    if message_type == "users" and isinstance(message_data, dict):
        Console.users_table(message_data)
    else:
        Console.brotcast_msg(str(message_data))


