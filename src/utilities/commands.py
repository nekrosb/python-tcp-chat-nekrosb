import rich

from utilities import helpers


class Client_command:
    def __init__(self, client_socket, stop_event, log):
        self.client_socket = client_socket
        self.stop_event = stop_event
        self.log = log

    def write_help(self, *_args):
        rich.print(
            """[bold cyan]Available commands:[/bold cyan]
    [bold green]/help[/bold green] - Show this help message
    [bold green]/users[/bold green] - Show the list of connected users
    [bold green]/broadcast <message>[/bold green] - Send a chat message to everyone
    [bold green]/exit[/bold green] - Exit the chat
    [bold green]/changeNickname <new_nick>[/bold green] - Change your nickname
    """
        )
        return True

    def take_user(self, *_args):
        try:
            self.client_socket.sendall(helpers.build_msg("users", ""))
        except OSError as e:
            self.log.error(f"Error sending data: {e}")
            self.stop_event.set()
            return False
        return True

    def change_nickname(self, new_nickname):
        if not new_nickname or not str(new_nickname).strip():
            self.log.warning("Nickname cannot be empty.")
            return True

        try:
            self.client_socket.sendall(
                helpers.build_msg(
                    "command",
                    str(new_nickname).strip(),
                    command="changeNickname",
                )
            )
        except OSError as e:
            self.log.error(f"Error sending data: {e}")
            self.stop_event.set()
            return False
        return True

    def exit_chat(self, *_args):
        self.stop_event.set()
        try:
            self.client_socket.close()
        except OSError:
            pass
        return False

    def send_broadcast_message(self, message):
        message = str(message).strip()
        if not message:
            self.log.warning("Message cannot be empty.")
            return True

        try:
            self.client_socket.sendall(helpers.build_msg("broadcast", message))
        except OSError as e:
            self.log.error(f"Error sending data: {e}")
            self.stop_event.set()
            return False
        return True

    def handle_command(self, user_input):
        if not user_input or not str(user_input).strip():
            self.log.warning("Input cannot be empty.")
            return True

        parts = str(user_input).strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        command_map = {
            "/help": self.write_help,
            "/users": self.take_user,
            "/exit": self.exit_chat,
            "/changenickname": self.change_nickname,
            "/broadcast": self.send_broadcast_message,
        }


        if args:
            if command not in command_map:
                if not command.startswith("/"):
                    return self.send_broadcast_message(str(user_input).strip())
                self.log.warning(f"Unknown command: {command}")
                return True
            return command_map[command](args)
        else:
            if command not in command_map:
                self.log.warning(f"Unknown command: {command}")
                return True
            return command_map[command]()
        
    
class ServerCommand:
    def __init__(
        self,
        client_socket,
        list_of_clients,
        niks,
        clients_lock,
        log,
        nickname,
    ):
        self.client_socket = client_socket
        self.nickname = nickname
        self.list_of_clients = list_of_clients
        self.niks = niks
        self.clients_lock = clients_lock
        self.log = log

    def send_broadcast_msg(self, msg):
        disconnected_users = []

        with self.clients_lock:
            users = list(self.list_of_clients.items())

        for username, user in users:
            user_socket = user[0]
            if user_socket == self.client_socket:
                continue

            try:
                user_socket.sendall(helpers.build_msg("broadcast", msg))
            except (ConnectionResetError, BrokenPipeError, OSError):
                disconnected_users.append(username)

        if not disconnected_users:
            return

        with self.clients_lock:
            for username in disconnected_users:
                user = self.list_of_clients.get(username)
                if user is None:
                    continue
                user_socket = user[0]
                try:
                    user_socket.close()
                except OSError:
                    pass
                if username in self.list_of_clients:
                    del self.list_of_clients[username]

    def change_nickname(self, new_nickname):
        if new_nickname is None:
            new_nickname = ""
        new_nickname = str(new_nickname).strip()

        if not new_nickname:
            self.client_socket.sendall(
                helpers.build_msg("broadcast", "Nickname cannot be empty.")
            )
            return True

        if len(new_nickname) > helpers.MAX_NICKNAME_SIZE:
            self.client_socket.sendall(
                helpers.build_msg(
                    "broadcast",
                    f"Nickname is too long. Maximum {helpers.MAX_NICKNAME_SIZE} characters.",
                )
            )
            return True

        old_nickname = self.nickname
        if old_nickname == new_nickname:
            self.client_socket.sendall(
                helpers.build_msg("broadcast", "You are already using this nickname.")
            )
            return True

        with self.clients_lock:
            if new_nickname in self.niks:
                self.client_socket.sendall(
                    helpers.build_msg("broadcast", "This nickname is already taken.")
                )
                return True

            self.niks.discard(old_nickname)
            self.niks.add(new_nickname)
            user = self.list_of_clients.pop(old_nickname, None)
            if user is not None:
                self.list_of_clients[new_nickname] = user
            self.nickname = new_nickname

        self.client_socket.sendall(
            helpers.build_msg(
                "broadcast",
                f"Your nickname has been changed: {old_nickname} -> {new_nickname}",
            )
        )
        self.send_broadcast_msg(f"{old_nickname} has changed their nickname to {new_nickname}")
        return True

    def exit_chat(self):
        self.client_socket.sendall(helpers.build_msg("broadcast", "You have exited the chat."))
        try:
            self.client_socket.close()
        except OSError:
            pass
        return False

    def send_users(self):
        with self.clients_lock:
            users_list = helpers.users_table(self.list_of_clients)

        try:
            self.client_socket.sendall(
                helpers.build_msg("users", users_list)
            )
        except OSError as e:
            self.log.error(f"Error sending users list: {e}")
            return False

        return True

    def handle_command(self, user_input):
        try:
            data_from_client = helpers.decode_message(user_input)
        except (TypeError, ValueError) as exc:
            self.log.warning(f"Invalid JSON from client {self.nickname}: {exc}")
            try:
                self.client_socket.sendall(
                    helpers.build_msg("broadcast", "Invalid JSON message.")
                )
            except OSError:
                pass
            return False
    
        message_type = data_from_client.get("type")
    
        command_map = {
            "changeNickname": self.change_nickname,
            "/changeNickname": self.change_nickname,
            "/exit": self.exit_chat,
        }

        if message_type == "broadcast":
            data = data_from_client.get("data", "")
            data = str(data).strip()

            if not data:
                self.client_socket.sendall(
                    helpers.build_msg("broadcast", "Message cannot be empty.")
                )
                return True
            self.log('не понятно что тут', data)
            self.send_broadcast_msg(f"{self.nickname}: {data}")
            
            return True
        elif message_type == "command":
            command = data_from_client.get("command")
            data = data_from_client.get("data", "")
            if command in command_map:
                return command_map[command](data)
            else:
                self.client_socket.sendall(
                    helpers.build_msg("broadcast", f"Unknown command: {command}")
                )
                return True
        elif message_type == "users":
            return self.send_users()

        self.log.warning(f"Unknown message type: {message_type}")
        return True