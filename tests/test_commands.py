import json
import threading
import unittest
from unittest.mock import Mock

from utilities import commands
from utilities import helpers


class DummySocket:
    def __init__(self):
        self.sent = []

    def sendall(self, data):
        self.sent.append(data)

    def close(self):
        pass


class ClientCommandTests(unittest.TestCase):
    def test_regular_message_is_sent_as_broadcast(self):
        sock = DummySocket()
        logger = Mock()
        cmd = commands.Client_command(sock, threading.Event(), logger)

        cmd.handle_command("hello there")

        self.assertTrue(sock.sent)
        payload = json.loads(sock.sent[-1].decode("utf-8"))
        self.assertEqual(payload["type"], "broadcast")
        self.assertEqual(payload["data"], "hello there")

    def test_empty_input_does_not_crash(self):
        sock = DummySocket()
        logger = Mock()
        cmd = commands.Client_command(sock, threading.Event(), logger)

        cmd.handle_command("   ")

        self.assertEqual(sock.sent, [])
        logger.warning.assert_called_once()


class ServerCommandTests(unittest.TestCase):
    def test_invalid_json_is_rejected(self):
        sock = DummySocket()
        logger = Mock()
        server = commands.ServerCommand(
            sock,
            {"alice": [sock, ("127.0.0.1", 1234)]},
            {"alice"},
            threading.Lock(),
            logger,
            "alice",
        )

        result = server.handle_command("not-json")

        self.assertFalse(result)
        self.assertTrue(sock.sent)

    def test_broadcast_preserves_sender_identity(self):
        sock = DummySocket()
        other = DummySocket()
        logger = Mock()
        server = commands.ServerCommand(
            sock,
            {"alice": [sock, ("127.0.0.1", 1234)], "bob": [other, ("127.0.0.2", 4321)]},
            {"alice", "bob"},
            threading.Lock(),
            logger,
            "alice",
        )

        result = server.handle_command('{"type": "broadcast", "data": "hi there"}')

        self.assertTrue(result)
        self.assertTrue(other.sent)
        payload = json.loads(other.sent[-1].decode("utf-8"))
        self.assertEqual(payload["data"], "alice: hi there")

    def test_broadcast_does_not_include_command_prefix(self):
        sock = DummySocket()
        other = DummySocket()
        logger = Mock()
        server = commands.ServerCommand(
            sock,
            {"alice": [sock, ("127.0.0.1", 1234)], "bob": [other, ("127.0.0.2", 4321)]},
            {"alice", "bob"},
            threading.Lock(),
            logger,
            "alice",
        )

        result = server.handle_command(
            '{"type": "broadcast", "data": "/broadcast hello"}'
        )

        self.assertTrue(result)
        payload = json.loads(other.sent[-1].decode("utf-8"))
        self.assertEqual(payload["data"], "alice: hello")

    def test_renamed_nickname_respects_size_limit(self):
        sock = DummySocket()
        logger = Mock()
        server = commands.ServerCommand(
            sock,
            {"alice": [sock, ("127.0.0.1", 1234)]},
            {"alice"},
            threading.Lock(),
            logger,
            "alice",
        )

        result = server.change_nickname("x" * (helpers.MAX_NICKNAME_SIZE + 1))

        self.assertTrue(result)
        self.assertEqual(server.nickname, "alice")
        self.assertIn("Nickname is too long", sock.sent[-1].decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
