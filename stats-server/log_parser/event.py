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

    def __init__(self, timestamp):
        self._timestamp = timestamp

    def get_timestamp(self):
        return self._timestamp

    def impact_match(self, match: MatchInProgress):
        raise NotImplementedError("Subclass responsibility")

    def impact_round(self, round: RoundInProgress):
        raise NotImplementedError("This event does not know how to impact a round")

    def is_attack(self):
        return False

    def is_kill(self):
        return False


class MapLoadingEvent(Event):
    REGEX = re.compile(r'Loading map \"(?P<map_name>.*)\"')

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

    def impact_match(self, match):
        match.start_new_round()
        match.record_round_event(self)


class RoundEndEvent(Event):
    REGEX = re.compile(r'World triggered "Round_End"')

    def impact_match(self, match):
        match.record_round_event(self)
        match.end_current_round()


class AttackEvent(Event):
    REGEX = re.compile(
        r'"(?P<attacker>.+)" attacked "(?P<victim>.+)" (?P<weapon>with "\w+") \(damage "(?P<damage>\d+)"\) '
        r'\(damage_armor "(?P<damage_armor>\d+)"\) \(health "(?P<health>-?\d+)"\) \(armor "(?P<armor>-?\d+)"\)'
    )

    def __init__(self, timestamp, attacker, victim, weapon, damage, damage_armor, health, armor):
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

    def impact_match(self, match: MatchInProgress):
        match.impact_current_round_with(self)

    def impact_round(self, round: RoundInProgress):
        round.record_event(self)


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


class MatchEndEvent(Event):
    REGEX = re.compile(
        r'Team "CT" scored'
    )

    def impact_match(self, match):
        match.record_match_event(self)
        match.end()


class ServerEvent(Event):
    REGEX = re.compile(
        r'Server'
    )

    def impact_match(self, match):
        pass  # ignore
