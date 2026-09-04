import logging
import socket
import threading

from config import pars_conf
from utilities import helpers
from utilities.logging_conf import setup_logging

setup_logging("client")


def main():
	args = pars_conf()
	host = args.host
	port = args.port
	log = logging.getLogger(__name__)

	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	stop_event = threading.Event()
	try:
		client_socket.connect((host, port))
	except ConnectionRefusedError:
		log.error(f"Could not connect to server at {host}:{port} ")
		return

	input_msg = threading.Thread(
		target=send_messages, args=(client_socket, stop_event, log), daemon=True
	)
	input_msg.start()
	log.info(f"Connected to server at {host}:{port}")

	receive_thread = threading.Thread(
		target=receive_messages, args=(client_socket, stop_event, log), daemon=True
	)
	receive_thread.start()

	try:
		while not stop_event.is_set():
			stop_event.wait(0.5)

	finally:
		log.info("Exiting client...")
		stop_event.set()
		client_socket.close()
		helpers.shutdown_server(client_socket, stop_event)


def receive_messages(client_socket, stop_event, log):
	client_socket.settimeout(1.0)

	buffer = b""

	while not stop_event.is_set():
		try:
			data = client_socket.recv(1024)

			if not data:
				log.info("Server closed the connection")
				stop_event.set()
				break

			buffer += data

			while b"\n" in buffer:
				raw_message, buffer = buffer.split(b"\n", 1)
				if len(raw_message) > helpers.MAX_MESSAGE_SIZE + helpers.MAX_NICKNAME_SIZE + 2:
					log.error("Received an oversized message from server")
					stop_event.set()
					break
				message = raw_message.decode("utf-8")

				if message:
					helpers.writer_msg(message)

			if len(buffer) > helpers.MAX_MESSAGE_SIZE + helpers.MAX_NICKNAME_SIZE + 2:
				log.error("Received an oversized message from server")
				stop_event.set()
				break

		except socket.timeout:
			continue

		except ConnectionResetError:
			log.warning("Connection reset by server")
			stop_event.set()
			break

		except UnicodeDecodeError:
			log.error("Received invalid UTF-8 data from server")
			stop_event.set()
			break

		except OSError as e:
			log.error(f"Error receiving data: {e}")
			stop_event.set()
			break


def send_messages(client_socket, stop_event, log):
	while not stop_event.is_set():
		try:
			message = input("Enter message (or '/exit' to quit): ")
			if message.lower() == "/exit":
				stop_event.set()
				break
			client_socket.sendall((message + "\n").encode("utf-8"))
		except OSError as e:
			log.error(f"Error sending data: {e}")
			stop_event.set()
			break


main()