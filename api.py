from fastapi import FastAPI
from pydantic import BaseModel
from gateway_client import GatewayClient
from socket_server import SocketServer

import random
import json
import threading


class ConnectGateway(object):
    def __init__(self):
        self.GATEWAY_IPS = self.get_config()["gateway_ips"]
        self.GATEWAY_SOCKS = []

    @staticmethod
    def get_config():
        with open("./config/config.json") as fin:
            return json.loads(fin.read())

    def run(self):
        for gip in GATEWAY_IPS:
            # ginstance
            gnode_sock = SocketServer(gip)
            self.GATEWAY_SOCKS.append(gnode_sock)
            t = threading.Thread(target = self.run_mmnode_thread, args=(gnode_sock))
            t.start()

    @staticmethod
    def run_mmnode_thread(gnode_sock):
        gnode_sock.connection_accept()

    def get_gateway_socks(self):
        return self.GATEWAY_SOCKS



gateways = ConnectGateway()
gateways.run()
GSOCKS = gateways.get_gateway_socks()

app = FastAPI()

class ListAllQuery(BaseModel):
    userid: str

@app.get("/api/list_all")
async def list_all(query: ListAllQuery):
    GSOCK = random.choice(GSOCKS)
    res = GSOCK.send_command({
        "USERID": query["userid"],
        "COMMAND": "LIST_ALL"
    })
    return {"response": res}

class InsertQuery(BaseModel):
    userid: str
    productid: str
    operation: str
    price: str
    category: str

@app.get("/api/insert")
async def insertion_api(query: InsertQuery):
    GSOCK = random.choice(GSOCKS)
    data = {
        "USERID": query["userid"],
        "PRODUCTID": query["productid"],
        "OPERATION": query["operation"],
        "PRICE":query["price"],
        "CATEGORY":query["category"],
        "COMMAND":"INSERT"
    }
    GSOCK.send_command(data)
    return {"response": "Added to cart"}

class DeletionQuery(BaseModel):
    userid: str
    productid: str

@app.get("/api/delete")
async def deletion_api(query: DeletionQuery):
    GSOCK = random.choice(GSOCKS)
    data = {
        "USERID": query["userid"],
        "PRODUCTID": query["productid"],
        "COMMAND":"DELETION"
    }
    GSOCK.send_command(data)
    return {"response": "Deleted from cart"}