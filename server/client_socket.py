import socket
from server_config import READ_TIMEOUT, BYTES_TRANSFER_PER_TIME

class ClientSocket(object):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address

    def readbytes(self):
        bufferSize = BYTES_TRANSFER_PER_TIME
        self.connection.settimeout(READ_TIMEOUT)
        return self.connection.recv(bufferSize).decode()

    def send(self, *args, **kwargs):
        return self.connection.send(*args, **kwargs)

    def close(self, *args, **kwargs):
        return self.connection.close(*args, **kwargs)