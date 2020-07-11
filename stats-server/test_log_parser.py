import datetime
import re
import unittest
from abc import ABC
from typing import List


class UnhandledLine(Exception):
    pass


class RoundInProgress:
    def __init__(self):
        self._events = []
        self._ended = False

    def has_ended(self):
        return self._ended

    def end(self):
        self._ended = True

    def record_event(self, event: 'Event'):
        self._events.append(event)

    def get_round_report(self):
        assert self._ended
        first_event = self._events[0]
        start_time = first_event.get_timestamp()
        last_event = self._events[-1]
        end_time = last_event.get_timestamp()
        return RoundReport(
            start_time=start_time,
            end_time=end_time,
            events=self._events
        )


class MatchInProgress:
    """
    A match is a sequence of rounds happening in a given map.
    This represents a match that hasn't ended yet.
    It's useful to construct MatchReport objects while parsing a log file.
    """

    def __init__(self):
        self._map_name = ''
        self._match_events = []
        self._ended_rounds = []
        self._ongoing_round = None
        self._ended = False

    def set_map_name(self, map_name):
        self._map_name = map_name

    def record_match_event(self, event):
        self._match_events.append(event)

    def record_round_event(self, event):
        self._ongoing_round.record_event(event)

    def start_new_round(self):
        if self._ongoing_round:
            assert self._ongoing_round.has_ended()
            round_report = self._ongoing_round.get_round_report()
            self._ended_rounds.append(round_report)
        self._ongoing_round = RoundInProgress()

    def end_current_round(self):
        self._ongoing_round.end()

    def impact_current_round_with(self, event: 'Event'):
        event.impact_round(self._ongoing_round)

    def has_ended(self):
        return self._ended

    def end(self):
        self._ended = True

    def get_match_report(self):
        assert self._ended
        first_event = self._match_events[0]
        start_time = first_event.get_timestamp()
        last_event = self._match_events[-1]
        end_time = last_event.get_timestamp()

        report = MatchReport(
            start_time=start_time,
            end_time=end_time,
            map_name=self._map_name,
            rounds=self._ended_rounds
        )
        return report


class MatchReport:
    """
    An inmutable representation of an ended match.
    A match is a sequence of rounds happening in a given map.
    Every log file contains one match.
    """

    def __init__(self, start_time, end_time, map_name, rounds):
        self._start_time = start_time
        self._end_time = end_time
        self._map_name = map_name
        self._rounds = tuple(rounds)  # make inmutable

    def get_rounds(self):
        return self._rounds

    def get_first_blood(self):
        for event in self._all_events():
            if isinstance(event, AttackEvent):
                return event
        raise Exception("There's no blood in this game")

    def get_map_name(self):
        return self._map_name

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def _all_events(self):
        return (event for round in self.get_rounds() for event in round.get_events())

class RoundReport(object):
    def __init__(self, start_time, end_time, events):
        self._start_time = start_time
        self._end_time = end_time
        self._events = tuple(events)  # make inmutable

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def get_events(self):
        return self._events


class LogParser:
    """
    Parser of a single logfile
    """

    def __init__(self, logfile):
        self.lines = self._get_lines(logfile)

    def get_map_name(self) -> str:
        events = self.get_events()
        for event in events:
            if isinstance(event, MapLoadingEvent):
                return event.get_map_name()
        raise Exception("MapLoadingEvent not found in the log file")

    def get_events(self) -> List['Event']:
        events = []
        for line in self.lines:
            try:
                event = self._parse_line(line)
                events.append(event)
            except UnhandledLine:
                continue
        return events

    def _parse_line(self, line):
        for event_type in Event.__subclasses__():
            if event_type.handles(line):
                event = event_type.new_from_line(line)
                return event
        raise UnhandledLine(line)

    def _get_lines(self, logfile):
        with open(logfile, 'r') as file:
            lines = file.readlines()
        return lines

    def get_match_report(self):
        match = MatchInProgress()
        for event in self.get_events():
            event.impact_match(match)
        assert match.has_ended()
        return match.get_match_report()


class Event(ABC):
    """
    An event represents something that happened in the match server.
    This usually corresponds to a line in the server log file.
    An event knows how to impact an MatchInProgress and change its state.
    """
    REGEX = None  # Subclass responsibility

    @classmethod
    def handles(cls, line):
        match = cls.get_regex_match(line)
        return bool(match)

    @classmethod
    def get_regex_match(cls, line):
        regex = cls.get_regex()
        match = re.search(regex, line)
        return match

    @classmethod
    def get_regex(cls):
        return cls.REGEX

    @classmethod
    def _get_timestamp_from_line(cls, line):
        timestamp_str = re.search(r'L (\d{2}\/\d{2}\/\d{4} - \d{2}:\d{2}:\d{2}):', line).group(1)
        timestamp = datetime.datetime.strptime(timestamp_str, '%m/%d/%Y - %H:%M:%S')
        return timestamp

    @classmethod
    def new_from_line(cls, line):
        timestamp = cls._get_timestamp_from_line(line)
        match = cls.get_regex_match(line)
        kwargs = cls._get_data_from(match)
        return cls(timestamp=timestamp, **kwargs)

    @classmethod
    def _get_data_from(cls, match):
        # by default, convert the match object into a dictionary with the key/values of the matched groups
        return {key: match[key] for key in match.re.groupindex}

    def __init__(self, timestamp):
        self._timestamp = timestamp

    def get_timestamp(self):
        return self._timestamp

    def impact_match(self, match: MatchInProgress):
        raise NotImplementedError("Subclass responsibility")

    def impact_round(self, round: RoundInProgress):
        raise NotImplementedError("This event does not know how to impact a round")


class MapLoadingEvent(Event):
    REGEX = re.compile(r'Loading map \"(?P<map_name>.*)\"\n')

    def __init__(self, timestamp, map_name: str):
        super().__init__(timestamp)
        self._map_name = map_name

    def get_map_name(self) -> str:
        return self._map_name

    def impact_match(self, match: MatchInProgress):
        match.set_map_name(self.get_map_name())
        match.record_match_event(self)


class RoundStartEvent(Event):
    REGEX = re.compile(r'World triggered "Round_Start"\n')

    def impact_match(self, match):
        match.start_new_round()
        match.record_round_event(self)


class RoundEndEvent(Event):
    REGEX = re.compile(r'World triggered "Round_End"\n')

    def impact_match(self, match):
        match.record_round_event(self)
        match.end_current_round()


class AttackEvent(Event):
    REGEX = re.compile(
        r'"(?P<attacker>.+)" attacked "(?P<victim>.+)" with "(?P<weapon>.+)" \(damage "(?P<damage>\d+)"\) '
        r'\(damage_armor "(?P<damage_armor>\d+)"\) \(health "(?P<health>.+)"\) \(armor "(?P<armor>.+)"\)\n'
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


class LogParserTests(unittest.TestCase):
    def test_can_read_the_map(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        match = parser.get_match_report()
        # then the log parser can get the map
        assert match.get_map_name() == 'awp_india'

    def test_can_read_the_timestamps(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        match = parser.get_match_report()
        # then the resulting match report knows it start and end time
        assert match.get_start_time() == datetime.datetime(2020, 4, 9, 20, 47, 30)
        assert match.get_end_time() == datetime.datetime(2020, 4, 9, 21, 7, 46)

    def test_can_get_a_round_start_and_end(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        match = parser.get_match_report()
        # then the resulting match report knows the start and end of the first round
        first_round = match.get_rounds()[0]
        assert first_round.get_start_time() == datetime.datetime(2020, 4, 9, 20, 47, 34)
        assert first_round.get_end_time() == datetime.datetime(2020, 4, 9, 20, 47, 43)

    def test_can_get_a_round_first_blood(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        match = parser.get_match_report()
        # then the resulting match report knows its first blood
        first_blood = match.get_first_blood()
        assert first_blood.get_attacker() == 'Mcd.<4><STEAM_0:1:538382878><CT>'


if __name__ == '__main__':
    unittest.main()
