#!/usr/bin/python
import socket
import subprocess
import json
import os
import sys
import base64
import threading
from tinydb import TinyDB, Query
import struct
from kazooMaster import kazooMaster
from gateway import Gateway

db = TinyDB('db/db.json', indent=4, separators=(',', ': '))


# record = TinyDB("records.json")
# secondary_index = TinyDB("secondary.json")

# TO DO SET INDIVIDUAL self.DEVICE ID's FOR EACH CONTAINER


class Node(object):
	def __init__(self, IP_CONNECT, DEVICE):
		self.DEVICE = DEVICE
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.sock.connect((IP_CONNECT,54321))
    		
		self.kmaster = kazooMaster(IP_CONNECT, "p", "", "", "", "")
		self.kmaster.start_client()

	def reliable_send(self, data):
		self.sock.sendall(data)

	def run(self):
		while True:
			print("Listening")
			data_recv = self.reliable_recv()
			if not data_recv:
				continue
			

	def recvall(self, n):
		# Helper function to recv n bytes or return None if EOF is hit
		data = bytearray()
		while len(data) < n:
			packet = self.sock.recv(n - len(data))
			if not packet:
				return None
			data.extend(packet)
		return data

	def reliable_recv(self):
		raw_msglen = self.recvall(4)
		if not raw_msglen:
			return None
		msglen = struct.unpack('>I', raw_msglen)[0]
		data = self.recvall(msglen)
		#print(data.decode())
		criteria = data.decode()
		criteria = json.loads(criteria)

		t1 = threading.Thread(target = self.concurrency_check, args=(criteria))
		t1.start()

	def concurrency_check(self, criteria):
		if db.search(Query()["userid"] == criteria["userid"]) == None:
			path = "/" + criteria["userid"] + "/" + criteria["productid"] 
			path_rev = "/" + self.DEVICE + "/" +criteria["userid"] + "/" + criteria["productid"]
			if self.kmaster.exist("path"):
				pass
				# Gateway.read_repair({"NODES":self.DEVICE})
			else:
				to_store = {
					'userid': criteria["userid"],
					'product': [
						criteria["productid"],
						criteria["operation"],
						criteria["price"],
						criteria["category"],
						"0"
					]
				}
				db.insert(to_store)
				self.kmaster.setVersion(path,b"0")
		else:
			to_store = db.search(Query()["userid"] == criteria["userid"])
			version = to_store[0]['product'][4]

			path = "/" +criteria["userid"]+ "/"+ criteria["productid"] + "/" + self.DEVICE
			path_rev = "/" + self.DEVICE + "/" + criteria["userid"]+ "/"+ criteria["productid"] 
			zversion = self.kmaster.retrieve(path)
			if zversion != version:
				reliable_send("CONCURRENT TRANSACTION : INITIATING READ REPAIR")
				pass
				# Gateway.read_repair({"NODES":self.DEVICE})
			else:
				version = version + 1
				to_store = db.search(Query()["userid"] == criteria["userid"])
				dbversion = to_store[0]['PRODUCT_INFO'][4]
				if dbversion  == version :
					print("CONCURRENT")
					reliable_send("CONCURRENT TRANSACTION : INITIATING READ REPAIR")
				else:

					to_store = {'USERID': criteria["USERID"], 'PRODUCT_INFO': [criteria["PRODUCTID"],criteria["OPERATION"],criteria["PRICE"],criteria["CATEGORY"],version]}
					self.kmaster.setVersion(path,version)
					self.kmaster.setVersion(path_rev,version)
					db.insert(to_store)

		"""
		implement concurrency here
		read from saved file version number and than from zookeeper if fault tell client
		"""
		#print(criteria["DevID"])
		# for val in criteria["DevID"]:
		# 	self.kmaster = kazooMaster(
		# 				"172.17.0.3", "p", val, criteria["userid"], 
		# 				criteria["productid"], criteria["operation"]
		# 			)
		# 	self.kmaster.start_client()
		# 	#         
		# 	#use version vectors for concurrency
		# 	if self.kmaster 
		return True


		def __del__(self):
			self.sock.close()


def run_node():
	if len(sys.argv) != 3:
		print("Please provide <IP> <DEVICE name>")
		sys.exit(-1)
	IP_CONNECT = sys.argv[1]
	DEVICE = sys.argv[2]
	node = Node(IP_CONNECT, DEVICE)
	node.run()

if __name__ == "__main__":
	run_node()




# [
# 	{
# 	"USER": "USER1"
# 	"PRODUCTS": [
# 		"P1":[
# 		 {
# 			"HISTORY":[
# 				{"OPERATION": "ADD", VERSION_VEC: 1},
# 				{"OPERATION": "ADD", VERSION_VEC: 2},
# 				{"OPERATION": "ADD", VERSION_VEC: 3},
# 				{"OPERATION": "ADD", VERSION_VEC: 5},
# 				{"OPERATION": "ADD", VERSION_VEC: 4},
# 				{"OPERATION": "DELETION", VERSION_VEC: 6},
# 			],
# 			"LATEST_VERSION_VEC": 6
# 		},
# 	],
# 	},
# ]
