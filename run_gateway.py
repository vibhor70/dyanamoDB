from gateway import Gateway
import sys

if len(sys.argv) != 2:
    print("Gateway ip dedo bhai")
    sys.exit(-1)

gatway_ip = sys.argv[1]
gatway = Gateway(gatway_ip)
gatway.list_all({
    "USERID": "1"
})



"""
from gateway import Gateway

gatway_ip = "172.17.0.6"
gatway = Gateway(gatway_ip)
# for i in range(5):

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



"""