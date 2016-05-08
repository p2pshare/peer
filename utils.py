import os

config = {
    "tracker_host": "localhost",
    "tracker_port": 8888
}
global config

def create_sparse_file(size, fpath):
    if os.path.exists(fpath) and os.stat(fpath).st_size == size:
        return
    with open(fpath, "w") as f:
        f.seek(size-1)
        f.write("\0")

def get_config():
    return config

def recvall(sock):
    data = ""
    part = None
    while part != "":
        part = sock.recv(4096)
        data += part
        if len(part) < 4096:
            break
    return data

def sendall(sock, msg):
    MSGLEN=4096
    totalsent = 0
    while totalsent < MSGLEN:
        sent = sock.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent
