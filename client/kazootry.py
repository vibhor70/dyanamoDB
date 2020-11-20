from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
from kazoo.recipe.watchers import DataWatch
import logging


def my_listener(state):
    print("in listener")
    if state == KazooState.LOST:
        logging.info('Session lost')
    if state == KazooState.SUSPENDED:
        logging.info('Disconnected')
    else:
        print("Connected to client")
        logging.info('Connected to Client')
        


zk = KazooClient(hosts='172.17.0.2:2181')

zk.start()

@zk.DataWatch("/rmr")
def my_func(data,stat):
    print("changed")
    print("Data is {} ".format(data))
    print("Version is {} ".format(stat.version))


logging.basicConfig(filename='connection.log', filemode='w', level=logging.DEBUG)
zk.add_listener(my_listener)
DataWatch(zk,"/rmr",func=my_func)

i=1
while i > -1:
    i=i+1


zk.stop()
