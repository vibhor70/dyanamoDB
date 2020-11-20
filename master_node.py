import socket
import json
import os
import base64
import threading
import sys

CONTAINER_IP = "127.0.0.1"

class MasterNode(object):
    def __init__(self):
        self.ips =[]
        self.targets =[]
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.s.bind((CONTAINER_IP,54321))
        self.s.listen(5)
        self.clients = 0
        self.stop_threads = False

    def send_all(self, target, data):
        target.sendall(data)

    def reliable_send(self, target,ip,command):
        print("Command send:",command)
        target.sendall(command.encode())

    def reliable_recv(self, target):
        data=""
        cter=True
        while cter:
            try:
                print("Recieving")
                new_recv = target.recv(1024)
                print(new_recv.decode())
                data += new_recv.decode() 
                if(not new_recv or len(new_recv.decode()) < 1024 ):
                    cter=False
                    break
                print(data)
            except ValueError as e:
                print(e)
                break
        print("end of reliable recv")
        return data

    def server(self):
        print("I ma in server")
        while True:
            if self.stop_threads:
                break
            self.s.settimeout(1)
            try:
                target,ip = self.s.accept()
                print(target, ip)
                self.targets.append(target)
                self.ips.append(ip[0])
                print(target, ip)
                #print(str(targets[clients]) + "..."+str(ips[clients])+"has connected")
                print(str(ips[self.clients])+"has connected")
                print(self.ips)
                self.clients +=1
            except Exception as e:
                pass

    def send_command(self, ips_list, operation, item):
        to_send = "{} | {}".format(operation, item)
        print(ips_list)
        for id_,ip in enumerate(self.ips):
            if ip in ips_list:
                self.reliable_send(self.targets[id_], self.ips[id_], to_send)


    def connection_accept(self):
        print("[+] waiting for Data Nodes to connect")
        t1 = threading.Thread(target = self.server)
        t1.start()
        while len(self.ips) == 0:
            # print(self.ips)
            continue

    def get_ips(self):
        return self.ips
        

a = MasterNode()
a.connection_accept()
a.send_command(["127.0.0.1"], "ADD", "yogurt")


            
           
