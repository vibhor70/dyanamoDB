from kazoo.client import KazooClient
from kazoo.recipe.watchers import DataWatch
import logging
import sys

"""
Usage: python delete.py ip nodename
"""

logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)

if len(sys.argv) != 3:
    print("Provide 2 arguements: ip, node name")
    sys.exit(0)

ip = sys.argv[1]
node_name = sys.argv[2]

zk = KazooClient(hosts='{}:2181'.format(ip), read_only = False)
zk.start()


if zk.exists(node_name):
    print("Node {} in ip {} exists".format(node_name))
else:
    print("Node {} in ip {} does not exists".format(node_name))
    raise Exception("Node does not exists")
    sys.exit(0)

try:
    zk.delete(node_name, recursive = True)
except Exception as e:
    logging.info("Error whle updating Node " + node_name)

zk.stop()
