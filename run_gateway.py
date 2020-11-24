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