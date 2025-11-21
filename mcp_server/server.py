import logging
import time
import socket

# Constants
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 65432
TIMEOUT = 5

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_server_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)  # Set timeout for socket operations
    return sock

def start_server():
    server_socket = create_server_socket()
    try:
        server_socket.bind((SERVER_ADDRESS, SERVER_PORT))
        server_socket.listen(5)
        logging.info(f'Server listening on {SERVER_ADDRESS}:{SERVER_PORT}')

        while True:
            try:
                connection, client_address = server_socket.accept()
                handle_client(connection, client_address)
            except socket.timeout:
                logging.warning('Socket timed out')
            except Exception as e:
                logging.error(f'Error accepting connection: {e}')
    finally:
        server_socket.close()

def handle_client(connection, client_address):
    logging.info(f'Connection from: {client_address}')
    try:
        while True:
            data = connection.recv(1024)
            if not data:
                break  # no data, connection closed
            logging.info(f'Received data: {data}')
            connection.sendall(data)  # Echo back the received data
    except Exception as e:
        logging.error(f'Error handling client {client_address}: {e}')
    finally:
        connection.close()
        logging.info(f'Connection closed for {client_address}')

if __name__ == '__main__':
    start_server()