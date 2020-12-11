import docker

client = docker.from_env()
containers = client.containers.list()

zoo_conf = open("./zoo.cfg", "r").read()

commands = [
    "cd /opt/dyanamoDB/ && git pull",
    "cp /opt/dyanamoDB/config/zoo.cfg /opt/zookeeper/conf/zoo.cfg",
    "/opt/zookeeper/bin/zkServer.sh start",
    "pip3 install tinydb",
    "pip3 install fastapi",
    "pip3 install uvicorn",
    "cd /opt/dyanamoDB && rm db/*",
]

for i, container in enumerate(containers):
    cid = container.id
    print(cid)
    cout = container.exec_run(
        f"echo {i+1} > /var/zookeeper/myid",
        stdout=True, stderr=True, 
        stdin=False, tty=False, privileged=False
    )
    print(cout)
    for cmd in commands:
        cout = container.exec_run(
            cmd,
            stdout=True, stderr=True, 
            stdin=False, tty=False, privileged=False
        )   
        print(cout)
    print("\n\n")