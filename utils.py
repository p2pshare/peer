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
