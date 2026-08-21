from rich.console import Console as RichConsole
from rich.table import Table


class Console:
    @staticmethod
    def users_table(users: dict):
        table = Table(
            title="Users",
            show_header=True,
            header_style="bold cyan",
            border_style="bright_blue",
        )

        table.add_column("#", style="dim", justify="right")
        table.add_column("Username", style="bold green")
        table.add_column("Address", style="yellow")

        for number, (username, address) in enumerate(users.items(), start=1):
            table.add_row(str(number), username, address)

        RichConsole().print(table)

    @staticmethod
    def brotcast_msg(msg: str):
        RichConsole().print(f"[bold magenta]Broadcast:[/bold magenta] {msg}")
