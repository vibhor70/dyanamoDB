from kazoo.recipe.watchers import DataWatch
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
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



logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)
zk.add_listener(my_listener)
zk.create("/vibhor",value=b"made by kazoo",makepath=True)


zk.stop()