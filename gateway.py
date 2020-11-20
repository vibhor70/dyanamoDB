"""
Steps:
1. 
2. 
3.

"""

from client.kazooMaster import kazooMaster
import subprocess


value = 12
replication_count = 2
proc = subprocess.Popen(['python2', 'utils/crush_runner.py', str(value), str(replication_count)], 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                    )

stdout_value = proc.communicate()
print(stdout_value[0].decode())

# kmaster = kazooMaster()