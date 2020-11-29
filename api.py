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
Flaged_ip = {}
app = FastAPI()

class ListAllQuery(BaseModel):
    userid: str

class ListCategoryQuery(BaseModel):
    category: str

class InsertQuery(BaseModel):
    userid: str
    productid: str
    price: str
    category: str

class DeletionQuery(BaseModel):
    userid: str
    productid: str

'''
{
      "ID": "5",
      "PRICE": "1",
      "CATEGORY": "1",
      "LATEST_VERSION_VECTOR": "0",
      "OPERATIONS": [
        {
          "OPERATION": "ADD",
          "VERSION_VECTOR": "0"
        }
      ]
    }
}
'''


@app.post("/api/list_all")
async def list_all(query: ListAllQuery):
    GIP = random.choice(GATEWAY_IPS)
    APISOCK.send_command(
        [GIP,],
        {"USERID": query.userid, "COMMAND": "LIST_ALL"}
    )
    target = APISOCK.targets[GIP]
    res = APISOCK.reliable_recv(target)
    res = json.loads(res)
    response = []
    for r in res["data"]:
        qty = 0
        for op in r["OPERATIONS"]:
            if op["OPERATION"] == "ADD":
                qty+=1
            elif op["OPERATION"] == "DELETE":
                qty-=1

        response.append({
            "name": r["ID"],
            "price": r["PRICE"],
            "category": r["CATEGORY"],
            "qty": qty
        })

    return {"response": response}


@app.post("/api/list_category")
async def list_category(query: ListCategoryQuery):
    GIP = random.choice(GATEWAY_IPS)
    APISOCK.send_command(
        [GIP,],
        {"CATEGORY": query.category, "COMMAND": "LIST_CATEGORY"}
    )
    target = APISOCK.targets[GIP]
    res = APISOCK.reliable_recv(target)
    res = json.loads(res)
    users = set()
    for r in res:
        for u in r["PRODUCT"]:
            users.add(u)
    return {"response": list(users)}



@app.post("/api/insert")
async def insert_api(query: InsertQuery):
    GIP = random.choice(GATEWAY_IPS)
    data = {
        "USERID": query.userid,
        "PRODUCTID": query.productid,
        "OPERATION": "ADD",
        "PRICE":query.price,
        "CATEGORY":query.category,
        "COMMAND":"INSERT",
    }
    target = APISOCK.targets[GIP]
    APISOCK.send_command([GIP,], data)
    res = APISOCK.reliable_recv(target)
    res = json.loads(res)
    return {"response": "Added to cart"}


@app.post("/api/delete")
async def delete_api(query: DeletionQuery):
    GIP = random.choice(GATEWAY_IPS)
    data = {
        "USERID": query.userid,
        "PRODUCTID": query.productid,
        "COMMAND":"DELETE",
        "OPERATION": "DELETE"
    }
    APISOCK.send_command([GIP,], data)
    return {"response": "Deleted from cart"}