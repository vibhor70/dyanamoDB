from kazoo.recipe.watchers import DataWatch
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
import logging


class kazooMaster(object):

    def __init__(self,ip,type_="p",node="",userID="",pid="",operation="",remap=False):
        self.ip = ip
        self.node = node
        self.type=type_
        self.userID = userID
        self.productID = pid
        self.operation = operation
        self.path_rev = ""
        if type_ == "e" or type_ == "E":
            self.path = "/"+self.node
        else:
            self.path_rev = "/"+self.node+"/"+self.userID+"/"+self.productID
            self.path = "/"+self.userID+"/"+self.productID+"/"+self.node
        self.version=""
        self.remap = remap
        self.start_client()

    def start_client(self):
        self.zk = KazooClient(hosts='{}:2181'.format(self.ip), read_only = False)
        self.zk.start()

    def start_client_async(self):
        self.zk = KazooClient(hosts='{}:2181'.format(self.ip), read_only = False)
        self.zk.start_async()

    def children_watch(self, path = None):
        if path is None:
            path = self.path
        print(path)
        @self.zk.ChildrenWatch(path)
        def watch_children(children):
            print("Children are now: %s" % children)
        # Above function called immediately, and from then on

    def stop_client(self):
        self.zk.stop()
    
    def get_children(self,path):
        print(path, "in get children")
        return self.zk.get_children(path)

    def exist(self,path):
        if self.zk.exists(path) == None:
            return False
        else:
            return True

    def create(self, path, param = "p"):
        ephemeral = False
        if param == "p":
            ephemeral = False
        elif param == "e":
            ephemeral = True
            
        logging.basicConfig(filename='logs/connection.log', filemode='w', level=logging.DEBUG)

        if(self.path == ""):
            logging.error("PATH EMPTY")
            return False
        else:
            if self.zk.exists(path) == None:
                self.zk.create(path, value=b"0", makepath=True, ephemeral = ephemeral)
                # self.zk.create(self.path_rev,value=b"0",makepath=True)
                return True
        return False

#stat is blocking ,control will return to called object after ephemeral node crashes
    def stat(self):
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

    def retrieve(self, custom_path = None):
        if not custom_path:
            custom_path = self.path
            
        if self.zk.exists(self.path) == None:
            return -1
        else:
            data,version_number = self.zk.get(custom_path)
            version_number = str(version_number.version)
            return version_number

    #Give only user ID for finding mapping
    def getmap(self):
        parent = self.userID
        parent = "/"+parent
        children = self.zk.get_children(parent)
        to_return = []
        for keys in children:
            #print("KEY: ",keys)
            subChildren = parent+"/"+keys
            subChild = self.zk.get_children(subChildren)
            for val in subChild:
                path = subChildren+"/"+val
                print("KEY: ",keys," DEVICES: ",val, "version", self.retrieve(path))
                to_return.append({
                    "key": keys,
                    "device": val, 
                    "version": self.retrieve(path)
                })
                

        return to_return

    #give only Device Id for remapping
    def reMap(self):
        remap_data=[]
        print(self.remap)
        if self.remap == True:
            dev_down=self.node
            dev_down = "/"+dev_down
            val = self.zk.get_children(dev_down)
            for users in val:
                user_name = dev_down+"/"+users
                allItems = self.zk.get_children(user_name)
                for items in allItems:
                    remap_data.append((users,items))
                    #TODO:delete user key pairs here
                    print(users,items)

            #print(remap_data)
        else:
            print("REMAP PARAMETER FALSE")
        
    def setVersion(self,path,value):
        if self.zk.exists(path) == None:
            print("NODE ERROR in setversion method")
        else:
            try:
                self.zk.set(path=path,value=str(value).encode())
            except Exception as e:
                print(e, "Exception in set versioning")

# a = kazooMaster("172.17.0.3","p","dev1","","","",True)
# a.reMap()


# # a=kazooMaster("172.17.0.3","p","","usr1","key1","ADD")
# # val=a.getmap()

# print("Version updated")


