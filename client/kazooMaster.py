from kazoo.recipe.watchers import DataWatch
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
import logging


class kazooMaster(object):

    def __init__(self,ip,type_,node,userID,cartID,operation):
        self.ip = ip
        self.node = node
        self.type=type_
        self.userID = userID
        self.cartID = cartID
        self.operation = operation
        if type_ == "e" or type_ == "E":
            self.path = "/"+self.node
        else:
            self.path = "/"+self.userID+"/"+self.cartID+"/"+self.node
        self.version=""

        self.start_client()

    def start_client(self):
        self.zk = KazooClient(hosts='{}:2181'.format(self.ip), read_only = False)
        self.zk.start()

    def create(self):
        logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)

        if(self.path == ""):
            logging.error("PATH EMPTY")
        else:
            if self.zk.exists(self.path) == None:
                self.zk.create(self.path,value=b"version 1",makepath=True)
                #self.zk.create(self.path,self.operation.encode(),sequence=True)
            else:
                data,stat = self.zk.get(self.path)
                self.zk.set(self.path,str(stat.version).encode())
                #self.zk.create(self.path,self.operation.encode(),sequence=True)
        self.zk.stop()
#stat is blocking ,control will return to called object after ephemeral node crashes
    def stat(self,node):
        stop=4

        @self.zk.DataWatch("{}".format(self.path))
        def my_func(data,stat):
            nonlocal stop
            stop = stop -1
            if stat is None:
                return 
            print("changed")
            print("Data is {} ".format(data))
            print("Version is {} ".format(stat.version))

        if self.zk.exists(self.path) !=None:
            val=DataWatch(self.zk,self.path,func=my_func)
            print(type(val),"VAL:",val)
            if not val:
                return -1
            while stop > 0:
                continue
        else:
            print("PATH INVALID")
        
        self.zk.stop()

    def delete(self, node_name):
        if self.zk.exists(node_name):
            print("Node {} in ip {} exists".format(node_name))
        else:
            print("Node {} in ip {} does not exists".format(node_name))
            raise Exception("Node does not exists")
        try:
            self.zk.delete(node_name, recursive = True)
        except Exception as e:
            logging.info("Error whle updating Node " + node_name)

        self.zk.stop()

    def retrieve(self):
        if self.zk.exists(self.path) == None:
            return -1
        else:
            data,version_number = self.zk.get(self.path)
            version_number = str(version_number.version)
            return version_number

a=kazooMaster("172.17.0.3","p","1","usr1","cart1","ADD")
val=a.create()

print("Node Lost")


