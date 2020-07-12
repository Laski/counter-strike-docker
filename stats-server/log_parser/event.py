import re
from abc import ABC

from match import MatchInProgress, RoundInProgress


class Event(ABC):
    """
    An event represents something that happened in the match server.
    This usually corresponds to a line in the server log file.
    An event knows how to impact an MatchInProgress and change its state.
    """

    REGEX = None  # Useful to know how to construct the event from a logline

    # I know coupling an event with its string representation in a logfile sounds wrong.
    # But it's useful to have it near the __init__, and seems better than duplicating the event hierarchy elsewhere.
    # The logic that translates a logfile into a sequence of events is in the log_parser module (as it should).

    def __init__(self, timestamp):
        self._timestamp = timestamp

    def get_timestamp(self):
        return self._timestamp

    def impact_match(self, match: MatchInProgress):
        raise NotImplementedError("Subclass responsibility")

    def impact_round(self, round: RoundInProgress):
        raise NotImplementedError("This event does not know how to impact a round")

    def impact_player_stats(self, player: "Player", stats: "PlayerStats"):
        pass  # subclass may override this

    def is_attack(self):
        return False

    def is_kill(self):
        return False


class MapLoadingEvent(Event):
    REGEX = re.compile(r"Loading map \"(?P<map_name>.*)\"")

    def __init__(self, timestamp, map_name: str):
        super().__init__(timestamp)
        self._map_name = map_name

    def get_map_name(self) -> str:
        return self._map_name

    def impact_match(self, match: MatchInProgress):
        match.set_map_name(self.get_map_name())
        match.record_match_event(self)


class RoundStartEvent(Event):
    REGEX = re.compile(r'World triggered "Round_Start"')

    def impact_match(self, match: MatchInProgress):
        match.start_new_round()
        match.record_round_event(self)


class RoundEndEvent(Event):
    REGEX = re.compile(r'World triggered "Round_End"|World triggered "Restart_Round_')

    def impact_match(self, match: MatchInProgress):
        match.record_round_event(self)
        match.end_current_round()


class AttackEvent(Event):
    REGEX = re.compile(
        r'"(?P<attacker>.+)" attacked "(?P<victim>.+)" (?P<weapon>with "\w+") \(damage "(?P<damage>\d+)"\) '
        r'\(damage_armor "(?P<damage_armor>\d+)"\) \(health "(?P<health>-?\d+)"\) \(armor "(?P<armor>-?\d+)"\)'
    )

    def __init__(
        self, timestamp, attacker, victim, weapon, damage, damage_armor, health, armor
    ):
        super().__init__(timestamp)
        self._attacker = attacker
        self._victim = victim
        self._weapon = weapon
        self._damage = damage
        self._damage_armor = damage_armor
        self._health_after_attack = health
        self._armor_after_attack = armor

    def is_attack(self):
        return True

    def get_attacker(self):
        return self._attacker

    def get_weapon(self):
        return self._weapon

    def get_victim(self):
        return self._victim

    def impact_match(self, match: MatchInProgress):
        match.impact_current_round_with(self)

    def impact_round(self, round: RoundInProgress):
        round.record_event(self)

    def impact_player_stats(self, player: "Player", stats: "PlayerStats"):
        if player == self._attacker:
            stats.damage_inflicted += self._damage
            stats.damage_inflicted_by_weapon[self._weapon] += self._damage
        if player == self._victim:
            stats.damage_received += self._damage


class KillEvent(Event):
    REGEX = re.compile(
        r'"(?P<attacker>.+)" killed "(?P<victim>.+)" (?P<weapon>with "\w+")'
    )

    def __init__(self, timestamp, attacker, victim, weapon):
        super().__init__(timestamp)
        self._attacker = attacker
        self._victim = victim
        self._weapon = weapon

    def is_attack(self):
        return True

    def is_kill(self):
        return True

    def get_attacker(self):
        return self._attacker

    def impact_match(self, match: MatchInProgress):
        match.impact_current_round_with(self)

    def impact_round(self, round: RoundInProgress):
        round.record_event(self)

    def impact_player_stats(self, player: "Player", stats: "PlayerStats"):
        if player == self._attacker:
            stats.kills += 1
        if player == self._victim:
            stats.deaths += 1


class MatchStartedEvent(Event):
    REGEX = re.compile(r'World triggered "Game_Commencing"')

    def impact_match(self, match: MatchInProgress):
        match.record_match_event(self)
        match.start()


class MatchEndEvent(Event):
    REGEX = re.compile(r'Team "CT" scored|Log file closed')

    def impact_match(self, match: MatchInProgress):
        match.record_match_event(self)
        match.end()


class PlayerJoinsTeamEvent(Event):
    REGEX = re.compile(r'"(?P<player>.+)" joined (?P<team>team "[A-Z]+")')

    def __init__(self, timestamp, player, team):
        super().__init__(timestamp)
        self._player = player
        self._team = team

    def impact_match(self, match: MatchInProgress):
        match.record_match_event(self)
        match.add_player_to_team(self._team, self._player)


class PlayerDisconnectsEvent(Event):
    REGEX = re.compile(r'"(?P<player>.+)" disconnected')

    def __init__(self, timestamp, player):
        super().__init__(timestamp)
        self._player = player

    def impact_match(self, match: MatchInProgress):
        match.record_match_event(self)
        match.remove_player_if_present(self._player)


class TeamWinEvent(Event):
    REGEX = re.compile(r'(?P<team>Team "[A-Z]+") triggered "\w+_Win"')

    def __init__(self, timestamp, team):
        super().__init__(timestamp)
        self._team = team

    def impact_match(self, match: MatchInProgress):
        match.impact_current_round_with(self)

    def impact_round(self, round: RoundInProgress):
        round.set_winner_team(self._team)


class ServerEvent(Event):
    REGEX = re.compile(r"Server")

    def impact_match(self, match: MatchInProgress):
        pass  # ignore