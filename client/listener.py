from kazoo.recipe.watchers import DataWatch
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
import logging

zk = KazooClient(hosts='172.17.0.2:2181', read_only=True)

def my_listener(state):
    print("in listener")
    if state == KazooState.LOST:
        logging.info('Session lost')
    elif state == KazooState.SUSPENDED:
        logging.info('Disconnected')
    elif state == KazooState.CONNECTED:
        print("Connected to client")
        logging.info('Connected to Client')
        if zk.client_state == state.CONNECTED_RO:
            print("Read only mode!")
            logging.info("Read only mode!")
        else:
            logging.info("Read/Write mode!")
            print("Read/Write mode!")

        # zk.create("/vibhor",value=b"made by kazoo",makepath=True)


zk.start()
logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)
zk.add_listener(my_listener)
zk.stop()