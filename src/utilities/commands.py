import rich
from utilities import helpers

class Client_command:

    def __init__(self, client_socket, stop_event, log):
        self.client_socket = client_socket
        self.stop_event = stop_event
        self.log = log

    def Write_help(self):
        rich.print(
        """[bold cyan]Available commands:[/bold cyan]
    [bold green]/help[/bold green] - Show this help message
    [bold green]/users[/bold green] - Show the list of connected users
    [bold green]/private <username> <message>[/bold green] - Send a private message to a user
    [bold green]/exit[/bold green] - Exit the chat
    [bold green]/changeNickname <newNik[/bold green] - Change your nickname
    """
        )

    def take_user(self):
        try:
            self.client_socket.sendall(helpers.build_msg("users", ""))
        except OSError as e:
            self.log.error(f"Error sending data: {e}")
            self.stop_event.set()

    def change_nickname(self, new_nickname):
        try:
            self.client_socket.sendall(helpers.build_msg("command", new_nickname, command="changeNickname"))
        except OSError as e:
            self.log.error(f"Error sending data: {e}")
            self.stop_event.set()

    def exit_chat(self):
        self.stop_event.set()
        self.client_socket.close()

    def send_broadcast_message(self, message):
        try:
            self.client_socket.sendall(helpers.build_msg("broadcast", message))

        except OSError as e:
            self.log.error(f"Error sending data: {e}")
            self.stop_event.set()

    def handle_command(self, user_input):
        dic = {
            "/help": self.Write_help,
            "/users": self.take_user,
            "/exit": self.exit_chat,
            "/changeNickname": self.change_nickname,
            '/broadcast': self.send_broadcast_message
        }

        part = user_input.split()
        command = part[0]
        arg = part[1:]



        if command in dic:
            if len(arg) > 0:
                dic[command](" ".join(arg))
            else:
                dic[command]()
        else:
            self.log.warning(f"Unknown command: {command}. Type /help for a list of commands.")




class ServerCommand:

    

    def __init__(
        self,
        client_socket,
        list_of_clients,
        niks,
        clients_lock,
        log,
        nickname
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
        
        with self.clients_lock:    
            for username in disconnected_users:    
                user = self.list_of_clients.get(username)    
        
                if user is None or user[0] is self.client_socket:    
                    continue    
        
                user_socket = user[0]    
        
                try:    
                    user_socket.close()    
                except OSError:    
                    pass    
        
                del self.list_of_clients[username]

    def change_nickname(self, new_nickname):
        new_nickname = new_nickname.strip()
        if not new_nickname:
            self.client_socket.sendall(
                helpers.build_msg("broadcast", "Nickname cannot be empty.")
            )
            return True

        old_nickname = self.nickname
        if old_nickname == new_nickname:
            self.client_socket.sendall(
                helpers.build_msg(
                    "broadcast",
                    "You are already using this nickname."
                )
            )
            return True

        with self.clients_lock:
            if new_nickname in self.niks:
                self.client_socket.sendall(
                    helpers.build_msg(
                        "broadcast",
                        "This nickname is already taken."
                    )
                )
                return True

            self.niks.remove(old_nickname)
            self.niks.add(new_nickname)
            user = self.list_of_clients.pop(old_nickname, None)
            if user is not None:
                self.list_of_clients[new_nickname] = user
            self.nickname = new_nickname

        self.client_socket.sendall(
            helpers.build_msg(
                "broadcast",
                f"Your nickname has been changed: {old_nickname} -> {new_nickname}"
            )
        )
        self.send_broadcast_msg(
            f"{old_nickname} has changed their nickname to {new_nickname}"
        )
        return True

    def exit_chat(self):
        self.client_socket.sendall(
            helpers.build_msg(
                "broadcast",
                "You have exited the chat."
            )
        )
        self.client_socket.close()
        return False

    def handle_command(self, user_input):
        commands = {
            "changeNickname": self.change_nickname,
            "/exit": self.exit_chat,
        }

        data_from_client = helpers.decode_message(user_input)
        message_type = data_from_client.get("type")
        data = data_from_client.get("data")
        if message_type == "users":
            self.client_socket.sendall(
                helpers.build_msg("users", helpers.users_table(self.list_of_clients))
            )
        elif message_type == "broadcast":
            self.send_broadcast_msg(data)
        elif message_type == "command":
            command = data_from_client.get("command")
            handler = commands.get(command)
            if handler is not None:
                return handler(data) if data is not None else handler()

        return True