import re
from abc import ABC


class GameEntity(ABC):
    """
    A game entity represents something that exists within a game.
    It usually corresponds to a part of a log file.
    For example, player and weapons are game entities.
    """
    REGEX = None  # Useful to know how to construct the entity from a logline


class Player(GameEntity):
    REGEX = re.compile(r'(?P<nickname>.*)<\d+><STEAM_0:[0-1]:(?P<steam_id>\d+)><(?P<team>.*)>')

    def __init__(self, nickname, steam_id, team):
        self._nickname = nickname
        self._steam_id = steam_id
        self._team = team

    def __eq__(self, other):
        # players are identified by their Steam ID
        return isinstance(other, Player) and other._steam_id == self._steam_id

    def __hash__(self):
        # needed because we redefined __eq__
        return hash(self._steam_id)

    def get_nickname(self):
        return self._nickname


class Weapon(GameEntity):
    REGEX = re.compile(r'with "(?P<name>\w+)"')

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name
