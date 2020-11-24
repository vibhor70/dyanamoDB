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
from tinydb.operations import delete


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
		print(criteria)
		self.run_command(criteria)

	def run_command(self, criteria):
		if criteria["COMMAND"] == "INSERT":
			self.concurrency_check(criteria)
		elif criteria["COMMAND"] == "RETRIEVE":
			self.list_all(criteria)
		elif criteria["COMMAND"] == "REPLACE":
			self.replace(criteria)
		elif criteria["COMMAND"] == "DELETE":
			self.delete_product(criteria)

	def delete_product(self,criteria):
		User = Query()
		userid = criteria["USERID"]
		to_store = db.search(User["USERID"] == criteria["USERID"])
		if not to_store:
			print("No user with user id exists")
			return
		query = (User.USERID == criteria["USERID"])
		db.update(delete('PRODUCTS'), query)
		productid = criteria["PRODUCTID"]
		toChange = to_store[0]["PRODUCTS"]
		newList=[]
		print(toChange)
		for val in toChange:
			print(val)
			if val["ID"] == productid:
				pass
			else:
				newList.append(val)
		db.update({'PRODUCTS': newList}, query)

		
	def replace(self,criteria):
		User = Query()
		userid = criteria["USERID"]
		db.update({'PRODUCTS': criteria["UPDATEDLIST"]}, User.USERID == userid)
		return True

	def list_all(self, criteria):
		User = Query()
		userid = criteria["USERID"]
		user_products = db.search(User["USERID"] == criteria["USERID"])
		if user_products:
			print(user_products)
			print(str(user_products[0]["PRODUCTS"]).encode())
			self.reliable_send(str(user_products[0]["PRODUCTS"]).encode())
		else:
			self.reliable_send("NO RECORD FOUND".encode())

	@staticmethod
	def get_store_dict(criteria, version):
		return {
			'USERID': criteria["USERID"],
			'PRODUCTS': [
					{
						"ID": criteria["PRODUCTID"],
						"PRICE": criteria["PRICE"],
						"CATEGORY": criteria["CATEGORY"],
						"LATEST_VERSION_VECTOR": version,
						"OPERATIONS": [
							{
								"OPERATION": criteria["OPERATION"],
								"VERSION_VECTOR": version
							}
						]
					
					}
				]
			}

	def concurrency_check(self, criteria):
		User = Query()
		# query = {
		# 	'USERID': criteria["USERID"],
		# 	'PRODUCTS': {
		# 			"ID": criteria["PRODUCTID"],
		# 		}
		# 	}
		print("/" + criteria["USERID"] + "/" + criteria["PRODUCTID"],
			"/" + self.DEVICE + "/" + criteria["USERID"] + "/" + criteria["PRODUCTID"]
		)
		query = (User.USERID == criteria["USERID"]) & (User.PRODUCTS.all(Query().ID == criteria["PRODUCTID"]))
		db_user_product = db.search(query)

		print(db_user_product, "user produt in concurrecny query")
		if not db_user_product: # if product and user id DNE, simply push the 1st operation
			path = "/" + criteria["USERID"] + "/" + criteria["PRODUCTID"] + '/' + self.DEVICE 
			path_rev = "/" + self.DEVICE + "/" +criteria["USERID"] + "/" + criteria["PRODUCTID"]
			print(path, path_rev)

			if self.kmaster.exist("path"):
				# pass
				gateway = Gateway()
				gateway.read_repair({"NODES":[self.DEVICE,]})
			else:
				self.kmaster.create(path)
				self.kmaster.create(path_rev)

				to_store = self.get_store_dict(criteria, "0")
				db.upsert(to_store, query)
				self.kmaster.setVersion(path, 0)
		else:
			version = int(db_user_product[0]["PRODUCTS"][0]['LATEST_VERSION_VECTOR'])
			# version = to_store[0]['PRODUCT'][-1]
			# if len(version) > 1:
			# 	version = int(version[-1][-1])
			# else:
			# 	version =int(version[-1])

			path = "/" +criteria["USERID"]+ "/"+ criteria["PRODUCTID"] + "/" + self.DEVICE
			path_rev = "/" + self.DEVICE + "/" + criteria["USERID"]+ "/"+ criteria["PRODUCTID"] 
			zversion = int(self.kmaster.retrieve(path))
			print(zversion, "zversion", type(zversion))
			print(version, "version", type(version))
			
			version = version + 1
			if zversion != version:
				self.reliable_send("CONCURRENT TRANSACTION : ".encode())
				print("CONCURRENT TRANSACTION")
				return # handle concurrent
				# pass

			"""Why more checking?"""			
			# to_store = db.search(User["USERID"] == criteria["USERID"])
			# dbversion = to_store[0]['PRODUCT'][-1]


			# if len(dbversion) > 1:
			# 	dbversion = dbversion[-1][-1]
			# else:
			# 	dbversion = dbversion[-1]

			# if dbversion  == version :
			# 	print("CONCURRENT")
			# 	self.reliable_send("CONCURRENT TRANSACTION : ".encode())
			
			# to_store_updated = self.get_store_dict(criteria, str(version))
			# print(to_store_updated, "new to_store updated")
			# to_store_updated = {
			# 	'USERID': criteria["USERID"], 
			# 	'PRODUCT_INFO': [criteria["PRODUCTID"],criteria["OPERATION"],criteria["PRICE"],criteria["CATEGORY"],version
			# ]}

			self.kmaster.setVersion(path, version)
			self.kmaster.setVersion(path_rev, version)
			# to_append = [criteria["PRODUCTID"],criteria["OPERATION"],criteria["PRICE"],criteria["CATEGORY"],version] # TODO: UPDATE
			# temp = db.search(User["USERID"] == criteria["USERID"])
			# new = []
			# new.append(temp[0]["PRODUCT"])
			# new.append(to_append) 
			# db.update(delete('USERID'), User["USERID"] == criteria["USERID"] )
			# db.insert({
			# 	'USERID': criteria["USERID"],
			# 	'PRODUCT': new
			# })


			# update lastest version vector 
			db_user_product[0]["PRODUCTS"][0]['LATEST_VERSION_VECTOR'] = str(version)
			## append the operation and update
			db_user_product[0]["PRODUCTS"][0]['OPERATIONS'].append(
				{"OPERATION": criteria["OPERATION"], "VERSION_VECTOR": str(version)}
			)
			print(db_user_product)
			db.update(db_user_product)
			

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
