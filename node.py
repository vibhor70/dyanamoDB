#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64
from tinydb import TinyDB,Query
IP_CONNECT = "127.0.0.1"
DEVICE = "1"
record = TinyDB("records.json")
secondary_index = TinyDB("secondary.json")

# TO DO SET INDIVIDUAL DEVICE ID's FOR EACH CONTAINER
def reliable_send(data):
	json_data = data
	print(json_data)
	sock.sendall(json_data)

def reliable_recv():
	data=""
	while True:
		try:
			data =""
			data =  sock.recv(1024).decode()
			
			#print(data.split(">"))
			data = data.split(">")
			for value in range(len(data)):
				print(data[value-1])
				print(data[value-1].split("|")[0])
				# userID = data[value-1].split("|")[0]
				# pid = data[value-1].split("|")[1]
				# price = data[value-1].split("|")[4]

				# category = data[value-1].split("|")[5]
				# record.insert({userID:{"VALUE":data}})
				# #print(userID," ",data)
				# secondary_index.insert({"PRODUCTID":pid,"PRICE":price,"CATEGORY":category})
			#print(pid," ",price," ",category)

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

