from gateway import Gateway
import struct
import json

class GatewayClient(object):
    def __init__(self, gateway_ip):
        self.gateway_instance = Gateway(gateway_ip)

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

    def run_command(self, criteria):
        if criteria["COMMAND"] == "INSERT":
            self.gateway_instance.insert(criteria)
        if criteria["COMMAND"] == "LIST_ALL":
            self.gateway_instance.list_all(criteria)
        if criteria["COMMAND"] == "DELETE":
            self.gateway_instance.delete(criteria)