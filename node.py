#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64
from tinydb import TinyDB, Query

db = TinyDB('db/db.json')

IP_CONNECT = "127.0.0.1"

def reliable_send(data):
	json_data = data
	print(json_data)
	sock.sendall(json_data)

def reliable_recv():
	data= b""
	while True:
		try:
			data = data + sock.recv(1024)
			if len(data) < 1024:
				break

		except ValueError as e:
			print("caught", e)
			print(e)

	try:
		data = json.loads(data.decode())
		print(data)
	except Exception as e:
		print(e, "exception")
		return None

	return data


def shell():
	while True:
		print("Listening")
		data_recv = reliable_recv()
		if data_recv is not None:
			db.insert(data_recv)
		#print(command)
		

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((IP_CONNECT,54321))

shell()
sock.close()

