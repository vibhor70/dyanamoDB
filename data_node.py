#!/usr/bin/python
import base64
import json
import logging
import os
import socket
import struct
import subprocess
import sys
import threading

from tinydb import Query, TinyDB
from tinydb.operations import delete

from gateway import Gateway
from kazoo_master import kazooMaster

db = TinyDB('db/db.json', indent=4, separators=(',', ': '))
sec_index_db = TinyDB("db/secondary.json", indent=4, separators=(',', ': '))
logging.basicConfig(filename='logs/node.log', filemode='w', level=logging.INFO)

class DataNode(object):
	def __init__(self, IP_CONNECT, DEVICE):
		self.DEVICE = DEVICE
		self.IP_CONNECT = IP_CONNECT
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.sock.connect((IP_CONNECT,54321))
    		
		self.kmaster = kazooMaster(IP_CONNECT, "p", "", "", "", "")
		# create ephermeral node
		self.create_ephemeral_node()
		self.kmaster.start_client()
		logging.info("Node initialized")
		

	def create_ephemeral_node(self):
		try:
			self.kmaster.create("/ephemeral_{}".format(self.DEVICE), "e")
		except Exception as e:
			print("exception", e)
			logging.error("Error in creating ephermeral node" + str(e))

	def reliable_send(self, data):
		self.sock.sendall(data)

	def run(self):
		print(self.IP_CONNECT)
		while True:
			logging.info("Listening from device: {} and gateway ip: ".format(self.DEVICE, self.IP_CONNECT))
			print("Listening from device: {} and gateway ip: ".format(self.DEVICE, self.IP_CONNECT))
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
		self.run_command(criteria)

	def run_command(self, criteria):
		logging.info("In run command, with data = " + str(criteria))
		print("run command", criteria)
		if criteria["COMMAND"] == "INSERT":
			self.insertion(criteria)
			self.insert_secondary_index(criteria)
		elif criteria["COMMAND"] == "RETRIEVE":
			self.retrieve(criteria)
		elif criteria["COMMAND"] == "REPLACE":
			self.replace(criteria)
		elif criteria["COMMAND"] == "DELETE":
			self.deletion(criteria)
		elif criteria["COMMAND"] == "LISTCATEGORY":
			self.list_category(criteria)
		else:
			logging.info("No command found")

	def replace(self,criteria):
    	# VERIFY vibhor
		logging.info("In replace, with data = " + str(criteria))
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
			logging.info("No such user exists in replace")
			return

		db_products = user["PRODUCTS"]
		change_with = None
		for i, product in enumerate(updaed_products):
			if product["ID"] == max_product_id:
				change_with = updaed_products[i]
				break

		if not change_with:	return False

		for i, product in enumerate(db_products):
			if product["ID"] == max_product_id:
				db_products[i] = change_with
				break

		db.update({'PRODUCTS': db_products}, User.USERID == userid)
		return True

	def retrieve(self, criteria):
		logging.info("In retrieve, with data = " + str(criteria))
		User = Query()
		userid = criteria["USERID"]
		user_products = db.get(User["USERID"] == criteria["USERID"])
		print(user_products)
		if not user_products:
			products = json.dumps({"PRODUCT":{}})	
			self.reliable_send(products.encode())
			return

		productID = criteria["PRODUCTID"]
		for product in user_products["PRODUCTS"]:
			if productID  == product["ID"]:
				products = json.dumps({"PRODUCT":product})
				self.reliable_send(products.encode())
				return

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
		logging.info("In deletion, with data = " + str(criteria))
		User = Query()
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
			
			version = version + 1
			if zversion != version:
				logging.info("CONCURRENT TRANSACTION in node")

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
			logging.info("DELETION NOT POSSIBLE, USERID, PRODUCTD DOES NOT FOUND")


	def insert_secondary_index(self, criteria):
		logging.info("Inserting product secondary index for {}".format(str(criteria)))
		Product = Query()
		query = (Product.CATEGORY == criteria["CATEGORY"])
		product = db.get(query)
		print(product, "in insert sec index")
		if product:
			product["USERID"].append(criteria["USERID"])
			sec_index_db.update(product)
		else:
			sec_index_db.insert({
				"CATEGORY": criteria["CATEGORY"], 
				"USERID": [criteria["USERID"]]
			})
			
			
	def list_category(self,criteria):
		logging.info("Extracting product secondary index for {}".format(str(criteria)))
		Product = Query()
		query = (Product.CATEGORY == criteria["CATEGORY"])
		product = db.get(query)
		print(product, "in list category")
		if product:
			products = json.dumps({"PRODUCT":product["USERID"]})
			self.reliable_send(products.encode())
		else:
			products = json.dumps({"PRODUCT":[]})
			self.reliable_send(products.encode())

	def insertion(self, criteria):
		User = Query()
		logging.info("In insertion, with data = " + str(criteria))

		self.insert_secondary_index(criteria)

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

		if not up_found: # if product and user id DNE, simply push the 1st operation
			if self.kmaster.exist("path"):
				gateway = Gateway()
				gateway.read_repair({"NODES":[self.DEVICE,]})
			else:
				self.kmaster.create(path)
				self.kmaster.create(path_rev)
				
				to_store = self.get_store_dict(criteria, "0")
				db_user = db.get(query)
				if db_user:
					db_user["PRODUCTS"].append(to_store["PRODUCTS"][0])
					db.update(db_user)
				else:	
					db.insert(to_store)

				self.kmaster.setVersion(path, 0)
		else:
			for i, product in enumerate(db_user_product["PRODUCTS"]):
				if product["ID"] == criteria["PRODUCTID"]:
					version = int(db_user_product["PRODUCTS"][i]['LATEST_VERSION_VECTOR'])

			zversion = int(self.kmaster.retrieve(path))
			version = version + 1
			if zversion != version:
				logging.info("CONCURRENT TRANSACTION in node")

			self.kmaster.setVersion(path, version)
			self.kmaster.setVersion(path_rev, version)
			# update lastest version vector 
			for i, product in enumerate(db_user_product["PRODUCTS"]):
				if product["ID"] == criteria["PRODUCTID"]:
					db_user_product["PRODUCTS"][i]['LATEST_VERSION_VECTOR'] = str(version)
					## append the operation and update
					db_user_product["PRODUCTS"][i]['OPERATIONS'].append(
						{"OPERATION": criteria["OPERATION"], "VERSION_VECTOR": str(version)}
					)
					break
			db.update(db_user_product)

		return True

		def __del__(self):
			self.sock.close()


def run_node_thread(GATWWAY_IP, DEVICE):
	node = DataNode(GATWWAY_IP, DEVICE)
	node.run()

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Please provide <DEVICE name>")
		sys.exit(-1)

	DEVICE = sys.argv[1]
	with open("./config/config.json") as f:
		config = f.read()
		config = json.loads(config)
		gateway_ips = config["gateway_ips"]

		for gip in gateway_ips:
			t = threading.Thread(target = run_node_thread, args=(gip, DEVICE))
			t.start()
