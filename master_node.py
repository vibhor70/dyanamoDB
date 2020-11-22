import socket
import json
import os
import base64
import threading
import sys
import struct

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


    def send_command(self, ips_list, data):
        to_send = json.dumps(data).encode()
        to_send = struct.pack('>I', len(to_send))  + to_send
        # print(ips_list)
        for id_,ip in enumerate(self.ips):
            if ip in ips_list:
                self.reliable_send(self.targets[id_], self.ips[id_], to_send)


    def connection_accept(self):
        print("[+] waiting for Data Nodes to connect")
        t1 = threading.Thread(target = self.server)
        t1.start()
        while len(self.ips) == 0:
            # TO DO ADD CONDITION FOR CHECKING DATA NODE CONTAINERS ARE ACTIVE OR NOT
            continue

    def get_ips(self):
        return self.ips
        

a = MasterNode()
#Blocking Call

a.connection_accept()


a.send_command(["127.0.0.1"], {"USERID":"1", "PRODUCTID":"2","OPERATION":"3","PRICE":"4","CATEGORY":"120"})
a.send_command(["127.0.0.1"], {"USERID":"1", "PRODUCTID":"3","OPERATION":"5","PRICE":"45","CATEGORY":"120"})
a.send_command(["127.0.0.1"], {"USERID":"1", "PRODUCTID":"4","OPERATION":"3","PRICE":"4","CATEGORY":"120"})

