from fastapi import FastAPI
from pydantic import BaseModel
from gateway import Gateway
import random

gatway_ip = [
    "172.17.0.6",
    "172.17.0.7"
]


app = FastAPI()

class ListAllQuery(BaseModel):
    userid: str

@app.get("/api/list_all")
async def list_all(query: ListAllQuery):
    gatway = Gateway(gatway_ip[0])
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
    gatway = Gateway(gatway_ip[0])
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
    gatway = Gateway(gatway_ip[0])
    data = {
        "USERID": query["userid"],
        "PRODUCTID": query["productid"],
        "COMMAND":"DELETION"
    }
    gatway.delete(data)
    return {"response": "Deleted from cart"}