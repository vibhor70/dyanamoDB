import json
from crush import Crush
import sys

if len(sys.argv) != 3:
    print("Provide 3 arguements: ip, node name, node val")
    raise Exception("Provide 3 arguements: ip, node name, node val")
    sys.exit(0)

value = sys.argv[1]
rcount = sys.argv[2]
crushmap = open("utils/crushmap.json", "r").read()

c = Crush()
c.parse(json.loads(crushmap))
print(c.map(rule="data", value=int(value), replication_count=int(rcount)))
