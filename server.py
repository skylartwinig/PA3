import threading
import socket
import sys
from time import sleep
from os import _exit
from sys import stdout
from typing import Any
import operator as op
import hashlib
import os
from pathlib import Path

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
        print("NEW POST ",title, " from ", username)

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
                print("NEW COMMENT ",title, " from ", username)
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
    def __init__(self, serverId):
        self.serverID = serverId
        self.accepted_proposal = None
        self.log = []
        self.last_accepted_round = -1
        self.promised_round = -1
        self.accepted_round = -1
        self.accepted_value = None
        self.proposal_value = None
        self.num_servers = 5
        self.num_of_promises = 0
        self.num_of_accepts = 0
        self.my_round = 1
        self.sent_accept_request = False
        self.sent_decision = False
        self.acceptor_waiting_on_decision = False
        self.in_progress = False
        

        self.my_socket = None
        self.clientSockets = []
        self.clientSockPortList = [('localhost', 4445), ('localhost', 4446), ('localhost', 4447), ('localhost', 4448), ('localhost', 4449)]
        self.portNum = self.clientSockPortList[int(sys.argv[1]) - 1]
        self.clientSockPortList.remove(self.portNum)

        self.leaderId = None

        self.blog = Blog()
        self.pending_operations = []

    def start(self):
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.my_socket.bind(self.portNum)
        self.my_socket.listen()

        print(self.my_socket)

        filename = "recovery_file_" + str(self.serverID) + ".txt" 
        my_file = Path(filename)
        if my_file.is_file():
            lines = open(filename, 'r').readlines()
            for line in lines:
                line = line.strip("\n")
                line = line.strip("()")
                line = line.replace("'", "")
                line = line.replace("[", "")
                line = line.replace("]", "")
                temp = line.split(", ")
                round = int(temp[0])
                hash = temp[1]
                compressed = temp[2]
                list_of_operations = []
                list_of_operations.append(temp[3])
                list_of_operations.append(temp[4])
                list_of_operations.append(temp[5])
                list_of_operations.append(temp[6])
                nonce = temp[7]
                log_entry = (round, hash, compressed, list_of_operations, nonce)
                self.log.append(log_entry)
                operation = ""
                for i in list_of_operations:
                    operation += i + " "
                self.apply_operation(operation)

        terminal = threading.Thread(target=self.get_user_input)
        terminal.start()

        while True:
            client_socket, client_address = self.my_socket.accept()
            print(client_socket, " why is this same port ", client_address)

            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def send_to_all_clients(self, message):
        try:
            self.client1Sock.sendall(bytes(message, 'utf-8'))
        except:
            print("Client 1 not connected")
        try:
            self.client2Sock.sendall(bytes(message, 'utf-8'))
        except:
            print("Client 2 not connected")
        try:
            self.client3Sock.sendall(bytes(message, 'utf-8'))
        except:
            print("Client 3 not connected")
        try:
            self.client4Sock.sendall(bytes(message, 'utf-8'))
        except:
            print("Client 4 not connected")
    
    def get_user_input(self):
        while True:
            user_input = input().lower()

            if user_input.startswith('conn'):
                self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client1Sock.connect(self.clientSockPortList[0])
                self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client2Sock.connect(self.clientSockPortList[1])
                self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client3Sock.connect(self.clientSockPortList[2])
                self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client4Sock.connect(self.clientSockPortList[3])

            elif user_input.startswith('faillink'):
                print("in fail link")
                open_index = user_input.find('(')
                close_index = user_input.find(')')
                node_to_fail = int(user_input[open_index + 1:close_index])
                print(node_to_fail)
                if node_to_fail == self.serverID:
                    print("Cannot fail self")
                elif self.serverID == 1:
                    if node_to_fail == 2:
                        self.client1Sock.close()
                    elif node_to_fail == 3:
                        self.client2Sock.close()
                    elif node_to_fail == 4:
                        self.client3Sock.close()
                    elif node_to_fail == 5:
                        self.client4Sock.close()
                        print("closed client 4")
                elif self.serverID == 2:
                    if node_to_fail == 1:
                        self.client1Sock.close()
                    elif node_to_fail == 3:
                        self.client2Sock.close()
                    elif node_to_fail == 4:
                        self.client3Sock.close()
                    elif node_to_fail == 5:
                        self.client4Sock.close()
                elif self.serverID == 3:
                    if node_to_fail == 1:
                        self.client1Sock.close()
                    elif node_to_fail == 2:
                        self.client2Sock.close()
                    elif node_to_fail == 4:
                        self.client3Sock.close()
                    elif node_to_fail == 5:
                        self.client4Sock.close()
                elif self.serverID == 4:
                    if node_to_fail == 1:
                        self.client1Sock.close()
                    elif node_to_fail == 2:
                        self.client2Sock.close()
                    elif node_to_fail == 3:
                        self.client3Sock.close()
                    elif node_to_fail == 5:
                        self.client4Sock.close()
                elif self.serverID == 5:
                    if node_to_fail == 1:
                        self.client1Sock.close()
                    elif node_to_fail == 2:
                        self.client2Sock.close()
                    elif node_to_fail == 3:
                        self.client3Sock.close()
                    elif node_to_fail == 4:
                        self.client4Sock.close()
                
            
            elif user_input.startswith('fixlink'):
                open_index = user_input.find('(')
                close_index = user_input.find(')')
                node_to_fail = int(user_input[open_index + 1:close_index])
                if node_to_fail == self.serverID:
                    print("Cannot fail self")
                elif self.serverID == 1:
                    if node_to_fail == 2:
                        self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client1Sock.connect(self.clientSockPortList[0])
                    elif node_to_fail == 3:
                        self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client2Sock.connect(self.clientSockPortList[1])
                    elif node_to_fail == 4:
                        self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client3Sock.connect(self.clientSockPortList[2])
                    elif node_to_fail == 5:
                        self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client4Sock.connect(self.clientSockPortList[3])
                        self.client4Sock.sendall(bytes("reconnect", 'utf-8'))
                elif self.serverID == 2:
                    if node_to_fail == 1:
                        self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client1Sock.connect(self.clientSockPortList[0])
                    elif node_to_fail == 3:
                        self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client2Sock.connect(self.clientSockPortList[1])
                    elif node_to_fail == 4:
                        self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client3Sock.connect(self.clientSockPortList[2])
                    elif node_to_fail == 5:
                        self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client4Sock.connect(self.clientSockPortList[3])
                elif self.serverID == 3:
                    if node_to_fail == 1:
                        self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client1Sock.connect(self.clientSockPortList[0])
                    elif node_to_fail == 2:
                        self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client2Sock.connect(self.clientSockPortList[1])
                    elif node_to_fail == 4:
                        self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client3Sock.connect(self.clientSockPortList[2])
                    elif node_to_fail == 5:
                        self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client4Sock.connect(self.clientSockPortList[3])
                elif self.serverID == 4:
                    if node_to_fail == 1:
                        self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client1Sock.connect(self.clientSockPortList[0])
                    elif node_to_fail == 2:
                        self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client2Sock.connect(self.clientSockPortList[1])
                    elif node_to_fail == 3:
                        self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client3Sock.connect(self.clientSockPortList[2])
                    elif node_to_fail == 5:
                        self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client4Sock.connect(self.clientSockPortList[3])
                elif self.serverID == 5:
                    if node_to_fail == 1:
                        self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client1Sock.connect(self.clientSockPortList[0])
                    elif node_to_fail == 2:
                        self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client2Sock.connect(self.clientSockPortList[1])
                    elif node_to_fail == 3:
                        self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client3Sock.connect(self.clientSockPortList[2])
                    elif node_to_fail == 4:
                        self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.client4Sock.connect(self.clientSockPortList[3])



            elif user_input.startswith('post') or user_input.startswith('comment'):
                operation = user_input
                # self.pending_operations.append(operation)
                self.proposal_value = operation
                ballot_number = (self.my_round, self.serverID, len(self.log))
                ballot_number = str(ballot_number).replace(' ', '')

                if self.in_progress:
                    print("Already in progress")
                    self.pending_operations.append(operation)

                elif not self.leaderId: #leader election
                    prepare_message = 'PREPARE ' + ballot_number
                    print("SENT: ", prepare_message)
                    self.in_progress = True
                    sleep(3)
                    self.send_to_all_clients(prepare_message)
                
                elif self.leaderId != self.serverID: 
                    self.in_progress = True
                    to_leader_message = 'TO-LEADER ' + str(ballot_number) + ' ' + str(self.proposal_value)
                    print("SENT: ", to_leader_message)
                    sleep(3)
                    self.send_to_all_clients(to_leader_message)
                
                else:
                    self.in_progress = True
                    accept_message = 'ACCEPT-REQUEST ' + str(ballot_number) + ' ' + str(self.proposal_value)
                    print("SENT: ", accept_message)
                    sleep(3)
                    self.send_to_all_clients(accept_message)         

            elif user_input.startswith('blog'):
                if len(self.blog.posts) > 0:
                    print(self.blog.view_all_posts())
                else:
                    print("BLOG EMPTY")

            elif user_input.startswith('view'):
                if len(self.blog.posts) > 0:
                    print(self.blog.view_posts_by_user(user_input.split(' ', 1)[1]))
                else:
                    print("NO POST")

            elif user_input.startswith('read'):
                self.append_to_log(user_input)
                if len(self.blog.posts) > 0:
                    title = user_input.split(' ', 1)[1]
                    for post in self.blog.posts:
                        if self.blog.posts[post]["title"] == title:
                            print("CONTENT: ", self.blog.posts[post]["content"])
                            if len(self.blog.posts[post]["comments"]) > 0:
                                print("COMMENTS: ")
                                for i in self.blog.posts[post]["comments"]:
                                    print(i)
                            break
                        else:
                            print("POST NOT FOUND")
                else:
                    print("POST NOT FOUND")

            elif user_input.startswith('log'):
                print(self.log)

            elif user_input.startswith('blockchain'):
                for event in self.log:
                    eventData = event[3]
                    print('Length of log:' + str(event[0]))
                    print('Previous Hash: ' + event[1])
                    print('Operation Compressed: ' + str(event[2]))
                    if(eventData[0].startswith('read')):
                        print(eventData[0],eventData[1])
                    else:
                        print(eventData[0],eventData[1],eventData[2],eventData[3])
                    print('Nonce: ' + str(event[4]))

            elif user_input.startswith('crash'):
                print("exiting")
                # self.serverSock.sendall(bytes(self.client_id + ': ' + user_input, 'utf-8'))
                # self.serverSock.close()
                # stdout.flush()
                _exit(0)
                
            #
            # handle "COMMENT"
            #

            else:
                self.send_to_all_clients(user_input)
        
    

    def handle_client(self, client_socket):
        while True:
            sleep(3)
            try:
                data = client_socket.recv(1024).decode()
            except:
                continue
            if data and op.countOf(data, " ") > 0:
                promise_data = data.split(' ', 2)
                ballot_number = eval(promise_data[1])

                if data.startswith("PROMISE") and ballot_number[1] != self.serverID:
                    temp = 0
                elif data.startswith("ACCEPT ") and self.leaderId != self.serverID:
                    temp = 0
                else:
                    print("RECIEVED: ", data)

            if data.startswith('reconnect'):
                self.client1Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client1Sock.connect(self.clientSockPortList[0])
                self.client2Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client2Sock.connect(self.clientSockPortList[1])
                self.client3Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client3Sock.connect(self.clientSockPortList[2])
                self.client4Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client4Sock.connect(self.clientSockPortList[3])

            if data.startswith('PREPARE'):
                self.in_progress = True
                ballot_number = eval(data.split(' ', 1)[1])
                # print(ballot_number)
                if self.is_higher_ballot_number(ballot_number):
                    self.leaderId = ballot_number[1]
                    self.promised_round = ballot_number[0]
                    ballot_number = str(ballot_number).replace(' ', '')
                    promise_message = 'PROMISE ' + ballot_number + ' ' + str(self.promised_round) 
                    print("SENT: ", promise_message)
                    sleep(3)
                    self.send_to_all_clients(promise_message)

            
            elif data.startswith('PROMISE'):
                promise_data = data.split(' ', 2)
                ballot_number = eval(promise_data[1])

                if ballot_number[1] == self.serverID:
                    self.num_of_promises += 1
                    if self.num_of_promises >=2 and not self.sent_accept_request:
                        self.num_of_promises = 0
                        self.sent_accept_request = True
                        sleep(3)
                        print("")
                        self.leaderId = self.serverID
                        print("I AM THE LEADER")
                        # accept_request_message = 'ACCEPT-REQUEST ' + str(ballot_number) + ' ' + str(self.proposal_value)
                        accept_request_message = 'ACCEPT-REQUEST ' + promise_data[1] + ' ' + str(self.proposal_value)
                        print("SENT: ",accept_request_message)
                        sleep(3)
                        self.send_to_all_clients(accept_request_message)
                        self.sent_accept_request = False

            elif data.startswith('TO-LEADER'):
                self.in_progress = True
                toLeaderData = data.split(' ', 2)
                ballot_number = eval(toLeaderData[1])
                self.proposal_value = toLeaderData[2]

                if self.leaderId == self.serverID:
                    accept_request_message = 'ACCEPT-REQUEST ' + promise_data[1] + ' ' + str(self.proposal_value)
                    print("SENT: ",accept_request_message)
                    sleep(3)
                    self.send_to_all_clients(accept_request_message)   

            elif data.startswith('ACCEPT-REQUEST'):
                self.in_progress = True
                accept_data = data.split(' ', 2)
                ballot_number = eval(accept_data[1])
                if ballot_number[0] == self.promised_round:
                    self.accepted_round = ballot_number[0]
                    self.accepted_value = accept_data[2]
                    # decision_message = 'ACCEPT ' + str(ballot_number) + ' ' + str(self.accepted_value)
                    decision_message = 'ACCEPT ' + accept_data[1] + ' ' + str(self.accepted_value)
                    print("SENT: ", decision_message)
                    self.append_to_log(self.accepted_value)
                    self.acceptor_to_disk_tenative()
                    self.log.pop()
                    sleep(3)
                    self.send_to_all_clients(decision_message)
                    self.acceptor_waiting_on_decision = True
                    timeout_thread = threading.Thread(target= self.timeout)
                    timeout_thread.start()
                    

                # if self.is_higher_ballot_number(ballot_number):
                    # accepted_value = eval(accept_data[2])
                    # self.accepted_round = ballot_number
                    # self.accepted_value = accepted_value
                    # decision_message = 'DECISION ' + str(ballot_number) + ' ' + str(accepted_value)
                    # for client_socket in self.clientSockets:
                    #     client_socket.sendall(bytes(decision_message, 'utf-8'))
                    # self.append_to_log(accepted_value)
                    # self.apply_operation(accepted_value)
                    # self.remove_pending_operation(accepted_value)

            elif data.startswith('ACCEPT'):
                accept_data = data.split(' ', 2)
                ballot_number = eval(accept_data[1])
                self.accepted_value = accept_data[2]
                # if ballot_number[1] == self.serverID:
                if self.leaderId == self.serverID:
                    self.num_of_accepts += 1
                    # print(" adding the num of promises ", self.num_of_accepts)
                    if self.num_of_accepts >=2 and not self.sent_decision:
                        self.num_of_accepts = 0
                        self.sent_decision = True
                        sleep(3)
                        print("DECISION MADE to be ",self.accepted_value)
                        # accept_message = 'DECISION ' + str(ballot_number) + ' ' + str(self.accepted_value)
                        accept_message = 'DECISION ' + accept_data[1] + ' ' + str(self.accepted_value)
                        print("SENT: ", accept_message)
                        sleep(3)
                        self.send_to_all_clients(accept_message)
                        self.append_to_log(self.accepted_value)
                        self.apply_operation(self.accepted_value)
                        self.sent_decision = False
                        self.leader_to_disk()
                        self.in_progress = False
                        self.handle_pending_operation(self.accepted_value)

            elif data.startswith('DECISION'):
                self.acceptor_waiting_on_decision = False
                print("received decision")
                decision_data = data.split(' ', 2)
                ballot_number = eval(decision_data[1])
                decision_value = decision_data[2]
                self.append_to_log(decision_value)
                self.apply_operation(decision_value)
                self.acceptor_to_disk_final()
                self.in_progress = False
                self.handle_pending_operation(decision_value)

    def leader_to_disk(self):
        filename = "recovery_file_" + str(self.serverID) + ".txt" 
        if len(self.log) == 1:
            f = open(filename, "w")
        else:
            f = open(filename, "a")
        f.write(str(self.log[-1]))
        f.write("\n")
        f.close()
    
    def acceptor_to_disk_tenative(self):
        filename = "recovery_file_" + str(self.serverID) + ".txt" 
        if len(self.log) == 1:
            f = open(filename, "w")
        else:
            f = open(filename, "a")
        f.write(str(self.log[-1]) + " TENATIVE")
        f.write("\n")
        f.close()

    def acceptor_to_disk_final(self):
        filename = "recovery_file_" + str(self.serverID) + ".txt" 
        lines = open(filename, 'r').readlines()
        lines[-1] = str(self.log[-1]) + "\n"
        f = open(filename, "w")
        for i in lines:
            f.write(i)
        f.close()


    def timeout(self):
        sleep(10)
        if self.acceptor_waiting_on_decision:
            print("TIMEOUT")

    def is_higher_ballot_number(self, ballot_number):

        if ballot_number[0] > self.promised_round:
            return True
        elif ballot_number[0] == self.promised_round and ballot_number[1] > self.serverID:
            return True
        return False

        # if ballot_number[2] > len(self.log):
        #     return True
        # elif ballot_number[2] == len(self.log) and ballot_number[1] > self.serverID:
        #     return True
        # elif  ballot_number[0] > self.last_accepted_round:
        #     return True
        
        # if ballot_number[2] > len(self.log):
        #     return True
        # elif ballot_number[2] == len(self.log) and ballot_number[1] > self.serverID:
        #     return True
        # elif ballot_number[2] == len(self.log) and ballot_number[1] == self.serverID and ballot_number[0] > self.last_accepted_round:
        #     return True
        return False

    def append_to_log(self, operation):
        if operation.startswith('post') or operation.startswith('comment') :
            operation_data = operation.split(' ')
            op = f'{operation_data[0]}{operation_data[1]}{operation_data[2]}{operation_data[3]}'
            self.block_op(op, operation_data)

        elif operation.startswith('read'):
            operation_data = operation.split(' ')
            op = f'{operation_data[0]}{operation_data[1]}'
            self.block_op(op, operation_data)
        

    def block_op(self, operation, opData):
        if(self.log == []):
            prevHash = '0' * 64
        else:
            prevHash = hashlib.sha256((f'{self.log[len(self.log)-1][2]}').encode()).hexdigest().zfill(64)
        found, nonce = False, 0
        while not found:
            m = hashlib.sha256((f'{prevHash}{operation}{nonce}').encode())
            dig = m.hexdigest().zfill(64)
            if str(dig)[0] in ["0", "1", "2", "3"]:
                self.last = 0
                self.log.append((len(self.log), prevHash, operation, opData,  nonce))
                found = True
            else:
                nonce += 1

    def apply_operation(self, operation):
        if operation.startswith('post'):
            operation_data = operation.split(' ', 3)
            username = operation_data[1]
            title = operation_data[2]
            content = operation_data[3]
            self.blog.make_post(username, title, content)
        elif operation.startswith('comment'):
            operation_data = operation.split(' ', 3)
            username = operation_data[1]
            title = operation_data[2]
            comment = operation_data[3]
            self.blog.comment_on_post(username, title, comment)

    def handle_pending_operation(self, operation):
        if len(self.pending_operations) > 0:
            operation = self.pending_operations[0]
            self.proposal_value = operation
            ballot_number = (self.my_round, self.serverID, len(self.log))
            ballot_number = str(ballot_number).replace(' ', '')
            self.pending_operations.pop(0)

            if self.leaderId != self.serverID: 
                self.in_progress = True
                to_leader_message = 'TO-LEADER ' + str(ballot_number) + ' ' + str(self.proposal_value)
                print("SENT: ", to_leader_message)
                sleep(3)
                self.send_to_all_clients(to_leader_message)
                    
            else:
                self.in_progress = True
                accept_message = 'ACCEPT-REQUEST ' + str(ballot_number) + ' ' + str(self.proposal_value)
                print("SENT: ", accept_message)
                sleep(3)
                self.send_to_all_clients(accept_message)   


if __name__ == '__main__':
    # server1 = Server(str('P' + sys.argv[1]))
    server1 = Server(int(sys.argv[1]))
    server1.start()
