#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64
from tinydb import TinyDB, Query

db = TinyDB('db/db.json')

IP_CONNECT = "127.0.0.1"
DEVICE = "1"
# record = TinyDB("records.json")
# secondary_index = TinyDB("secondary.json")

# TO DO SET INDIVIDUAL DEVICE ID's FOR EACH CONTAINER
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
			print("caught in data", e)
			print(e)
	try:
		data = data.decode().split("\n")
		to_return = []
		for d in data :
			if len(d)>0:
				to_return.append(json.loads(d))

		return to_return
	except Exception as e:
		print(e, "exception in loads")
		return []



def shell():
	while True:
		print("Listening")
		data_recv = reliable_recv()
		print(data_recv)
		if data_recv is not None:
			try:
				db.insert_multiple(data_recv)
			except ValueError as e:
				print(e, "exception in db insert")
		

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((IP_CONNECT,54321))

shell()
sock.close()

