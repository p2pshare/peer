import socket
import time
import os
import click
import threading
import thread
import tracker
import state
import shares
import signal
import json
import utils
import cmd
import sys
import traceback
import base64
from threading import Thread


def handle(sock, addr):
    try:
        req = json.loads(read_from_sock(sock))
        resp = shares.get_chunk(req['share_id'], req['chunk_id'])
        # print "resp len", len(resp)
        print "sent", req
        sock.send(resp)
    except Exception, e:
        msg = "ERROR"
        print e
        sock.send(msg)
    finally:
        sock.close()

def read_from_sock(sock):
    buffer_max_len = 4096
    buffer = sock.recv(4096)
    if len(buffer) <= buffer_max_len:
        return buffer
    buffering = True
    while buffering:
        more = sock.recv(4096)
        if not more:
            buffering = False
        else:
            buffer += more
    return buffer

class P2PShareServer(object):

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def bind(self):
        self.sock.bind((self.address, self.port))

    def run(self):
        self.bind()
        try:
            self.sock.listen(5)
            print "Listening on", self.port
            while True:
                sock, addr = self.sock.accept()
                thread.start_new_thread(handle, (sock, addr))
        finally:
            self.sock.close()

def keepalive_thread():
    while True:
        time.sleep(20)
        print 'keepalive'
        tracker.send_keepalive()
        #tracker.announce_all_chunks()

def state_sync_thread():
    while True:
        time.sleep(10)
        state.sync_to_disk()

def setup_fetch_workers():
    ret = []
    def worker():
        while True:
            try:
                f, share, chunk = shares.fetch_queue.get()
                chunk_data = shares.get_chunk_from_peers(share["id"], chunk["part"])
                decoded = base64.b64decode(chunk_data)
                if chunk["md5"] != shares.get_chunk_md5(decoded):
                    print 'Checksum mismatch', chunk['part']
                    raise shares.ChecksumMismatch
                shares.put_chunk(f, share["id"], chunk, decoded)
                tracker.announce_chunk_download(share["id"], chunk["part"])
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                print e
            finally:
                shares.fetch_queue.task_done()
    for i in range(100):
        t = Thread(target=worker)
        t.daemon = True
        t.start()
        ret.append(t)
    return ret

def cli():
    class Cmd(cmd.Cmd):
        def do_get_share(self, args):
            share_id, tpath = args.split()
            if share_id and tpath:
                shares.get_file(int(share_id), tpath)

        def do_EOF(self, line):
            "Exit"
            return True

    print
    Cmd().cmdloop()

def signal_handler(signal, frame):
    print
    print 'You pressed Ctrl+C!'
    print 'Syncing to disk'
    state.sync_to_disk()
    sys.exit(0)

@click.command()
@click.argument('datadir')
@click.argument('hostname')
@click.argument('port', type=int)
def peer(datadir, hostname, port):
    signal.signal(signal.SIGINT, signal_handler)
    utils.config['port'] = port
    utils.config['hostname'] = hostname
    utils.config['datadir'] = datadir
    state.setup(datadir)
    tracker.send_keepalive()
    tracker.announce_all_chunks()
    s = P2PShareServer("localhost", port)
    threads = [
        threading.Thread(target=s.run),
        threading.Thread(target=keepalive_thread),
        threading.Thread(target=state_sync_thread),
        threading.Thread(target=cli),
    ]
    for t in threads:
        t.daemon = True
        t.start()
    threads.extend(setup_fetch_workers())
    while True:
        for t in threads:
            t.join(600)

if __name__ == "__main__":
    peer()

