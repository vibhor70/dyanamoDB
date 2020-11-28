import base64
import json
import os
import socket
import struct
import sys
import threading

class SocketServer(object):
    def __init__(self, CONTAINER_IP, PORT = 54321):
        # self.ips =[]
        self.targets = dict()
        self.CONTAINER_IP = CONTAINER_IP

        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.s.bind((self.CONTAINER_IP,PORT))
        self.s.listen(10)
        self.clients = 0
        self.stop_threads = False

    def send_all(self, target, data):
        target.sendall(data)

    def reliable_send(self, target, command):
        target.sendall(command)

    def reliable_recv(self, target):
        data=""
        cter=True
        while cter:
            try:
                print("Recieving")
                new_recv = target.recv(4048)
                print(new_recv.decode())
                data += new_recv.decode() 
                if(not new_recv or len(new_recv.decode()) < 4048 ):
                    cter=False
                    break
            except ValueError as e:
                print(e)
                break
        print("end of reliable recv")
        print("Recieved: ", data)
        return data

    def server(self):
        while True:
            if self.stop_threads:
                break
            self.s.settimeout(1)
            try:
                target, ip = self.s.accept()
                self.targets[ip] = target
                # self.ips.append(ip[0])
                print(str(ip)+"has connected")
                # self.clients +=1
            except Exception as e:
                pass


    def send_command(self, ips_list, data):
        to_send = json.dumps(data).encode()
        to_send = struct.pack('>I', len(to_send))  + to_send
        for id_,ip in enumerate(list(self.targets.keys())):
            if ip in ips_list:
                self.reliable_send(self.targets[ip], to_send)


    def connection_accept(self):
        print("[+] waiting for Nodes to connect")
        t1 = threading.Thread(target = self.server)
        t1.start()
        while len(self.targets.keys()) == 0:
            # TO DO ADD CONDITION FOR CHECKING DATA NODE CONTAINERS ARE ACTIVE OR NOT
            continue

    def get_ips(self):
        return list(self.targets.keys())
        
