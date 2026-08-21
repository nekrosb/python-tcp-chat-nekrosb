import json

from classes.client.console import Console


def shutdown_server(socket, stop_event):
    stop_event.set()
    socket.close()


def users_table(users: dict):
    new_list_of_users = {}

    for nik, client_info in users.items():
        host, port = client_info[1]
        new_list_of_users[nik] = f"{host}:{port}"

    return new_list_of_users


def build_msg(type, data):
    msg = {"type": type, "data": data}

    return (json.dumps(msg) + "\n").encode("utf-8")


def decode_message(data):
    return json.loads(data)


def writer_msg(data):
    msg = decode_message(data)

    if msg["type"] == "broadcast":
        Console.brotcast_msg(msg["data"])
    elif msg["type"] == "users":
        Console.users_table(msg["data"])
