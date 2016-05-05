import hashlib
from pprint import pprint
import getpass
import os
import random
import base64
import state
import socket
import json

from random import shuffle
from tracker import get_peers_for_chunk, announce_chunk_download
from utils import create_sparse_file

CHUNK_SIZE = 512# * 1024 # 512K

class ChunkNotFound(Exception):
    pass

def get_p2pshare_metadata(path):
    filehash, chunks = get_hashes(path)
    filename = os.path.basename(path)
    return {
        "id": 1,
        "author": getpass.getuser(),
        "chunks": chunks,
        "size": os.stat(path).st_size,
        "hash": filehash,
        "filename": filename,
        "trackers": [
            "localhost:9098",
            "localhost:9099"
        ]
    }


def get_hashes(path):
    filehash = hashlib.md5()
    chunks = []
    count = 0
    with open(path, 'rb') as f:
        while True:
            start = f.tell()
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            md5 = hashlib.md5(chunk).hexdigest()
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

def get_file(share_id, fpath):
    share = get_share(share_id)
    state.add_share(share, fpath)
    create_sparse_file(share["size"], fpath)
    chunks = share["chunks"]
    shuffle(chunks)
    with open(fpath, "wb") as f:
        # XXX Do this in a multithreaded way
        for chunk in chunks:
            chunk_data = get_chunk_from_peers(share["id"], chunk["part"])
            put_chunk(f, share["id"], chunk, chunk_data)
            announce_chunk_download(share["id"], chunk["part"])

def get_share(share_id):
    # XXX Make a request to registry
    with open('/Users/pdvyas/shares.json', 'r') as f:
        return json.load(f)[0]

def get_chunk_from_peers(share_id, chunk_id):
    peer = random.choice(get_peers_for_chunk(share_id, chunk_id))
    return get_chunk_from_peer(peer, share_id, chunk_id)

def get_chunk_from_peer(peer, share_id, chunk_id):
    """
    Make a TCP connection to the peer and fetch the chunk
    """
    host, port = peer.split(":")
    port = int(port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(json.dumps({"share_id": share_id, "chunk_id": chunk_id}))
    # XXX read more than 4096
    buff = s.recv(4096)
    s.close()
    return buff

def get_chunk(share_id, chunk_id):
    if (share_id, chunk_id) in state.chunks:
        print "chunk not found"
        raise ChunkNotFound
    share = state.shares[share_id]
    chunk = share['chunks'][chunk_id]
    return _get_chunk(share, chunk)

def _get_chunk(share, chunk):
    print "in _get_chunk", share, chunk
    with open(share["filename"], 'rb') as f:
        f.seek(chunk["start"])
        chunk_data = f.read(chunk["size"])
    assert hashlib.md5(chunk_data).hexdigest() == chunk["md5"]
    return base64.b64encode(chunk_data)

def put_chunk(f, share_id, chunk, chunk_data):
    f.seek(chunk["start"])
    f.write(base64.b64decode(chunk_data))
