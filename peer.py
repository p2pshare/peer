import socket
import threading

def handle(sock, addr):
    while True:
        r = sock.recv(4096)
        print "received", r, len(r)
        if r.strip() == "exit":
            break
        sock.send(r, 4096)
    sock.close()

class P2PShareServer(object):

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def bind(self):
        self.sock.bind((self.address, self.port))

    def run(self):
        self.bind()
        self.sock.listen(5)
        print "Listening on", self.port
        while True:
            sock, addr = self.sock.accept()
            handle(sock, addr)


s1 = P2PShareServer("localhost", 9092)
s2 = P2PShareServer("localhost", 9093)

t1 = threading.Thread(target=s1.run)
t1.daemon = True
t1.start()
t2 = threading.Thread(target=s2.run)
t2.daemon = True
t2.start()

while True:
    t1.join(600)
    t2.join(600)
