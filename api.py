from fastapi import FastAPI
from pydantic import BaseModel
from gateway import Gateway
import random
import json

def get_config():
    with open("./config.json") as fin:
        return json.loads(fin.read())

CONFIG = get_config()
GATEWAY_IPS = CONFIG["gateway_ips"]
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