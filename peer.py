import socket
import click
import threading
import thread
import state
import registry
import json


def handle(sock, addr):
    try:
        req = json.loads(read_from_sock(sock))
        resp = registry.get_chunk(req['share_id'], req['chunk_id'])
        # print "resp len", len(resp)
        print "sent", req
        sock.send(resp)
    except Exception, e:
        msg = "ERROR"
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

@click.command()
@click.argument('datadir')
@click.argument('port', type=int)
def peer(datadir, port):
    state.setup(datadir)
    s1 = P2PShareServer("localhost", port)
    t1 = threading.Thread(target=s1.run)
    t1.run()
    t1.daemon = True
    while True:
        t1.join(600)

if __name__ == "__main__":
    peer()

