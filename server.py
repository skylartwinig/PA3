import threading
import socket
import sys
from time import sleep
from os import _exit
from sys import stdout
from typing import Any

class Blog:
    def __init__(self):
        self.posts = {}
        self.comments = {}

    def make_post(self, username, title, content):
        post_id = len(self.posts) + 1
        post = {
            'id': post_id,
            'username': username,
            'title': title,
            'content': content,
            'comments': []
        }
        self.posts[post_id] = post

    def comment_on_post(self, username, title, comment):
        for post in self.posts.values():
            if post['title'] == title:
                comment_id = len(self.comments) + 1
                new_comment = {
                    'id': comment_id,
                    'username': username,
                    'comment': comment
                }
                post['comments'].append(new_comment)
                self.comments[comment_id] = new_comment
                break

    def view_all_posts(self):
        posts = []
        for post in self.posts.values():
            posts.append((post['title'], post['username']))
        return sorted(posts, key=lambda x: x[0])

    def view_posts_by_user(self, username):
        posts = []
        for post in self.posts.values():
            if post['username'] == username:
                posts.append((post['title'], post['content']))
        return sorted(posts, key=lambda x: x[0])

    def view_comments_on_post(self, title):
        comments = []
        for post in self.posts.values():
            if post['title'] == title:
                comments = [(c['comment'], c['username']) for c in post['comments']]
                break
        return comments



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
        self.clientSockPortList = [('localhost', 4445), ('localhost', 4446), ('localhost', 4447), ('localhost', 4448), ('localhost', 4449)]
        self.portNum = self.clientSockPortList[int(sys.argv[1]) - 1]
        self.clientSockPortList.remove(self.portNum)

        self.leaderId = None

    def start(self):

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.my_socket.bind(self.portNum)
        self.my_socket.listen()

        print(self.my_socket)

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
            
            elif user_input.startswith('POST'):
                if not self.leaderId:
                    self.leaderElection()
            
            else:
                self.client1Sock.sendall(bytes(user_input, 'utf-8'))
                self.client2Sock.sendall(bytes(user_input, 'utf-8'))
                self.client3Sock.sendall(bytes(user_input, 'utf-8'))
                self.client4Sock.sendall(bytes(user_input, 'utf-8'))

    def leaderElection(self):
        ballot_number = 0
        self.client1Sock.sendall(bytes('PREPARE ' + self.leaderId, 'utf-8'))
        self.client2Sock.sendall(bytes('PREPARE ' + self.leaderId, 'utf-8'))
        self.client3Sock.sendall(bytes('PREPARE ' + self.leaderId, 'utf-8'))
        self.client4Sock.sendall(bytes('LEAPREPAREDER ' + self.leaderId, 'utf-8'))

    
    def handle_client(self, client_socket):
        while True:
            sleep(3)
            data = client_socket.recv(1024).decode()
            print(data)

if __name__ == '__main__':
    # Create 5 server
    server1 = Server(str('P' + sys.argv[1]))

    # Start clients
    server1.start()

