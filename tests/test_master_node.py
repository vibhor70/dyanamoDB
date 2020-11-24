from ..master_node import MasterNode

a = MasterNode()
#Blocking Call
a.connection_accept()

a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"6","OPERATION":"2","PRICE":"4","CATEGORY":"1"})

a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"5","OPERATION":"2","PRICE":"4","CATEGORY":"12"})
a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"2","OPERATION":"3","PRICE":"4","CATEGORY":"10"})
a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"3","OPERATION":"3","PRICE":"4","CATEGORY":"1"})
a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"2","OPERATION":"2","PRICE":"4","CATEGORY":"10"})
a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"4","OPERATION":"2","PRICE":"4","CATEGORY":"0"})
a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"5","OPERATION":"2","PRICE":"4","CATEGORY":"20"})
a.send_command(["172.17.0.2"], {"COMMAND":"INSERT","USERID":"1", "PRODUCTID":"5","OPERATION":"2","PRICE":"4","CATEGORY":"1"})

    
a.send_command(["172.17.0.2"], {"COMMAND":"RETRIEVE","USERID":"1"})
a.send_command(["172.17.0.2"], {"COMMAND":"REPLACE","USERID":"1", "MAX_PRODUCTID": 2, "UPDATEDLIST": [{
    "ID": "2", "PRICE":"4","CATEGORY":"120", "LATEST_VERSION_VECTOR": "10",
    "OPERATIONS": [{"OPERATION": "1","VERSION_VECTOR": "10"}]
    }]})
a.send_command(["172.17.0.2"], {"COMMAND":"DELETE", "USERID":"1","PRODUCTID":"6"})