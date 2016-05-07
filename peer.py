import socket
import time
import click
import threading
import thread
import tracker
import state
import registry
import json
import utils
import cmd


def handle(sock, addr):
    try:
        req = json.loads(read_from_sock(sock))
        resp = registry.get_chunk(req['share_id'], req['chunk_id'])
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
    print 'inrun'
    while True:
        time.sleep(20)
        print 'keepalive'
        tracker.send_keepalive()
        tracker.announce_all_chunks()

def state_sync_thread():
    while True:
        time.sleep(10)
        state.sync_to_disk()

def cli():
    class Cmd(cmd.Cmd):
        def do_get_share(self, args):
            share_id, tpath = args.split()
            if share_id and tpath:
                registry.get_file(int(share_id), tpath)

        def do_EOF(self, line):
            "Exit"
            return True

    print
    Cmd().cmdloop()

@click.command()
@click.argument('datadir')
@click.argument('hostname')
@click.argument('port', type=int)
def peer(datadir, hostname, port):
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
    while True:
        for t in threads:
            t.join(600)

if __name__ == "__main__":
    peer()

