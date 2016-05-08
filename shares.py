import hashlib
from pprint import pprint
import os
import random
import threading
import base64
import state
import socket
import json
import Queue

from random import shuffle
from tracker import get_peers_for_chunk, announce_chunk_download, announce_chunks_for_share
from utils import create_sparse_file, recvall
from registry import get_share
from registry import add_share as _add_share

CHUNK_SIZE = 512 * 1024 # 512K

fetch_queue = Queue.Queue()

class ChunkNotFound(Exception):
    pass

class ChecksumMismatch(Exception):
    pass

files_mutexes = {}

def add_share(path):
    share = _add_share(path)
    print 'added to registry', share["id"]
    state.set_share_downloaded(share)
    announce_chunks_for_share(share)

def get_file(share_id):
    share = get_share(share_id)
    fpath = share['filename']
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
    buff = recvall(s)
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
