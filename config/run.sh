cd /

echo 1 > /var/zookeeper/myid

vim /opt/zookeeper/conf/zoo.cfg

/opt/zookeeper/bin/zkServer.sh start