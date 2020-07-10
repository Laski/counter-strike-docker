import collections
import datetime
import re
import unittest
from typing import List


class UnhandledLine(Exception):
    pass


class MatchInProgress:
    """
    A match is a sequence of rounds happening in a given map.
    This represents a match that hasn't ended yet.
    It's useful to construct Match objects while parsing a log file.
    """

    def __init__(self):
        self.ended_rounds = []
        self.ongoing_round = None


class Match:
    """
    An inmutable representation of an ended match.
    A match is a sequence of rounds happening in a given map.
    Every log file has one (and only one) match.
    """

    def __init__(self, start_time, end_time, map_name, rounds):
        self._start_time = start_time
        self._end_time = end_time
        self._map = map_name
        self._rounds = rounds

    def get_rounds(self):
        return self._rounds

    def get_first_blood(self):
        for event in self._all_events():
            if isinstance(event, AttackEvent):
                return event
        raise Exception("There's no blood in this game")

    def _all_events(self):
        return (event for round in self.get_rounds() for event in round.get_events())


EventWithTimestamp = collections.namedtuple('EventWithTimestamp', ('timestamp', 'event'))


class Round(object):
    def __init__(self, start_time, end_time, event_list):
        self._start_time = start_time
        self._end_time = end_time
        self._event_list = event_list

    def get_start_time(self):
        return self._start_time

    def get_end_time(self):
        return self._end_time

    def get_events(self):
        return self._event_list


class LogParser():
    """
    Parser of a single logfile
    """

    def __init__(self, logfile):
        self.lines = self._get_lines(logfile)

    def get_map_name(self) -> str:
        event_list = self.get_events()
        for timestamp, event in event_list:
            if isinstance(event, MapLoadingEvent):
                return event.get_map_name()
        raise Exception("MapLoadingEvent not found in the log file")

    def get_rounds(self):
        event_list = self.get_events()
        rounds = []
        events_in_round = []
        for event_with_timestamp in event_list:
            timestamp, event = event_with_timestamp
            if isinstance(event, RoundEndEvent):
                round_end_time = timestamp
                round = Round(start_time=round_start_time, end_time=round_end_time, event_list=events_in_round)
                rounds.append(round)
                events_in_round = []
            elif isinstance(event, RoundStartEvent):
                round_start_time = timestamp
            else:
                events_in_round.append(event)
        return rounds

    def get_match_start_time(self) -> datetime.datetime:
        round_start = self.lines[0]
        timestamp = self._get_timestamp_from_line(round_start)
        return timestamp

    def get_match_end_time(self):
        round_end = self.lines[-1]
        timestamp = self._get_timestamp_from_line(round_end)
        return timestamp

    def get_events(self) -> List['EventWithTimestamp']:
        event_list = []
        for line in self.lines:
            try:
                event = self._parse_line(line)
                timestamp = self._get_timestamp_from_line(line)
                event_with_timestamp = EventWithTimestamp(timestamp, event)
                event_list.append(event_with_timestamp)
            except UnhandledLine:
                continue
        return event_list

    def _parse_line(self, line):
        for event_type in Event.__subclasses__():
            if event_type.handles(line):
                event = event_type.new_from_line(line)
                return event
        raise UnhandledLine(line)

    def _get_timestamp_from_line(self, round_start):
        timestamp_str = re.search(r'L (\d{2}\/\d{2}\/\d{4} - \d{2}:\d{2}:\d{2}):', round_start).group(1)
        timestamp = datetime.datetime.strptime(timestamp_str, '%m/%d/%Y - %H:%M:%S')
        return timestamp

    def _get_lines(self, logfile):
        with open(logfile, 'r') as file:
            lines = file.readlines()
        return lines

    def get_match(self):
        start_time = self.get_match_start_time()
        end_time = self.get_match_end_time()
        map_name = self.get_map_name()
        rounds = self.get_rounds()
        return Match(start_time=start_time, end_time=end_time, map_name=map_name, rounds=rounds)


class Event:
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
    def new_from_line(cls, line):
        return cls()  # default event has no data

    def impact_match(self, match):
        raise NotImplementedError("Subclass responsibility")


class MapLoadingEvent(Event):
    REGEX = re.compile(r'Loading map \"(.*)\"\n')

    @classmethod
    def new_from_line(cls, line):
        match = cls.get_regex_match(line)
        map_name = match.group(1)
        return cls(map_name=map_name)

    def __init__(self, map_name: str):
        self._map_name = map_name

    def get_map_name(self) -> str:
        return self._map_name


class RoundStartEvent(Event):
    REGEX = re.compile(r'World triggered "Round_Start"\n')


class RoundEndEvent(Event):
    REGEX = re.compile(r'World triggered "Round_End"\n')


class AttackEvent(Event):
    REGEX = re.compile(
        r'"(?P<attacker>.+)" attacked "(?P<victim>.+)" with "(?P<weapon>.+)" \(damage "(?P<damage>\d+)"\) '
        r'\(damage_armor "(?P<damage_armor>\d+)"\) \(health "(?P<health>.+)"\) \(armor "(?P<armor>.+)"\)\n'
    )

    @classmethod
    def new_from_line(cls, line):
        match = cls.get_regex_match(line)
        attacker = match.group('attacker')
        return cls(attacker=attacker)

    def __init__(self, attacker: str):
        self._attacker = attacker

    def get_attacker(self):
        return self._attacker


class LogParserTests(unittest.TestCase):
    def test_can_read_the_map(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        # then the log parser can get the map
        assert parser.get_map_name() == 'awp_india'

    def test_can_read_the_timestamps(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        # then the log parser can get the start and end of a map
        assert parser.get_match_start_time() == datetime.datetime(2020, 4, 9, 20, 47, 30)
        assert parser.get_match_end_time() == datetime.datetime(2020, 4, 9, 21, 7, 51)

    def test_can_get_a_round_start_and_end(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        # then the log parser can get the start and end of the first round
        match = parser.get_match()
        first_round = match.get_rounds()[0]
        assert first_round.get_start_time() == datetime.datetime(2020, 4, 9, 20, 47, 34)
        assert first_round.get_end_time() == datetime.datetime(2020, 4, 9, 20, 47, 43)

    def test_can_get_a_round_first_blood(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser(filename)
        # then the log parser can get the start and end of the first round
        match = parser.get_match()
        first_blood = match.get_first_blood()
        assert first_blood.get_attacker() == 'Mcd.<4><STEAM_0:1:538382878><CT>'


if __name__ == '__main__':
    unittest.main()
