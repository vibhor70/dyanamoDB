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

gatway_ip = "172.17.0.7"
gatway = Gateway(gatway_ip)
# for i in range(5):

data = {
    "userid": "1",
    "productid": "toothpaste",
    "operation": "ADD",
}

gatway.insert(data)


gatway.list_all({
    "USERID": "1"
})

"""