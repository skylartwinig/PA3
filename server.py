import threading
import socket
import sys
from time import sleep
from os import _exit
from sys import stdout
from typing import Any

class Server:
    def __init__(self,serverId):
        self.serverID = serverId
        self.accepted_proposal = None
        self.log = []
        self.last_accepted_round = -1
        self.promised_round = -1
        self.accepted_round = -1
        self.accepted_value = None
        self.proposal_value = None
        self.num_servers = 5

        self.my_socket = None
        self.client1Sock = None
        self.client2Sock = None
        self.client3Sock = None
        self.client4Sock = None
        self.client5Sock = None
        self.clientSockPortList = [('localhost', 4445), ('localhost', 4446), ('localhost', 4447), ('localhost', 4448), ('localhost', 4449)]
        self.portNum = self.clientSockPortList[int(sys.argv[1]) - 1]
        self.clientSockPortList.remove(self.portNum)

    def start(self):

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.my_socket.bind(self.portNum)
        self.my_socket.listen()

        terminal = threading.Thread(target= self.get_user_input)
        terminal.start()
        while True:
            # Accept client connections
            client_socket, client_address = self.my_socket.accept()
            print(client_socket, " why is this same port ", client_address)

            # Create new thread for each client connection
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
        
    def get_user_input(self):
        while True:
            user_input = input()

            # Handle balance message
            if user_input.startswith('Conn'):
                self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client1Sock.connect(self.clientSockPortList[0])
                self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client2Sock.connect(self.clientSockPortList[1])
                self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client3Sock.connect(self.clientSockPortList[2])
                self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client4Sock.connect(self.clientSockPortList[3])
                self.client5Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client5Sock.connect(self.clientSockPortList[4])
                