from kazoo.recipe.watchers import DataWatch
import logging
import sys

"""
Usage: python create.py ip nodename nodeval
"""

logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)

if len(sys.argv) != 4:
    print("Provide 3 arguements: ip, node name, node val")
    raise Exception("Provide 3 arguements: ip, node name, node val")
    sys.exit(0)

ip = sys.argv[1]
node_name = sys.argv[2]
node_value = sys.argv[3]

zk = KazooClient(hosts='{}:2181'.format(ip), read_only = False)
zk.start()


if zk.exists(node_name):
    print("Node {} in ip {} alrea".format(node_name))
    raise Exception("Node already exists")
    sys.exit(0)

try:
    zk.create(node_name, node_value.encode("utf-8"))
except Exception as e:
    logging.info("Error whle creating Node " + node_name)

zk.stop()
