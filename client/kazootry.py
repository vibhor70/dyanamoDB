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
        self.operation =operation
        if type_ == "e" or type_ == "E":
            self.path = "/"+self.node
        else:
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
    def stat(self,node):
        stop=4
        zk = KazooClient(hosts='{}:2181'.format(self.ip), read_only = False)
        zk.start()

        @zk.DataWatch("{}".format(self.path))
        def my_func(data,stat):
            nonlocal stop
            stop =stop -1
            if stat is None:
                return 
            print("changed")
            print("Data is {} ".format(data))
            print("Version is {} ".format(stat.version))

        if zk.exists(self.path) !=None:
            val=DataWatch(zk,self.path,func=my_func)
            print(type(val),"VAL:",val)

            if not val:
                return -1
            while stop > 0:
                continue
        else:
            print("PATH INVALID")




a=kazooMaster("172.17.0.3","epe1","","","")
val=a.stat("/epe1")

print("Node Lost")


