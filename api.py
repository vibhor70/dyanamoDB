from fastapi import FastAPI
from pydantic import BaseModel
from gateway_client import GatewayClient
from socket_server import SocketServer

import random
import json
import threading
from tinydb import Query, TinyDB

class InventoryManagement(object):
    def __init__(self):
        self.db = TinyDB('db/inventory.json', indent=4, separators=(',', ': '))

    def add(self, item_name):
        Item = Query()
        item = self.db.get(Item.item == item_name)
        if item:
            qty = item["total_qty"]
            item.update({"total_qty":qty-1, "item": item})

    def delete(self, item_name):
        Item = Query()
        item = self.db.get(Item.item == item_name)
        if item:
            qty = item["total_qty"]
            item.update({"total_qty":qty+1, "item": item})

    def get_item_or_none(self, item_name):
        Item = Query()
        item = self.db.get(Item.item == item_name)
        if item:
            qty = item["total_qty"]
            category = item["category"]
            price = item["price"]
            return qty, category, price
        else:
            return None

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
inventory_mgmt = InventoryManagement()

class ListAllQuery(BaseModel):
    userid: str

class ListCategoryQuery(BaseModel):
    category: str

class InsertQuery(BaseModel):
    userid: str
    item_name: str

class DeletionQuery(BaseModel):
    userid: str
    item_name: str


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
        try:
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
        except:
            pass

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
    print(res, "result json loads")
    for r in res["data"]:
        try:
            for u in r["PRODUCT"]:
                users.add(u)
        except:
            pass
    return {"response": list(users)}



@app.post("/api/insert")
async def insert_api(query: InsertQuery):
    GIP = random.choice(GATEWAY_IPS)
    inventory_item = inventory_mgmt.get_item_or_none(query.item_name)
    if not inventory_item:
        return {"response": "No such item exists in inventory"}
    qty, category, price = inventory_item
    if qty == 0:
        return {"response": "Item is not longer available to add"} 
    data = {
        "USERID": query.userid,
        "PRODUCTID": query.item_name,
        "OPERATION": "ADD",
        "PRICE": price,
        "CATEGORY":category,
        "COMMAND":"INSERT",
    }
    target = APISOCK.targets[GIP]
    APISOCK.send_command([GIP,], data)
    # res = APISOCK.reliable_recv(target)
    # res = json.loads(res)
    inventory_mgmt.add(query.item_name)
    return {"response": "Added to cart"}


@app.post("/api/delete")
async def delete_api(query: DeletionQuery):
    GIP = random.choice(GATEWAY_IPS)
    inventory_item = inventory_mgmt.get_item_or_none(query.item_name)
    if not inventory_item:
        return {"response": "No such item exists in inventory"}
    qty, category, price = inventory_item

    data = {
        "USERID": query.userid,
        "PRODUCTID": query.item_name,
        "COMMAND":"DELETE",
        "OPERATION": "DELETE"
    }
    target = APISOCK.targets[GIP]
    APISOCK.send_command([GIP,], data)
    # res = APISOCK.reliable_recv(target)

    inventory_mgmt.delete(query.item_name)
    return {"response": "Deleted from cart"}