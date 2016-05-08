import socket
import shares
import hashlib
import os
import getpass
import json
from utils import recvall

registry_hostname = "localhost"
registry_port = 3000

def get_share(share_id):
    """
    Make a TCP connection to the registry and fetch the share
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((registry_hostname, registry_port))
    s.send(json.dumps({
        "method": "get_share",
        "args": {
            "id": share_id
        }
    }))
    buff = recvall(s)
    s.close()
    return json.loads(buff)

def add_share(path):
    data = get_p2pshare_metadata(path)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((registry_hostname, registry_port))
    s.send(json.dumps({
        "method": "add_share",
        "args": {
            "filename": data["filename"],
            "data": json.dumps(data)
        }
    }))
    buff = s.recv(4096)
    s.close()
    id = json.loads(buff)
    data["id"] = id
    return data

def get_p2pshare_metadata(path):
    filehash, chunks = get_hashes(path)
    filename = os.path.basename(path)
    return {
        "author": getpass.getuser(),
        "chunks": chunks,
        "size": os.stat(path).st_size,
        "hash": filehash,
        "filename": filename,
        "trackers": [
            "localhost:8888",
        ]
    }

def get_hashes(path):
    filehash = hashlib.md5()
    chunks = []
    count = 0
    with open(path, 'rb') as f:
        while True:
            start = f.tell()
            chunk = f.read(shares.CHUNK_SIZE)
            if not chunk:
                break
            md5 = get_chunk_md5(chunk)
            filehash.update(chunk)
            size = f.tell() - start
            chunks.append({
                'part': count,
                'start': start,
                'part': count,
                'md5': md5,
                'size': size
            })
            count += 1
    return filehash.hexdigest(), chunks

def get_chunk_md5(data):
    return hashlib.md5(data).hexdigest()

if __name__ == "__main__":
    # print add_share("p1/pdvyas.pdf")
    import pprint
    pprint.pprint(get_share(22))
