import os
import json

shares = {}
chunks = set()

def get_downloaded_shares():
    with open('shares.json', 'r') as f:
        return json.load(f)

def update_chunk_download(share_id, chunk_id):
    pass

def setup(datadir):
    global chunks
    global shares
    ret = []
    os.chdir(datadir)
    downloaded_shares = get_downloaded_shares()
    for share in downloaded_shares:
        shares[share['id']] = share
        for chunk in chunks:
            ret.append((share['id']), chunk['part'])
            chunks = set(ret)
