import pickle

from encarne.socket import (
    connect_client_socket,
    process_response,
    receive_data,
)


def add(args):
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
