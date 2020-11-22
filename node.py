#!/usr/bin/python
import socket
import subprocess
import json
import os
import base64
from tinydb import TinyDB, Query
import struct
from kazooMaster import kazooMaster
from gateway import Gateway
db = TinyDB('db.json')

IP_CONNECT = "127.0.0.1"
DEVICE = "dev1"
# record = TinyDB("records.json")
# secondary_index = TinyDB("secondary.json")

# TO DO SET INDIVIDUAL DEVICE ID's FOR EACH CONTAINER



kmaster = kazooMaster(
					IP_CONNECT, "p", "", "", 
				"", "")
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
	#print(data.decode())
	criteria = data.decode()
	criteria = json.loads(criteria)
	# print(criteria)
	# print(criteria["OPERATION"])

	#criteria["VERSION"]
	
	if db.search(Query()["USERID"] == "1") == None:
		path = "/" +criteria["USERID"]+ "/"+ criteria["PRODUCTID"] + "/" + DEVICE
		if kmaster.exist("path"):
			Gateway.read_repair({"NODES":DEVICE})
		else:
			to_store = {'USERID': criteria["USERID"], 'PRODUCT_INFO': [criteria["PRODUCTID"],criteria["OPERATION"],criteria["PRICE"],criteria["CATEGORY"],"0"]}
			db.insert(to_store)
	else:
		to_store = db.search(Query()["USERID"] == criteria["USERID"])
		version = to_store[0]['PRODUCT_INFO'][4]
		path = "/" +criteria["USERID"]+ "/"+ criteria["PRODUCTID"] + "/" + DEVICE
		path_rev = "/" +DEVICE + "/" + criteria["USERID"]+ "/"+ criteria["PRODUCTID"] 
		zversion = kmaster.retrieve(path)
		if zversion != version:
			Gateway.read_repair({"NODES":DEVICE})
		else:
			version = version + 1
			to_store = {'USERID': criteria["USERID"], 'PRODUCT_INFO': [criteria["PRODUCTID"],criteria["OPERATION"],criteria["PRICE"],criteria["CATEGORY"],version]}
			kmaster.setVersion(path,version)
			kmaster.setVersion(path_rev,version)
			db.insert(to_store)
	"""
	implement concurrency here
	read from saved file version number and than from zookeeper if fault tell client
	"""
	#print(criteria["DevID"])
	# for val in criteria["DevID"]:
	# 	kmaster = kazooMaster(
	# 				"172.17.0.3", "p", val, criteria["userid"], 
	# 				criteria["productid"], criteria["operation"]
	# 			)
	# 	kmaster.start_client()
	# 	#         
	# 	#use version vectors for concurrency
	# 	if kmaster 
	return True

def shell():
	
	while True:
		print("Listening")
		data_recv = reliable_recv()
		if data_recv :
			try:
				print("Successfully entered")
			except ValueError as e:
				print(e, "exception in db insert")
		

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((IP_CONNECT,54321))

shell()
sock.close()
kmaster.start_client()
