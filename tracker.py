import json
import socket
import utils
import state
import threading

announce_lock = threading.Lock()


def get_peers_for_chunk(share_id, chunk_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((utils.config['tracker_host'], utils.config['tracker_port']))
    message = Request(cmd="get_chunk_peers", share_id="{}".format(share_id), chunk_id="{}".format(chunk_id))
    sock.sendall(message.to_json())
    received = sock.recv(1024)
    sock.close()
    data = json.loads(received).get('data')
    data = [x for x in data if x != "{}:{}".format(utils.config['hostname'], utils.config['port'])]
    return data

def announce_chunk_download(share_id, chunk_id):
    with announce_lock:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((utils.config['tracker_host'], utils.config['tracker_port']))
        message = Request(cmd="report_chunk", ip=utils.config['hostname'], port=utils.config['port'], share_id="{}".format(share_id), chunk_id="{}".format(chunk_id))
        sock.sendall(message.to_json())
        sock.close()

def announce_all_chunks():
    for _, share in state.shares.items():
        for chunk in share['chunks']:
            announce_chunk_download(share['id'], chunk['part'])

def send_keepalive():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((utils.config['tracker_host'], utils.config['tracker_port']))
    message = Request(cmd="report_active", ip=utils.config['hostname'], port=utils.config['port'])
    sock.sendall(message.to_json())
    sock.close()

class Request(object):
    def __init__(self, js=None, cmd=None, ip=None, port=None, share_id=None, chunk_id=None):
        if js is not None:
            self.__dict__ = json.loads(js)
            return

        self.cmd = cmd
        self.ip = ip
        self.port = port
        self.share_id = share_id
        self.chunk_id = chunk_id

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
