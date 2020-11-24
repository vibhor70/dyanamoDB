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
		# create ephermeral node
		self.kmaster.create("/ephemeral_{}".format(DEVICE), "e")

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
		print(criteria)
		if criteria["COMMAND"] == "INSERT":
			self.insertion(criteria)
		elif criteria["COMMAND"] == "RETRIEVE":
			self.list_all(criteria)
		elif criteria["COMMAND"] == "REPLACE":
			self.replace(criteria)
		elif criteria["COMMAND"] == "DELETE":
			self.deletion(criteria)


		
	def replace(self,criteria):
    	# VERIFY vibhor
		print(criteria, "IN REPLACE")
		User = Query()
		userid = criteria["USERID"]
		updaed_products = criteria["UPDATEDLIST"]
		max_product_id = criteria["MAX_PRODUCTID"]
		user = db.get(User.USERID == userid)

		if not user:
			data = {
				"USERID": userid,
				"PRODUCTS": [criteria,]
			}
			db.insert(data)
			print("No such user exists in replace")
			return
		db_products = user["PRODUCTS"]
		print(db_products, "ORIGNAL db products")

		change_with = None
		for i, product in enumerate(updaed_products):
			if product["ID"] == max_product_id:
				change_with = updaed_products[i]
				break
		print("CHANGE WITH", change_with)
		if not change_with:
			return False

		for i, product in enumerate(db_products):
			if product["ID"] == max_product_id:
				db_products[i] = change_with
				print(db_products[i])
				break

		print(db_products, "new db products")	
		db.update({'PRODUCTS': db_products}, User.USERID == userid)
		return True

	def list_all(self, criteria):
		User = Query()
		userid = criteria["USERID"]
		user_products = db.get(User["USERID"] == criteria["USERID"])
		productID = criteria["PRODUCTID"]
		for product in user_products["PRODUCTS"]:
			if productID  == product["ID"]:
				# print(user_products)
				# print(str(user_products["PRODUCTS"]).encode())
				products = json.dumps({"PRODUCT":product})
				print(products, "in list_all")
				self.reliable_send(products.encode())
			else:
				products = json.dumps({"PRODUCT":{}})
				self.reliable_send(products.encode())

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



	def deletion(self,criteria):
		User = Query()
		print("IN DELETION")
		# query = (User.USERID == criteria["USERID"]) & (User.PRODUCTS.all(Query().ID == criteria["PRODUCTID"]))
		query = (User.USERID == criteria["USERID"])
		db_user_product = db.get(query)

		up_found = False
		if db_user_product:
			for db_user_prod in db_user_product["PRODUCTS"]:
				if db_user_prod["ID"] == criteria["PRODUCTID"]:
					up_found = True
					break

		path = "/" + criteria["USERID"] + "/" + criteria["PRODUCTID"] + '/' + self.DEVICE 
		path_rev = "/" + self.DEVICE + "/" +criteria["USERID"] + "/" + criteria["PRODUCTID"]

		if up_found: # if product and user id DNE, simply push the 1st operation
			for i, product in enumerate(db_user_product["PRODUCTS"]):
				if product["ID"] == criteria["PRODUCTID"]:
					version = int(db_user_product["PRODUCTS"][i]['LATEST_VERSION_VECTOR'])

			zversion = int(self.kmaster.retrieve(path))
			print(zversion, "zversion", type(zversion))
			print(version, "version", type(version))
			
			version = version + 1
			if zversion != version:
				print("CONCURRENT TRANSACTION in node")

			self.kmaster.setVersion(path, version)
			self.kmaster.setVersion(path_rev, version)

			for i, product in enumerate(db_user_product["PRODUCTS"]):
				if product["ID"] == criteria["PRODUCTID"]:
					db_user_product["PRODUCTS"][i]['LATEST_VERSION_VECTOR'] = str(version)
					## append the operation and update
					db_user_product["PRODUCTS"][i]['OPERATIONS'].append(
						{"OPERATION": "DELETE", "VERSION_VECTOR": str(version)}
					)
					break
			db.update(db_user_product)
		
		else:
			print("DELETION NOT POSSIBLE, USERID, PRODUCTD DOES NOT FOUND")


	def insertion(self, criteria):
		User = Query()
		print("IN insertion")
		print("/" + criteria["USERID"] + "/" + criteria["PRODUCTID"],
			"/" + self.DEVICE + "/" + criteria["USERID"] + "/" + criteria["PRODUCTID"]
		)
		# query = (User.USERID == criteria["USERID"]) & (User.PRODUCTS.all(Query().ID == criteria["PRODUCTID"]))
		query = (User.USERID == criteria["USERID"])

		db_user_product = db.get(query)

		up_found = False
		if db_user_product:
			for db_user_prod in db_user_product["PRODUCTS"]:
				if db_user_prod["ID"] == criteria["PRODUCTID"]:
					up_found = True
					break

		# print(db_user_product, "user produt in concurrecny query")
		if not up_found: # if product and user id DNE, simply push the 1st operation
			path = "/" + criteria["USERID"] + "/" + criteria["PRODUCTID"] + '/' + self.DEVICE 
			path_rev = "/" + self.DEVICE + "/" +criteria["USERID"] + "/" + criteria["PRODUCTID"]
			# print(path, path_rev)

			if self.kmaster.exist("path"):
				# pass
				gateway = Gateway()
				gateway.read_repair({"NODES":[self.DEVICE,]})
			else:
				self.kmaster.create(path)
				self.kmaster.create(path_rev)
				
				to_store = self.get_store_dict(criteria, "0")
				query = (User.USERID == criteria["USERID"])
				db_user = db.get(query)
				if db_user:
					print("db user found, not product")
					db_user["PRODUCTS"].append(to_store["PRODUCTS"][0])
					db.update(db_user)
				else:	
					print("db user not found")
					db.insert(to_store)

				self.kmaster.setVersion(path, 0)
		else:
			for i, product in enumerate(db_user_product["PRODUCTS"]):
				if product["ID"] == criteria["PRODUCTID"]:
					version = int(db_user_product["PRODUCTS"][i]['LATEST_VERSION_VECTOR'])

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
				# self.reliable_send("CONCURRENT TRANSACTION : ".encode())
				print("CONCURRENT TRANSACTION in node")
				# return # handle concurrent
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
			

			self.kmaster.setVersion(path, version)
			self.kmaster.setVersion(path_rev, version)
			# update lastest version vector 
			print("db user and db product both found")
			for i, product in enumerate(db_user_product["PRODUCTS"]):
				if product["ID"] == criteria["PRODUCTID"]:
					db_user_product["PRODUCTS"][i]['LATEST_VERSION_VECTOR'] = str(version)
					## append the operation and update
					db_user_product["PRODUCTS"][i]['OPERATIONS'].append(
						{"OPERATION": criteria["OPERATION"], "VERSION_VECTOR": str(version)}
					)
					break
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
