import binascii
import hashlib
import json
import os
import subprocess
import threading
import time

from kazoo.exceptions import NoNodeError

from kazoo_master import kazooMaster
from socket_server import SocketServer

class Gateway():
    def __init__(self, gateway_ip):
        self.Flaged_ip=dict()
        self.CONFIG = self.get_config()
        self.REPLICATION_COUNT = self.CONFIG["REPLICATION_COUNT"]
        self.GATEWAY_IP = gateway_ip
        self.mnode = SocketServer(gateway_ip)
        t = threading.Thread(target = self.run_mmnode_thread)
        t.start()

    def run_mmnode_thread(self):
        self.mnode.connection_accept()

    @staticmethod
    def get_config():
        with open("./config/config.json") as fin:
            return json.loads(fin.read())

    def get_crush(self):
        with open("./config/crushmap.json") as fin:
            return json.loads(fin.read())

    @staticmethod
    def create_hash(user_id:str, pid:str):
        m = hashlib.sha1()
        m.update(user_id.encode())
        m.update(pid.encode())
        digest = m.hexdigest()
        digest_int = int(digest, 16) % 10**8
        # decoded = binascii.unhexlify(str(encoded).encode()).decode()
        return digest_int

    def run_crush(self, user_id:str, pid:str, rcount:int):
        val = self.create_hash(user_id, pid)
        proc = subprocess.Popen(['python2', 'crush_runner.py', str(val), str(rcount)], 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                            )
        stdout_value = proc.communicate()
        device_ids = stdout_value[0].decode()

        device_ids = [str(devid).strip() for devid in device_ids.split("\n") if len(devid) > 0]
        print(device_ids, "in running crush")
        return device_ids

    def update_crush(self, critera):
        print("Update crush", critera)

        crush_map = self.get_crush()
        did = int(critera["DEVICE"].strip("_")[-1])
        if critera["OP"] == "ADD":
            crush_map["trees"][0]["children"].insert(did-1, {
                "type": "host", "name": "host{}".format(did-1), "id": -1*did,
                "children": [
                    { "id": did, "name": critera["DEVICE"], "weight": 65536 }
                ]
            })
            
        elif critera["OP"] == "REMOVE":
            del crush_map["trees"][0]["children"][did-1]

        fout = open("config/crushmap.json", "w")
        json.dump(crush_map, fout)
        fout.close()
        
    def insert(self, data:dict):
        kmaster = kazooMaster(
                self.GATEWAY_IP, "p", "", data["USERID"], 
                data["PRODUCTID"], data["OPERATION"]
            )

        for dname,val in self.Flaged_ip.items():
            path = "/ephemeral_" + dname
            if kmaster.exist(path) and val == -1:
                self.update_crush({"OP": "ADD","DEVICE": dname})
                #UP Update update crush
        #old
        MAX_loop_checker = 5
        while MAX_loop_checker > 0:
            MAX_loop_checker -= 1
            down_devices = False
            device_ids = list(self.run_crush(data["USERID"], data["PRODUCTID"], self.REPLICATION_COUNT))
            device_ip_map = {}
            for node in self.CONFIG["nodes"]:
                if node["device_id"] in device_ids:
                    device_ip_map[node["device_id"]] = node["ip"]
                    
            print(self.Flaged_ip, ":flagged ips")
            kmaster.start_client()

            for did, ip in device_ip_map.items():
                path = "/ephemeral_" + did
                if kmaster.exist(path):
                    if did in self.Flaged_ip.keys() and self.Flaged_ip[did] == -1:
                        self.read_repair({"NODES":device_ids})
                        self.Flaged_ip[did]=0
                        del self.Flaged_ip[did]
                else:
                    self.update_crush({"OP": "REMOVE","DEVICE": did})
                    self.Flaged_ip[did]=-1
                    down_devices = True

            if not down_devices:
                break

        for did, ip in device_ip_map.items():
            path = "/ephemeral_" + did
            if kmaster.exist(path):
                self.mnode.send_command(device_ip_map[did], data)

        kmaster.stop_client()    
        return True
        
    def read_repair(self,info:dict):
        print("In read repair", info)
        """
        dict={"NODES":[node1,node2,node3]}
        """
        kmaster = kazooMaster(
            self.GATEWAY_IP,"p","","","","",False
        )
        kmaster.start_client()
        all_user = set()
        flag = False
        down_node = []
        for nodes in info["NODES"]:
            path = "/" + nodes
            print(path, "in read_repar")
            all_child = []
            
            all_child = kmaster.get_children(path)
            print(all_child)
            if all_child == "":
                print("Node does not exists")
                kmaster.create(path)
                flag = True
                down_node.append(nodes)
            else:
                for child in all_child:
                    all_user.add(child)
        
        for child in all_user:
            self.list_all({"USERID":child}, flag, down_node)

        kmaster.stop_client()

    def get_device_ip_map(self):
        device_ip_map = {}
        for node in self.CONFIG["nodes"]:
            device_ip_map[node["device_id"]] = node["ip"]

        return device_ip_map

    def list_all(self,info:dict, flag = False, down_nodes = None):
        """
        dict={
            "userid":username
        }
        """
        print("list_all", info, flag, down_nodes)

        kmaster = kazooMaster(
            self.GATEWAY_IP,"p","",info["USERID"],"","",False
        )
        kmaster.start_client()
        to_return  = kmaster.getmap()

        if len(to_return) == 0:
            return []

        self.mnode 
        latest=dict()

        key=""
        maxVersion_replace = []

        device_ip_map = self.get_device_ip_map()

        for i in range(len(to_return)):
            tkey = to_return[i]["key"]
            tdevice = to_return[i]["device"]
            tversion = to_return[i]["version"]
            
            if key != tkey:
                key = tkey
                all_dev=[]
                all_dev.append((tdevice,tversion))
                latest[key]=all_dev
            else:
                all_dev.append((tdevice,tversion))
                latest[key]=all_dev
                # print(latest[key])
        
        maxData = None
        maxProductid = None
        for keys in latest:
            max_version=-1
            List = latest[keys]
            #print(keys,List)
            for i in range(len(List)):
                x,y = List[i]
                # print("FOR PID: ",keys," DEVICE: ",x," VERSION: ",y)
                if max_version < int(y):
                    max_version = int(y)
                    maxDevice = x
                    maxProductid = keys

            for node in self.CONFIG["nodes"]:
                if node["device_id"] == maxDevice:
                    self.mnode.send_command([node["ip"], ], 
                        {"COMMAND":"RETRIEVE","USERID":info["USERID"], "PRODUCTID": maxProductid})
                    target= self.mnode.targets[node["ip"]]
                    print(target)
                    maxData = self.mnode.reliable_recv(target)
                    # GOT THE PRODUCTS
                    maxData = json.loads(maxData)["PRODUCT"]
                    """
                    HUGE DOUBT IF SEND WILL I RECIVE USING RELIABLE RECV
                    """
            for i in range(len(List)):
                x,y = List[i]
                if max_version != int(y):
                    path = "/" + info["USERID"] + "/"+ str(keys) + "/" + str(x)
                    path_rev = "/" + str(x) + "/" + info["USERID"] + "/"+ str(keys)
                    device_ids = list(x)
                    for node in self.CONFIG["nodes"]:
                        if node["device_id"] in device_ids:
                            self.mnode.send_command(
                                [node["ip"]], 
                                {"COMMAND":"REPLACE","USERID":info["USERID"],
                                "UPDATEDLIST":maxData, "MAX_PRODUCTID": maxProductid}
                            )
                            """
                            SENDING A LIST DEPENDS ON IF maxData RECIEVED
                            """
                    kmaster.setVersion(path,max_version)
                    kmaster.setVersion(path_rev,max_version)


            if flag == True:
                for down_node in down_nodes:
                    kmaster.create("/{}/{}/{}".format(down_node, info["USERID"], keys))
                    kmaster.create("/{}/{}/{}".format(info["USERID"], keys, down_node))
                    print(maxData, type(maxData), "maxdata")
                    """
                    {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"5","OPERATION":"2","PRICE":"4","CATEGORY":"12"}
                    """
                    self.mnode.send_command(
                        [device_ip_map[down_node],], 
                        {"COMMAND":"REPLACE","USERID":info["USERID"], 
                        "MAX_PRODUCTID": maxProductid, "UPDATEDLIST":[maxData]})

        #TO DO CHANGE DATA NODES ALSO
        latest_data = kmaster.getmap()
        if len(latest_data) == 0:
            return []
        kmaster.stop_client()
        return latest_data

    def list_all_user_products(self, critera):
        latest_data = self.list_all({"USERID": critera["USERID"]})
        print(latest_data, "in gateway")
        device_ip_map = {}
        for node in self.CONFIG["nodes"]:
            device_ip_map[node["device_id"]] = node["ip"]

        counter = None
        to_return = []
        for data in latest_data:
            if counter != data["key"]:
                counter = data["key"]
                self.mnode.send_command([device_ip_map[data["device"]]], {
                    "COMMAND":"RETRIEVE","USERID":critera["USERID"], 
                    "PRODUCTID": data["key"]}
                )
                target = self.mnode.targets[device_ip_map[data["device"]]]
                prod = self.mnode.reliable_recv(target)
                prod = json.loads(prod)["PRODUCT"]
                to_return.append(prod)

        print(to_return, "in gateway")
        return to_return

    def delete(self,info:dict):
        """
        dict ={
            "USERID":username,
            "PRODUCTID":productID
        }
        """
        kmaster = kazooMaster(
            self.GATEWAY_IP,"p","",info["USERID"],info["PRODUCTID"],"",False
        )
        kmaster.start_client()
        allInfo = self.list_all({"USERID": info["USERID"]})
        print(allInfo)
        for val in range(len(allInfo)):
            if allInfo[val]["key"]==info["PRODUCTID"]:
                for node in self.CONFIG["nodes"]:
                    if node["device_id"] == allInfo[val]["device"]:
                        self.mnode.send_command([node["ip"]],   
                        {"COMMAND":"DELETE", 
                        "USERID":info["USERID"],"PRODUCTID":allInfo[val]["key"]})


    def list_category(self,info:dict):
        """
        {
        Find all the alive nodes and take secondary indexes from them
        }
        dict = {
            info={
                "CATEGORY":CATEGORY_NUMBER
            }
        }
        }
        """
        val = self.get_crush()
        all_category_info = []
        device_ip_map = self.get_device_ip_map()

        for value in range(len(val["trees"][0]["children"])):
            name = val["trees"][0]["children"][value]["children"][0]["name"]
            # for node in self.CONFIG["nodes"]:
            self.mnode.send_command( [device_ip_map[name], ],   
                {"COMMAND":"LISTCATEGORY",
                "CATEGORY":info["CATEGORY"]
                })
            target= self.mnode.targets[device_ip_map[name]]
            temp = self.mnode.reliable_recv(target)
            temp = json.loads(temp)
            all_category_info.append(temp)

        print(all_category_info, "in list_category")
        return all_category_info