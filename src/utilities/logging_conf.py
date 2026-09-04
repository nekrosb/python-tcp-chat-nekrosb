import logging

from rich.logging import RichHandler


def setup_logging(name):
    # console
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=False,
        show_level=False,
        show_path=False,
    )

    # file
    file_handler = logging.FileHandler(
        f"{name}.log",
        encoding="utf-8",
    )

    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(file_formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            console_handler,
            file_handler,
        ],
    )
