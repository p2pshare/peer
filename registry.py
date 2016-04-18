import hashlib
from pprint import pprint
import getpass
import os
import base64
from random import shuffle

CHUNK_SIZE = 512# * 1024 # 512K

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

def get_part(share_id, chunk):
    share = shares.get(share_id)
    with open(share["filename"], 'rb') as f:
        f.seek(chunk["start"])
        chunk_data = f.read(chunk["size"])
    assert hashlib.md5(chunk_data).hexdigest() == chunk["md5"]
    return base64.b64encode(chunk_data)

def get_file(share, fpath):
    create_sparse_file(share["size"], fpath)
    chunks = share["chunks"]
    shuffle(chunks)
    with open(fpath, "wb") as f:
        for chunk in chunks:
            put_chunk(f, share["id"], chunk)

def put_chunk(f, share_id, chunk):
    chunk_data = get_part(share_id, chunk)
    f.seek(chunk["start"])
    f.write(base64.b64decode(chunk_data))


def create_sparse_file(size, fpath):
    if os.path.exists(fpath) and os.stat(fpath).st_size == size:
        return
    with open(fpath, "w") as f:
        f.seek(size-1)
        f.write("\0")

if __name__ == "__main__":
    share = get_p2pshare_metadata("pdvyas.pdf")
    pprint(share)
    # shares = {
    #     share["id"]: share
    # }
    # get_file(shares[1], "tfile.pdf")

