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

from client.kazooMaster import kazooMaster
import subprocess
import binascii
import hashlib
import json

class Gateway():
    def __init__(self):
        pass
    
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

    def kazoo_master_thread(self):
        a = kazooMaster("172.17.0.3","p","dev1","","","",True)

    def run(self):
        device_config = self.get_config()

        t1 = threading.Thread(target = self.server)
        t1.start()