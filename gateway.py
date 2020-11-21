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

class Gateway():
    def __init__(self):
        pass
    

    def run_crush(self, val, rcount):
        proc = subprocess.Popen(['python2', 'utils/crush_runner.py', str(val), str(rcount)], 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                            )

        stdout_value = proc.communicate()
        return stdout_value[0].decode()

    

encoded = int(binascii.hexlify("user1".encode()).decode())
decoded = binascii.unhexlify(str(encoded).encode()).decode()
# kmaster = kazooMaster()
