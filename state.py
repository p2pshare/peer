import os
import json
import threading

shares = {}
chunks = set()

sync_mutex = threading.Lock()

def get_downloaded_shares():
    try:
        with open('shares.json', 'r') as f:
            return json.load(f)
    except IOError:
        return []

def update_chunk_download(share_id, chunk_id):
    global shares
    chunks.add((share_id, chunk_id))
    shares[share_id]['chunks'][chunk_id]['downloaded'] = True

def setup(datadir):
    ret = []
    os.chdir(datadir)
    downloaded_shares = get_downloaded_shares()
    for share in downloaded_shares:
        ret.extend(set_share_downloaded(share))
    return ret

def set_share_downloaded(share):
    global chunks
    global shares
    ret = []
    shares[share['id']] = share
    for chunk in chunks:
        if chunk.get('downloaded') == True:
            ret.append((share['id']), chunk['part'])
        chunks = set(ret)
    return ret

def add_share(share, fpath):
    global shares
    share['fpath'] = fpath
    shares[share['id']] = share

def sync_to_disk():
    sync_mutex.acquire()
    with open('shares.json', 'wb') as f:
        json.dump(shares.values(), f, indent=4)
    sync_mutex.release()
