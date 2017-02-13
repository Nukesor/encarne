import os
import sys
import socket
import pickle
import logging


def get_socket_path():
    """Get the socket path of pueue."""

    config_dir = os.path.join(os.path.expanduser('~'), '.config/pueue')
    socket_path = os.path.join(config_dir, "pueue.sock")
    return socket_path


def receive_data(socket):
    """Receive message from daemon and unpickle it."""
    answer = socket.recv(1048576)
    response = pickle.loads(answer)
    socket.close()
    return response


def process_response(response):
    """ Print it and exit with 1 if operation wasn't successful. """
    logging.info(response['message'])
    if response['status'] != 'success':
        sys.exit(1)


def connect_client_socket():
    """Create Socket and exit with 1, if socket can't be created."""
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(get_socket_path())
    except:
        logging.error("Error connecting to socket. Make sure the pueue daemon is running. Execute `pueue --daemon` to start it.")
        sys.exit(1)
    return client
