"""
Steps:
IMP:APPLY STAT METHOD OF KAZOO ON EPEHEMRAL NODES
0. TAKE USER ID AND CREATE PRODUCT ID FOR EACH PRODUCT 
2. MAP THEM USING CRUSH->(USER,PRODUCTID,DEVICE)->CREATE TWO NODES USER/ID/DEVICE AND /DEVICE/USER/ID USING create 
METHOD OF KAZOOMASTER
 THEREBY UPDATING THE UPDATING IN ZOOKEEPER USING KAZOOMASTER CLASS
4.UPDATE IN DATANODE USING MASTERNODE.PY
5.INCASE OF NODE FAILURE APPLY REMAP PROCEDURE :reMap METHOD IS HALF COMPLETED 
6.IF GATEWAY WANTS MAP OF USER IT CALL getMap OF KAZOOMASTER
7.CONCURRRENCY NOT HANDLED AS OF NOW

"""

from kazooMaster import kazooMaster
import subprocess
import binascii
import hashlib
import json
import threading
import time
import os
from kazoo.exceptions import NoNodeError
from master_node import MasterNode

REPLICATION_COUNT = 2

class Gateway():
    def __init__(self, gateway_ip):
        self.Flaged_ip=dict()
        self.CONFIG = self.get_config()
        self.GATEWAY_IP = gateway_ip
        self.mnode = MasterNode(gateway_ip)
        t = threading.Thread(target = self.run_mmnode_thread)
        t.start()

    def run_mmnode_thread(self):
        self.mnode.connection_accept()

    @staticmethod
    def get_config():
        with open("./config.json") as fin:
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
        proc = subprocess.Popen(['python2', 'utils/crush_runner.py', str(val), str(rcount)], 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                            )
        stdout_value = proc.communicate()
        device_ids = stdout_value[0].decode()

        device_ids = [str(devid).strip() for devid in device_ids.split("\n") if len(devid) > 0]
        return device_ids


    def insert(self, data:dict):

        device_ids = list(self.run_crush(data["USERID"], data["PRODUCTID"], REPLICATION_COUNT))
        print(device_ids, type(device_ids))
        device_ip_map = {}
        flag=False
        for node in self.CONFIG["nodes"]:
            if node["device_id"] in device_ids:
                device_ip_map[node["device_id"]] = node["ip"]
        #before inserting check if node exits or not than remove that IP
        kmaster = kazooMaster(
                self.GATEWAY_IP, "p", "", data["USERID"], 
                data["PRODUCTID"], data["OPERATION"]
            )
        print(device_ip_map)

        kmaster.start_client()
        for did, ip in device_ip_map.items():
            path = "/ephemeral_" + did
            if kmaster.exist(path):
                if did in self.Flaged_ip.keys() and self.Flaged_ip[did] == -1:
                    self.mnode.send_command(device_ip_map[did], data)
                    self.read_repair({"NODES":device_ids})
                    #DO READ REPAIR WHEN DOWN NODE COMES BACK
                    self.Flaged_ip[did]=0
                else:
                    # new initial node starts
                    self.mnode.send_command(device_ip_map[did], data)
            else:
                flag=False
                self.Flaged_ip[did]=-1

        kmaster.stop_client()    
        # data["DevID"]=device_ids
        #run in constructor also add device ids to arguement
        
#call list_all only when down node comes back


    def read_repair(self,info:dict):
        """
        dict={
            "NODES":[node1,node2,node3]
        }

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
        
        print(all_user)
        for child in all_user:
            self.list_all({"USERID":child}, flag, down_node)

        kmaster.stop_client()


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
        self.mnode 
        latest=dict()

        key=""
        maxVersion_replace = []
        device_ip_map = {}
        for node in self.CONFIG["nodes"]:
            device_ip_map[node["device_id"]] = node["ip"]

        for i in range(len(to_return)):
            tkey = to_return[i]["key"]
            tdevice = to_return[i]["device"]
            tversion = to_return[i]["version"]
            
            if key != tkey:
                key = tkey
                all_dev=[]
                all_dev.append((tdevice,tversion))
                latest[key]=all_dev
                # print("tkey :",tkey," tdevice",tdevice," tversion",tversion)
                # print(latest[key])

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

            print(maxDevice, max_version, maxProductid, "maxdevice, version , maxpid")
            for node in self.CONFIG["nodes"]:
                if node["device_id"] == maxDevice:
                    self.mnode.send_command([node["ip"]], {"COMMAND":"RETRIEVE","USERID":info["USERID"], "PRODUCTID": maxProductid})
                    target= self.mnode.targets[self.mnode.ips.index(node["ip"])]
                    maxData = self.mnode.reliable_recv(target)
                    # GOT THE PRODUCTS
                    print(maxData, "maxdata in loop")
                    maxData = json.loads(maxData)["PRODUCT"]
                    print("maxdata", maxData)
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

            latest_data = kmaster.getmap()
        #TO DO CHANGE DATA NODES ALSO
        latest_data = kmaster.getmap()
        kmaster.stop_client()
        return latest_data

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
            # version = int(allInfo[val]['version'])
            if allInfo[val]["key"]==info["PRODUCTID"]:
                # path = "/" + info["USERID"] + "/" + allInfo[val]["key"] + "/" + allInfo[val]["device"]
                # path_rev = "/" + allInfo[val]["device"] + "/" + info["userid"] + "/" + allInfo[val]["key"]
                for node in self.CONFIG["nodes"]:
                    if node["device_id"] in list(allInfo[val]["device"]):
                        
                        self.mnode.send_command([node["ip"]],   
                        {"COMMAND":"DELETE", 
                        "USERID":info["userid"],"PRODUCTID":allInfo[val]["key"]})
                # kmaster.setVersion(path, version)
                # kmaster.setVersion(path_rev, version)

        # kmaster.stop_client()
         
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Gateway ip dedo bhai")
        sys.exit(-1)

    w = Gateway(sys.argv[1])
   