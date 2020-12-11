cd /

echo 1 > /var/zookeeper/myid

vim /opt/zookeeper/conf/zoo.cfg

/opt/zookeeper/bin/zkServer.sh start

docker run -it -p 8088:8088 --name apiServer -h apiserver d073c12f7f42

# docker exec -it container_id date
docker exec -it <Containerid> pip3 freeze
uvicorn api:app --reload --host 0.0.0.0 --port 8085


docker run -it  -h data_node1 d073c12f7f42
cd /opt/dyanamoDB/ && git pull
cp /opt/dyanamoDB/config/zoo.cfg /opt/zookeeper/conf/zoo.cfg
/opt/zookeeper/bin/zkServer.sh start
pip3 install tinydb
pip3 install fastapi
pip3 install uvicorn
cd /opt/dyanamoDB && rm db/*