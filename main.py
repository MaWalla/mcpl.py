import json
import os
import sys
from time import sleep

from flask import Flask
from flask_sockets import Sockets

from playerlocation import MinecraftPlayerLocation


rcon_host = os.environ.get('RCON_HOST')
rcon_password = os.environ.get('RCON_PASSWORD')
rcon_port = os.environ.get('RCON_PORT', 25575)
fps = os.environ.get('REFRESH_RATE', 10)

if not rcon_host or not rcon_password:
    print('one or more env variables missing!', file=sys.stderr)
    print('please make sure that RCON_HOST, RCON_PASSWORD are set!', file=sys.stderr)
    print('Note: RCON_PORT and REFREH_RATE can also be set if necessary.', file=sys.stderr)
    exit(1)

app = Flask(__name__)
sockets = Sockets(app)

mcpl = MinecraftPlayerLocation(rcon_host, rcon_password, rcon_port, fps)


@sockets.route('/')
def mcpl_socket(ws):
    while not ws.closed:
        sleep(1 / int(fps))
        ws.send(json.dumps(mcpl.message))


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 25576), app, handler_class=WebSocketHandler)
    server.serve_forever()
