from fastapi import FastAPI
from pydantic import BaseModel
from gateway_client import GatewayClient
from socket_server import SocketServer

import random
import json
import threading


class ConnectGateway(object):
    def __init__(self):
        self.CONFIG = self.get_config()
        self.GATEWAY_IPS = self.CONFIG["gateway_ips"]
        self.GATEWAY_SOCKS = []
        self.CONTAINER_IP = self.CONFIG["api_server"]
        self.APISOCK = SocketServer(self.CONTAINER_IP, 44123)
        t = threading.Thread(target = self.run_APISOCK_thread)
        t.start()

    @staticmethod
    def get_config():
        with open("./config/config.json") as fin:
            return json.loads(fin.read())

    def run_APISOCK_thread(self):
        self.APISOCK.connection_accept()

    def get_gateway_ips(self):
        return self.GATEWAY_IPS

    def get_sock(self):
        return self.APISOCK

api_sock_server = ConnectGateway()
GATEWAY_IPS = api_sock_server.get_gateway_ips()
APISOCK = api_sock_server.get_sock()

app = FastAPI()

class ListAllQuery(BaseModel):
    userid: str

class ListCategory(BaseModel):
    category: str

class InsertQuery(BaseModel):
    userid: str
    productid: str
    price: str
    category: str

class DeletionQuery(BaseModel):
    userid: str
    productid: str

@app.post("/api/list_all")
async def list_all(query: ListAllQuery):
    GIP = random.choice(GATEWAY_IPS)
    APISOCK.send_command(
        [GIP,],
        {"USERID": query.userid, "COMMAND": "LIST_ALL"}
    )
    target = APISOCK.targets[APISOCK.ips.index(GIP)]
    res = APISOCK.reliable_recv(target)
    res = json.loads(res)
    return {"response": res["data"]}


@app.post("/api/list_catgory")
async def list_all(query: ListCategory):
    GIP = random.choice(GATEWAY_IPS)
    APISOCK.send_command(
        [GIP,],
        {"USERID": query.userid, "COMMAND": "LIST_CATEGORY"}
    )
    target = APISOCK.targets[APISOCK.ips.index(GIP)]
    res = APISOCK.reliable_recv(target)
    res = json.loads(res)
    return {"response": res["data"]}



@app.post("/api/insert")
async def insertion_api(query: InsertQuery):
    GIP = random.choice(GATEWAY_IPS)
    data = {
        "USERID": query.userid,
        "PRODUCTID": query.productid,
        "OPERATION": "ADD",
        "PRICE":query.price,
        "CATEGORY":query.category,
        "COMMAND":"INSERT"
    }
    APISOCK.send_command([GIP,], data)
    return {"response": "Added to cart"}


@app.post("/api/delete")
async def deletion_api(query: DeletionQuery):
    GIP = random.choice(GATEWAY_IPS)
    data = {
        "USERID": query.userid,
        "PRODUCTID": query.productid,
        "COMMAND":"DELETE",
        "OPERATION": "DELETE"
    }
    APISOCK.send_command([GIP,], data)
    return {"response": "Deleted from cart"}