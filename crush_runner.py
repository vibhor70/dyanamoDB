import json
from crush import Crush
import sys
import cPickle
import binascii
#1: CREATE CRUSH CLASS 
#2:(METHOD )TAKE INPUT VALUES USERID , PRODUCTID AND MAP IT INTO DEVICES,RETURN (USERID,PRODUCTID,DEVICE),...
#2:(METHOD)TAKE WHICH NODE DELETED AS PARAMETER AND UPDATE JSON MAP AND RELOAD THAT MAP AGAIN


if len(sys.argv) != 4:
    print("Provide 4 arguements: ip, node name, node val cmap")
    raise Exception("Provide 4 arguements: ip, node name, node val")
    sys.exit(0)

value = sys.argv[1]
rcount = sys.argv[2]
crushmap = cPickle.loads(binascii.unhexlify(sys.argv[3].encode()))

c = Crush()
c.parse(crushmap)
devices = c.map(rule="data", value=int(value), replication_count=int(rcount))
print("\n".join([str(device) for device in devices]))

