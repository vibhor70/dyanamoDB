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

class WatcherPipe():
    def __init__(self):
        self.thread_instances = []
        self.downs = -1
    
    @staticmethod
    def get_config():
        with open("./config.json") as fin:
            return json.loads(fin.read())

    def create_hash(self,user_id:str, pid:str):
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
        device_id = stdout_value[0].decode()

        return device_id

    def kazoo_master_thread(self, kazoo_instance, i, r, w):
        result = kazoo_instance.stat()
        self.thread_instances[i]["down"] = True
        print(i, kazoo_instance, "is down")
        os.close(r) 
        w = os.fdopen(w, 'w') 
        print("Child writing") 
        w.write(str(i)) 
        w.close() 

    # def monitor_thread(self):
    #     for thread_instance in self.thread_instances:
    #         if thread_instance.completed
    #         thread_instance["object"].join()

    def run_watcher(self, r, w):
        device_config = self.get_config()
        for i, device in enumerate(device_config["nodes"][0:3]):
            kmaster_instance = kazooMaster(
                device["ip"], "e", device["device_id"]
            )
            self.thread_instances.append({
                "down": False,
                "object": threading.Thread(target = self.kazoo_master_thread, args=(kmaster_instance, i, r, w))
            })
        
        for thread_instance in self.thread_instances:
            thread_instance["object"].start()

        # for i, thread_instance in self.thread_instances:
        #     thread_instance["object"].join()

        # time.sleep(3)
        for thread_instance in self.thread_instances:
            if thread_instance["down"] == True:
                print(thread_instance, "is down")
                # kmaster_instance = kazooMaster(
                #     device["ip"], "e", device["device_id"]
                # )

    def run_gateway(self):
        r, w = os.pipe() 
        processid = os.fork() 
        if processid: 
            # This is the parent process 
            # Closes file descriptor w 
            os.close(w) 
            r = os.fdopen(r) 
            print ("Parent reading") 
            read = int(r.read()) 
            print( "Parent reads =", read) 
        else: 
            # This is the child process 
            self.run_watcher(r, w)

w = WatcherPipe()
w.run_gateway()