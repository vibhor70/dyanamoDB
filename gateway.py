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
from master_node import MasterNode

REPLICATION_COUNT = 2


class Gateway():
    def __init__(self):
       pass
    
    @staticmethod
    def get_config():
        with open("./config.json") as fin:
            return json.loads(fin.read())

    @staticmethod
    def create_hash(user_id:str, pid:str):
        m = hashlib.sha256()
        m.update(user_id.encode())
        m.update(pid.encode())
        digest = m.digest()
        encoded = int(binascii.hexlify(digest).decode())
        # decoded = binascii.unhexlify(str(encoded).encode()).decode()
        return encoded

    def run_crush(self, user_id:str, pid:str, rcount:int):
        val = self.create_hash()
        proc = subprocess.Popen(['python2', 'utils/crush_runner.py', str(val), str(rcount)], 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                            )
        stdout_value = proc.communicate()
        device_ids = stdout_value[0].decode()

        return device_ids


    def insert(self, data:dict):
        # data = {
        #     "userid": userid,
        #     "productid": productid,
        #     "operation": operation,
        #     "item": item,
        #     "price": price,
        #     "category": category
        # }
        device_ids = self.run_crush(data["userid"], data["productid"], REPLICATION_COUNT)
        device_ip_map = {}
        for node in self.get_config()["nodes"]:
            if node["device_id"] in device_ids:
                device_ip_map[node["device_id"]] = node["ip"]
        #before inserting check if node exits or not than remove that IP

        for did, ip in device_ip_map.items():
            kmaster = kazooMaster(
                ip, "p", did, data["userid"], 
                data["productid"], data["operation"]
            )
            kmaster.start_client()
            kmaster.create()
        data["DevID"]=device_ids
        #run in constructor also add device ids to arguement
        mnode = MasterNode()
        mnode.connection_accept()
        mnode.send_command(device_ip_map.values(), data)
#call list_all only when down node comes back
    def list_all(self,info:dict):
        """
        dict={
            "userid":username
        }
        """
        kmaster = kazooMaster(
            "172.17.0.3","p","",info["userid"],"","",False
        )
        kmaster.start_client()
        to_return  = kmaster.getmap()

        latest=dict()

        key=""
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

        for keys in latest:
            max_version=-1
            List = latest[keys]
            #print(keys,List)
            for i in range(len(List)):
                x,y = List[i]
                # print("FOR PID: ",keys," DEVICE: ",x," VERSION: ",y)
                if max_version < int(y):
                    max_version = int(y)

            
            for i in range(len(List)):
                x,y = List[i]
                if max_version != int(y):
                    path = "/" + info["userid"] + "/"+ str(keys) + "/" + str(x)
                    path_rev = "/" + str(x) + "/" + info["userid"] + "/"+ str(keys)
                    kmaster.setVersion(path,max_version)
                    kmaster.setVersion(path_rev,max_version)
        #TO DO CHANGE DATA NODES ALSO
        latest_data = kmaster.getmap()
        return latest_data

    def delete_(self,info:dict):
        """
        dict ={
            "userid":username,
            "productid":productID
        }
        """
        kmaster = kazooMaster(
            "","p","",info["userid"],info["productid"],"",False
        )
        allInfo = kmaster.getmap()
        for val in range(len(allInfo)):
            if allInfo[val]["key"]==info["productid"]:
                path = "/" + info["userid"] + "/" + allInfo[val]["key"] + "/" + allInfo[val]["device"]
                path_rev = "/" + allInfo[val]["device"] + "/" + info["userid"] + "/" + allInfo[val]["key"]
                kmaster.delete(path)
                kmaster.delete(path_rev)

         #TO DO CHANGE DATA NODES ALSO
        
         
 
w = Gateway()
w.list_all({"userid":"usr1"})