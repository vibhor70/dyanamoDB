from gateway import Gateway
import struct
import json
import socket

class GatewayClient(object):
	def __init__(self, gateway_ip):
		self.gateway_instance = Gateway(gateway_ip)
		self.CONFIG = self.get_config()
		self.API_IP = self.CONFIG["api_server"]
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.sock.connect((self.API_IP,44123))

	@staticmethod
	def get_config():
		with open("./config/config.json") as fin:
			return json.loads(fin.read())

	def run(self):
		while True:
			print("Listening to device: API SERVER ".format(self.API_IP))
			data_recv = self.reliable_recv()
			if not data_recv:	continue

	def recvall(self, n):
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

	def reliable_send(self, data):
		self.sock.sendall(data)

	def run_command(self, criteria):
		if criteria["COMMAND"] == "INSERT":
			response = self.gateway_instance.insert(criteria)
			# result_json = json.dumps({"success": True})
			# self.reliable_send(result_json.encode())

		if criteria["COMMAND"] == "LIST_ALL":
    		# list all the products of all the user 
			# from wherever the products are present
			res = self.gateway_instance.list_all_user_products(criteria)
			print(res, "LISTALL in gateway client")
			products = json.dumps({"data":res})
			self.reliable_send(products.encode())

		if criteria["COMMAND"] == "DELETE":
			self.gateway_instance.delete(criteria)
			print("Delete in gateway client")
			# response = json.dumps({"success": True})
			# self.reliable_send(response.encode())

		if criteria["COMMAND"] == "LIST_CATEGORY":
			res = self.gateway_instance.list_category(criteria)
			print(res, "IN GATEWAY CLIENT")
			products = json.dumps({"data":res})
			self.reliable_send(products.encode())


if __name__ == "__main__":
	import sys
	if len(sys.argv) != 2:
		print("Gateway IP required")
		sys.exit(-1)

	g = GatewayClient(sys.argv[1])
	g.run()