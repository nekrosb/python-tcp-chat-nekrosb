import argparse
import os

from dotenv import load_dotenv


def pars_conf():
    load_dotenv()
    parse = argparse.ArgumentParser(description="TCP Chat Server")
    parse.add_argument(
        "-p",
        "--port",
        type=int,
        default=int(os.getenv("PORT", "12345")),
        help="Port to listen on",
    )

    parse.add_argument(
        "-H",
        "--host",
        type=str,
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to listen on",
    )

    return parse.parse_args()
