#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64
from tinydb import TinyDB, Query
import struct

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


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def reliable_recv():
	raw_msglen = recvall(sock, 4)
	if not raw_msglen:
		return None
	msglen = struct.unpack('>I', raw_msglen)[0]
	data = recvall(sock, msglen)
	return json.loads(data.decode())

def shell():
	while True:
		print("Listening")
		data_recv = reliable_recv()
		if data_recv is not None:
			try:
				db.insert(data_recv)
			except ValueError as e:
				print(e, "exception in db insert")
		

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((IP_CONNECT,54321))

shell()
sock.close()

