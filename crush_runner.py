import json
from crush import Crush
import sys

#1: CREATE CRUSH CLASS 
#2:(METHOD )TAKE INPUT VALUES USERID , PRODUCTID AND MAP IT INTO DEVICES,RETURN (USERID,PRODUCTID,DEVICE),...
#2:(METHOD)TAKE WHICH NODE DELETED AS PARAMETER AND UPDATE JSON MAP AND RELOAD THAT MAP AGAIN


if len(sys.argv) != 3:
    print("Provide 3 arguements: ip, node name, node val")
    raise Exception("Provide 3 arguements: ip, node name, node val")
    sys.exit(0)

value = sys.argv[1]
rcount = sys.argv[2]
crushmap = open("./config/crushmap.json", "r").read()

c = Crush()
c.parse(json.loads(crushmap))
devices = c.map(rule="data", value=int(value), replication_count=int(rcount))
print("\n".join([str(device) for device in devices]))