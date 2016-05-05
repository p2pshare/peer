import os
import json

shares = {}
chunks = set()

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
    global chunks
    global shares
    ret = []
    os.chdir(datadir)
    downloaded_shares = get_downloaded_shares()
    for share in downloaded_shares:
        shares[share['id']] = share
        for chunk in chunks:
            if chunk.get('downloaded') == True:
                ret.append((share['id']), chunk['part'])
            chunks = set(ret)

def add_share(share, fpath):
    global shares
    share['fpath'] = fpath
    shares[share['id']] = share

def sync_to_disk():
    # XXX Mutex
    with open('shares.json', 'wb') as f:
        return json.dump(shares.values(), f, indent=4)
