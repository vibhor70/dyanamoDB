Introduction:

We have developed a distributed database with help of zookeeper coordinator service. The distributed database consists of several datanodes running on containers ,two gateways running also on containers and an api server which sends the REST api request to GATEWAY ,which then forwards to data nodes accordingly.All the essential details are described below,the following inventory consist of available product at the shopping site.
Inventory:
This contains the shopping cart info for a particular user, 
item: Product Name/id 
category: Category a product belongs to
total_qty: Number of items bought finally 
price: Total cost for respective product 

"1": {
   "item": "pork",
   "total_qty": 5,
   "category": 1,
   "price": 61
},
"2": {
   "item": "soap",
   "total_qty": 1,
   "category": 1,
   "price": 36
}


SHOPPING CART
The shopping cart for users is given as follows. Below is the sample USER CART for USER1.
{
   "response": [
       {
           "name": "yogurt",
           "price": 28,
           "category": "2",
           "qty": 1
       },
       {
           "name": "cereals",
           "price": 69,
           "category": "3",
           "qty": 1
       }
   ]
}

TRANSACTION
Each individual record to insert <userid,productid,price,category> is a transaction in our system and is every operation add,delete is atomically done on this transaction i.e for every insert on same  <user id,productid> it increases the amount for every delete on same  <user id,productid> it decreases the amount


FIG: Architecture of the system
BACKBONE
There are six datanodes and running on six containers and two gateway servers running on gateway two containers all which can talk to each other through sockets . All the  datanodes connect to the gateway server and we store the  ips as well as socket objects of the connected data nodes at the gateway server.

A zookeeper server is running on every datanode ,and if a new a datanode connects it opens up a zookeeper and first starts the zookeeper server and connects to zookeeper ensemble and than starts it client and creates a ephemeral node as /ephemeral_deviceID ,it and when a network partition occurs or it gets disconnected the ephemeral node is destroyed so we can know the updated picture of the available datanodes.

Each datanode on receiving the command from gateway performs on its local db and if required updates in zookeeper
ZNODES DATA HIERARCHY

We are storing the meta information about the userid and productid and the corresponding device it maps to in following format 
<USERID/PRODUCTID/DEVICEID>
<DEVICEID/USERID/PRODUCTID>
Here,
USER ID = unique userID of user
PRODUCTID = unique productID of purchased product
DEVICEID = unique device ID of corresponding device mapped by crush algorithm

Since every transaction has at least 2 copies ,so to ease out work of finding where every copy of the transaction of a particular is stored on which datanodes and second mapping helps us in the read repair as it readily provides us with the all the product id of a particular user is on that device

Fig: Znode Client
API  SERVER
On receiving each REST request it send it to any of two gateways randomly and if the request is of insert/delete it reply back with inserted into cart/deleted back to user
We have used a different API server and forwarded it to gateway as we have separated the handling API request and essential work of sending and receiving and performing read repair which is done by gateway.
Also we can increase the number of API servers since each of them randomly selects a gateway the total number of requests will be 50:50 for both gateways after some time.

REST API ENDPOINTS
/api/insert:
If the corresponding Userid,productid exit it just increases the quantity by 1. If product is not available in inventory, it returns ERROR message saying, product is not available in cart, or qty=0
To insert into the cart:
Input: Userid, item_name 
Output: Returns the success message
 
/api/delete:
If the corresponding Userid,productid exit it just decreases the quantity by 1. it returns ERROR message saying, product is not available in cart
Input: userid, item_name
Output: Returns the success message
 
/api/list_all:
	List all products of particular user
input:user id
Output:productid,quantity,price,category
 
/api/list_category
For use by admin, it will get all users, with product category as given.
It makes use of a secondary index stored.
Input: Category
Output: List of all users who have bought item of that category

Crush Configuration
In order to identify the replicas of a shopping cart, the Gateway runs the Crush algorithm, which is responsible for identifying the data nodes where the shopping cart and its replicas are present. The algorithm uses a configuration map JSON defined as: 
{
   "trees": [{
       "type": "root","name": "dc1", "id": -10,
       "children": [
           {
               "type": "host", "name": "host0","id": -1,
               "children": [{"id": 1,"name": "device_1","weight": 65536 }]
           }, {
               "type": "host", "name": "host1","id": -2,
               "children": [{"id": 2,"name": "device_2","weight": 65536 }]
           },
           {
               "type": "host", "name": "host2","id": -3,
               "children": [{"id": 3,"name": "device_3","weight": 65536 }]
           },
           {
               "type": "host", "name": "host3","id": -4,
               "children": [{"id": 4,"name": "device_4","weight": 65536 }]
           },
           {
               "type": "host", "name": "host4","id": -5,
               "children": [{"id": 5,"name": "device_5","weight": 65536 }]
           },
           {
               "type": "host", "name": "host5","id": -6,
               "children": [{"id": 6,"name": "device_6","weight": 65536 }]
       }]
   }],
   "rules": {
       "data": [
           ["take", "dc1"],
           ["chooseleaf", "firstn", 0, "type", "host"],
           ["emit"]
       ]
   }
}

GATEWAY
Following functions are of gateway:
For each REST request  of type </api/insert,/api/delete>of a transaction it first put the combination of userid + productid into the CRUSH hash but as CRUSH take integer value we first convert it into one using method shown below:
We feed this digest_int into the crush HASH and get device id’s
@staticmethod
def create_hash(user_id:str, pid:str):
   m = hashlib.sha1()
   m.update(user_id.encode())
   m.update(pid.encode())
   digest = m.hexdigest()
   digest_int = int(digest, 16) % 10**8
   return digest_int

After we get the device id’s the checks for the ephemeral node of that device of form /ephemeral_deviceid every time so it always sends to right node.
If a ephemeral node does not exit it updates the CRUSH map the CRUSH hash function uses and also deletes that deviceid container’s IP and socket object
If the devices exists it and query is of type </api/insert,/api/delete> it sends this info to all the devices and if the query of type </api/list_all>
I.e to retrieve updated cart info of a particular user it first do read repair and than retrieves the updated info and reply back to API server
If a node that was down previously and was removed from CRUSH map now comes back ,the gateway again updates the CRUSH and reinsert that nodes info into CRUSH map,as it checks every time it does any operation

DATA NODE
PRIMARY DB
Database :key/value store
Key:userid
Value:all info of the products

For insert/delete type request for <userid,productid>
If it does not exist it first creates NODES of type
USERID/PRODUCTID/DEVICEID
DEVICEID/USERID/PRODUCTID

And since multiple request must be send to multiple devices each device will create znodes as described above and for USERID/PRODUCTID/DEVICEID
Each device will create a znode<DEVICE ID> under same USERID/PRODUCTID and each device will create a unique znode for DEVICEID/USERID/PRODUCTID

If both znodes exists as described above than for each same <user id/productid> it first takes the version number from zookeeper and +1 to it and appends it 

The datanode db structure is as follows:
{
  "USERID": "<user name>",
  "PRODUCTS": [{
      "ID": "<product name/id: str>",
      "PRICE": "<price: str>",
      "CATEGORY": "<category: str>",
      "LATEST_VERSION_VECTOR": "<latest ver vector:int>",
      "OPERATIONS": [
          {
              "OPERATION": "ADD/DELETE",
              "VERSION_VECTOR": "<ver vector:int>"
          }
      ]
  }]
}

After inserting into DB it also updates the secondary index db 
SECONDARY INDEX DB
{
   "CATEGORY": <category_id>,
   "USERID": [
       "userid/username",
   ]
}


After that it updates that version in zookeeper with updated version number

We are running 9 containers each having different IP’s
6 data nodes
2 gateway server
1 API server


