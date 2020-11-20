from kazoo.recipe.watchers import DataWatch
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
import logging



class kazooMaster(object):

    def __init__(self,ip,node,userID,cartID,operation):
        self.ip = ip
        self.node = node
        self.userID = userID
        self.cartID = cartID
        self.operation =operation
        self.path = "/"+self.node+"/"+self.cartID+"/"+self.userID
        self.version=""

    def create(self):
        logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)

        if(self.path == ""):
            logging.error("PATH EMPTY")
        else:
            zk = KazooClient(hosts='{}:2181'.format(self.ip), read_only = False)
            zk.start()
            if zk.exists(self.path) == None:
                zk.create(self.path,value=b"",makepath=True)
                zk.create(self.path,self.operation.encode(),sequence=True)
            else:
                zk.create(self.path,self.operation.encode(),sequence=True)
        zk.stop()




