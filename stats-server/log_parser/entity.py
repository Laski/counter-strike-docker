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
    REGEX = re.compile(
        r"(?P<nickname>.*)<\d+><STEAM_0:[0-1]:(?P<steam_id>\d+)><[A-Z]*>"
    )

    def __init__(self, nickname, steam_id):
        self._nickname = nickname
        self._steam_id = steam_id

    def __eq__(self, other):
        # players are identified by their Steam ID
        return isinstance(other, Player) and other._steam_id == self._steam_id

    def __hash__(self):
        # needed because we redefined __eq__
        return hash(self._steam_id)

    def get_nickname(self):
        return self._nickname

    def __repr__(self):
        return self.get_nickname()


class Weapon(GameEntity):
    REGEX = re.compile(r'with "(?P<name>\w+)"')

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, Weapon) and other.get_name() == self.get_name()

    def __hash__(self):
        return hash(self.get_name())

    def __repr__(self):
        return self.get_name()


class Team(GameEntity):
    REGEX = re.compile(r'[Tt]eam "(?P<name>CT|TERRORIST|SPECTATOR)"')

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def __eq__(self, other):
        return isinstance(other, Team) and other.get_name() == self.get_name()

    def __hash__(self):
        return hash(self.get_name())

    def __repr__(self):
        return self.get_name()


CT_team = Team("CT")
Terrorist_team = Team("TERRORIST")
Spectator_team = Team("SPECTATOR")
