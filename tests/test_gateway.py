from ..gateway import Gateway

gatway_ip = "172.17.0.6"
gatway = Gateway(gatway_ip)



data = {
    "USERID": "user_1",
    "PRODUCTID": "toothpaste",
    "OPERATION": "ADD",
    "PRICE":"4000","CATEGORY":"3",
    "COMMAND":"INSERT"
}

gatway.insert(data)


data = {
    "USERID": "user_1",
    "PRODUCTID": "toothpaste",
    "OPERATION": "ADD",
    "PRICE":"4","CATEGORY":"30",
    "COMMAND":"INSERT"
}

gatway.insert(data)


data = {
    "USERID": "user_2",
    "PRODUCTID": "brush",
    "OPERATION": "ADD",
    "PRICE":"4","CATEGORY":"1",
    "COMMAND":"INSERT"
}
gatway.insert(data)

gatway.list_all({"USERID": "user_1"})

gatway.delete({"USERID": "user_2", "PRODUCTID": "brush"})
gatway.delete({"USERID": "user_1", "PRODUCTID": "toothbrush"})
