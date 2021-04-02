import sys
import threading

from mcrcon import MCRcon
from time import sleep


class MinecraftPlayerLocation:
    rcon_connected = False

    def __init__(self, mcrcon_host, mcrcon_password, mcrcon_port, fps):
        self.timeout = 1 / int(fps)
        self.mcrcon = MCRcon(mcrcon_host, mcrcon_password, mcrcon_port)
        self.online_players = []
        self.message = {}

        self.refresh_rcon()
        threading.Thread(target=self.get_message).start()

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
                self.refresh_rcon()

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

    def get_message(self):
        while True:
            sleep(self.timeout)
            self.message = {player: info for player, info in self.parse_player_locations()}

