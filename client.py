import socket
import _pickle as pickle
from util import FORMAT, HOST_IP_ADDR, PORT


class Network:
    """
    class to connect, send and recieve information from the server

    need to hardcode the host attribute to be the server's ip
    """

    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = HOST_IP_ADDR
        self.port = PORT
        self.addr = (self.host, self.port)

    def connect(self, name):
        """
        connects to server and returns the id of the client that connected
        :param name: str
        :return: int representing id
        """
        self.client.connect(self.addr)
        self.client.send(name.encode(FORMAT))
        val = self.client.recv(8)
        return int(val.decode(FORMAT))  # can be int because will be an int id

    def disconnect(self):
        """
        disconnects from the server
        :return: None
        """
        self.client.close()

    def send(self, data, pick=False):
        """
        sends information to the server

        :param data: str
        :param pick: boolean if should pickle or not
        :return: str
        """
        try:
            if pick:
                self.client.send(pickle.dumps(data))
            else:
                self.client.send(data.encode(FORMAT))
            reply = self.client.recv(2048*4)
            try:
                reply = pickle.loads(reply)
            except Exception as e:
                print(e)

            return reply
        except socket.error as e:
            print(e)
