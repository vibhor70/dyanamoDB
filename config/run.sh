cd /

echo 1 > /var/zookeeper/myid

vim /opt/zookeeper/conf/zoo.cfg

/opt/zookeeper/bin/zkServer.sh start

docker run -it -p 8000:8000 --name apiServer -h apiserver d073c12f7f42

# docker exec -it container_id date
docker exec -it <Containerid> pip3 freeze
uvicorn api:app --reload --host 0.0.0.0