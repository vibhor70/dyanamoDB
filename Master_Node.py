import socket
import json
import os
import base64
import threading
import sys
def send_all(target,data):
    json_data = data
    target.sendall(json_data)

def reliable_send(target,ip,command,c_data):
        json_data = command + c_data
        print("Command send:",json_data)
        target.sendall(json_data.encode())


def reliable_recv(target):
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





def server():
    global clients
    while True:
        if stop_threads:
            break
        s.settimeout(1)
        try:
            target,ip = s.accept()
            targets.append(target)
            ips.append(ip[0])
			#print(str(targets[clients]) + "..."+str(ips[clients])+"has connected")
            print(str(ips[clients])+"has connected")
            print(ips)
            clients +=1
        except:
            pass




global s
ips =[]
targets =[]

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

s.bind(("192.168.30.118",54321))
s.listen(5)

clients = 0
stop_threads = False
print("[+] waiting for Data Nodes to connect")
t1 = threading.Thread(target = server)
t1.start()

def command(ips_list,command,c_data):
    print(ips_list)
    for id_,ip in enumerate(ips):
        if ip in ips_list:
            reliable_send(targets[id_],ips[id_],command,c_data)








while len(ips) ==0:
    continue

cter = "NONE"
def main_command(ip_to_send,input_):
    
    if cter != input_:
        cter = input_
        if len(ips)>0:
            print("ips cter",ips)
            if input_ == "SEND" and len(ips)!=0 :
                print(input_,len(ips))
                command(ip_to_send,"INSERT","APPLE")
            
           
