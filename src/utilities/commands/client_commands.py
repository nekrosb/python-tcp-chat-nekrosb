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
        
    
