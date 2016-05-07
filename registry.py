import hashlib
from pprint import pprint
import getpass
import os
import random
import threading
import base64
import state
import socket
import json
import Queue

from random import shuffle
from tracker import get_peers_for_chunk, announce_chunk_download
from utils import create_sparse_file

CHUNK_SIZE = 512# * 1024 # 512K

fetch_queue = Queue.Queue()

class ChunkNotFound(Exception):
    pass

class ChecksumMismatch(Exception):
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

files_mutexes = {}

def get_file(share_id, fpath):
    share = get_share(share_id)
    state.add_share(share, fpath)
    create_sparse_file(share["size"], fpath)
    chunks = share["chunks"]
    with open(fpath, "wb") as f:
        if f not in files_mutexes:
            files_mutexes[f] = threading.Lock()
        for chunk in chunks:
            fetch_queue.put((f, share, chunk))
        fetch_queue.join()
        del files_mutexes[f]
    if share["hash"] != get_file_checksum(fpath):
        print "File  checksum mismatch"
        raise ChecksumMismatch
    state.sync_to_disk()

def get_share(share_id):
    # XXX Make a request to registry
    with open('/Users/pdvyas/shares.json', 'r') as f:
        return json.load(f)[0]

def get_chunk_from_peers(share_id, chunk_id):
    peer = random.choice(get_peers_for_chunk(share_id, chunk_id))
    if not peer:
        print 'retrying'
        peer = random.choice(get_peers_for_chunk(share_id, chunk_id))
    if not peer:
        print 'give up'
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
    print "in _get_chunk", chunk
    with open(share["filename"], 'rb') as f:
        f.seek(chunk["start"])
        chunk_data = f.read(chunk["size"])
    assert hashlib.md5(chunk_data).hexdigest() == chunk["md5"]
    return base64.b64encode(chunk_data)

def put_chunk(f, share_id, chunk, chunk_data):
    with files_mutexes[f]:
        f.seek(chunk["start"])
        f.write(chunk_data)

def get_file_checksum(path):
    filehash = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            filehash.update(chunk)
    return filehash.hexdigest()
