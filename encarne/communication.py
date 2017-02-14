import pickle

from encarne.socket import (
    connect_client_socket,
    process_response,
    receive_data,
)


def add_to_pueue(args):
    client = connect_client_socket()

    # Send new instruction to daemon
    instruction = {
        'mode': 'add',
        'command': args['command'],
        'path': args['path']
    }
    data_string = pickle.dumps(instruction, -1)
    client.send(data_string)

    # Receive Answer from daemon
    response = receive_data(client)
    process_response(response)


def get_status():
    # Initialize socket, message and send it
    client = connect_client_socket()
    instruction = {'mode': 'status'}
    data_string = pickle.dumps(instruction, -1)
    client.send(data_string)

    response = receive_data(client)
    return response


def get_newest_status(command):
    """Get the status and key of the given process in pueue."""
    status = get_status()

    if isinstance(status['data'], dict):
        # Get the status of the latest submitted job, with this command.
        highest_key = None
        for key, value in status['data'].items():
            if value['command'] == command:
                if highest_key is None or highest_key < key:
                    highest_key = key
        if highest_key is not None:
            return status['data'][highest_key]['status']
    return None
