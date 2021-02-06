import asyncio
import json
import os
import sys

import websockets
from mcrcon import MCRcon, MCRconException
from time import sleep


class MinecraftPlayerLocation:
    rcon_connected = False

    def __init__(self, mcrcon_host, mcrcon_password, websocket_port):
        self.mcrcon = MCRcon(mcrcon_host, mcrcon_password)
        self.online_players = []

        self.refresh_rcon()

        try:
            start_server = websockets.serve(self.send_data, '0.0.0.0', websocket_port)
        except websockets.exceptions.ConnectionClosedError:
            pass

        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    def parse_players(self):
        rcon_playerlist = self.mcrcon.command('list')
        try:
            _, players = rcon_playerlist.split(':')
        except ValueError:
            players = ''
        if players.strip():
            self.online_players = [player.strip() for player in players.split(', ')]
        else:
            self.online_players = []

    def refresh_rcon(self):
        self.mcrcon.disconnect()
        rcon_connected = False
        sleep(1)
        while not rcon_connected:
            try:
                self.mcrcon.connect()
                rcon_connected = True
                self.parse_players()
                print('Connection to rcon established!')
            except ConnectionRefusedError:
                print('Coudn\'t connect to rcon. I\'ll try again in a sec!', file=sys.stderr)
                sleep(1)

    def parse_player_locations(self):
        self.parse_players()
        for player in self.online_players:
            rcon_pos = self.mcrcon.command(f'data get entity {player} Pos')
            rcon_dimension = self.mcrcon.command(f'data get entity {player} Dimension')
            try:
                _, dimension = rcon_dimension.split(':', 1)
                _, coords = rcon_pos.split(':')
                x, y, z = coords.strip().replace('[', '').replace(']', '').replace('d', '').split(', ')
            except ValueError:
                dimension = ''
                x = y = z = 0
            cleaned_dimension = dimension.strip()
            yield player, {'name': player, 'x': x, 'y': y, 'z': z, 'dimension': cleaned_dimension}

    async def send_data(self, websocket, path):
        while True:
            try:
                data = {player: info for player, info in self.parse_player_locations()}

                if data:
                    message = json.dumps(data)
                    await websocket.send(message)

                self.mcrcon.connect()
            except (ConnectionRefusedError, BrokenPipeError):
                self.refresh_rcon()
            except ConnectionResetError:
                pass


rcon_host = os.environ.get('RCON_HOST')
rcon_password = os.environ.get('RCON_PASSWORD')
websocket_port = os.environ.get('WS_PORT')

if not rcon_host or not rcon_password or not websocket_port:
    print('one or more env variables missing!', file=sys.stderr)
    print('please make sure that RCON_HOST, RCON_PASSWORD and WS_PORT are set!', file=sys.stderr)
    exit(1)


mclp = MinecraftPlayerLocation(rcon_host, rcon_password, websocket_port)
mclp.mcrcon.disconnect()
