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
        text = (user_input or "").strip()
        if not text:
            self.log.warning("Empty input ignored. Type /help for a list of commands.")
            return True

        if not text.startswith("/"):
            return self.send_broadcast_message(text)

        parts = text.split()
        command = parts[0].lower()
        args = parts[1:]
        command_map = {
            "/help": self.write_help,
            "/users": self.take_user,
            "/exit": self.exit_chat,
            "/changenickname": self.change_nickname,
            "/broadcast": self.send_broadcast_message,
        }

        if command not in command_map:
            self.log.warning(
                f"Unknown command: {parts[0]}. Type /help for a list of commands."
            )
            return True

        handler = command_map[command]
        if command in {"/help", "/users", "/exit"}:
            return handler(*args)

        if command == "/changenickname":
            if len(args) != 1:
                self.log.warning("Usage: /changeNickname <new_nickname>")
                return True
            return handler(args[0])

        if not args:
            self.log.warning(f"Usage: {parts[0]} <message>")
            return True

        return handler(" ".join(args))


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

    def handle_command(self, user_input):
        commands = {
            "changeNickname": self.change_nickname,
            "/exit": self.exit_chat,
        }

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

        if not isinstance(data_from_client, dict):
            self.log.warning(f"Client {self.nickname} sent a non-object JSON message.")
            try:
                self.client_socket.sendall(
                    helpers.build_msg("broadcast", "Invalid JSON message.")
                )
            except OSError:
                pass
            return False

        message_type = data_from_client.get("type")
        data = data_from_client.get("data")

        if message_type == "users":
            with self.clients_lock:
                snapshot = dict(self.list_of_clients)
            self.client_socket.sendall(
                helpers.build_msg("users", helpers.users_table(snapshot))
            )
            return True

        if message_type == "broadcast":
            if not isinstance(data, str):
                self.log.warning(f"Client {self.nickname} sent an invalid broadcast message.")
                return False
            self.send_broadcast_msg(f"{self.nickname}: {data}")
            return True

        if message_type == "command":
            command = data_from_client.get("command")
            if not isinstance(command, str):
                self.log.warning(
                    f"Client {self.nickname} sent a command without a valid name."
                )
                return False
            handler = commands.get(command)
            if handler is not None:
                value = data if data is not None else None
                return handler(value)
            self.log.warning(f"Unsupported command received from {self.nickname}: {command}")
            return True

        return True