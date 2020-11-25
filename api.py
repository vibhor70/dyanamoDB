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
        self.GATEWAY_INSTANCES = []

    def get_config(self):
        with open("./config/config.json") as fin:
            return json.loads(fin.read())

    def run(self):
        for gip in GATEWAY_IPS:
            # ginstance
            GATEWAY_INSTANCES.append(gip)
            gnode = SocketServer(gip)
            t = threading.Thread(target = self.run_mmnode_thread)
            t.start()

    def run_mmnode_thread(self):
        self.mnode.connection_accept()

app = FastAPI()

class ListAllQuery(BaseModel):
    userid: str

@app.get("/api/list_all")
async def list_all(query: ListAllQuery):
    gatway = Gateway(GATEWAY_IPS[0])
    res = gatway.list_all({"USERID": query["userid"]})
    return {"response": res}

class InsertQuery(BaseModel):
    userid: str
    productid: str
    operation: str
    price: str
    category: str

@app.get("/api/insert")
async def insertion_api(query: InsertQuery):
    gatway = Gateway(GATEWAY_IPS[0])
    data = {
        "USERID": query["userid"],
        "PRODUCTID": query["productid"],
        "OPERATION": query["operation"],
        "PRICE":query["price"],
        "CATEGORY":query["category"],
        "COMMAND":"INSERT"
    }
    gatway.insert(data)
    return {"response": "Added to cart"}


class DeletionQuery(BaseModel):
    userid: str
    productid: str

@app.get("/api/delete")
async def deletion_api(query: DeletionQuery):
    gatway = Gateway(GATEWAY_IPS[0])
    data = {
        "USERID": query["userid"],
        "PRODUCTID": query["productid"],
        "COMMAND":"DELETION"
    }
    gatway.delete(data)
    return {"response": "Deleted from cart"}