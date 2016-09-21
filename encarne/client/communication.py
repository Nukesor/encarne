import pickle

from encarne.helper.socket import (
    connect_client_socket,
    receive_data,
    process_response,
)


def execute_add(args):
    client = connect_client_socket()

    # Send new instruction to daemon
    instruction = {
        'mode': 'add',
        'command': args['command'],
        'path': args['path']
    }
    data_string = pickle.dumps(instruction, -1)
    client.send(data_string)

    # Receive Answer from daemon and print it
    response = receive_data(client)
    process_response(response)


def execute_remove(args):
    client = connect_client_socket()

    # Send new instruction to daemon
    instruction = {
        'mode': 'remove',
        'key': args['key']
    }
    data_string = pickle.dumps(instruction, -1)
    client.send(data_string)

    # Receive Answer from daemon and print it
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
