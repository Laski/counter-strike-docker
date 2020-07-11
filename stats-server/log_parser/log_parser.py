import datetime
import re
from typing import List

from event import Event
from match import MatchInProgress


class UnhandledLine(Exception):
    pass


class EventFactory(object):
    def get_regex_event_mapping(self):
        return {event_type.REGEX: event_type for event_type in Event.__subclasses__()}

    def from_log_line(self, line):
        for regex, event_type in self.get_regex_event_mapping().items():
            regex_match = re.search(regex, line)
            if regex_match:
                timestamp = self._get_timestamp_from_line(line)
                event_data = self._get_data_from(regex_match)
                event = event_type(timestamp=timestamp, **event_data)
                return event
        raise UnhandledLine(line)

    def _get_timestamp_from_line(self, line):
        timestamp_str = re.search(r'L (\d{2}\/\d{2}\/\d{4} - \d{2}:\d{2}:\d{2}):', line).group(1)
        timestamp = datetime.datetime.strptime(timestamp_str, '%m/%d/%Y - %H:%M:%S')
        return timestamp

    def _get_data_from(self, match):
        # convert the match object into a dictionary with the key/values of the matched groups
        return {key: match[key] for key in match.re.groupindex}


class MatchReportFactory(object):
    def from_event_list(self, events):
        match = MatchInProgress()
        for event in events:
            event.impact_match(match)
        assert match.has_ended()
        return match.get_match_report()


class LogParser:
    """
    Parser of a single logfile.
    """

    @classmethod
    def from_raw_text(cls, text):
        lines = text.split('\n')
        return cls(lines)

    @classmethod
    def from_filename(cls, filename):
        lines = cls._get_lines(filename)
        return cls(lines)

    @classmethod
    def _get_lines(cls, logfile):
        with open(logfile, 'r') as file:
            lines = file.readlines()
        return lines

    def __init__(self, lines):
        self._lines = lines

    def get_events(self) -> List[Event]:
        events = []
        for line in self._lines:
            try:
                event = self._parse_line(line)
                events.append(event)
            except UnhandledLine:
                continue
        return events

    def _parse_line(self, line) -> Event:
        event_factory = EventFactory()
        event = event_factory.from_log_line(line)
        return event

    def get_match_report(self):
        match_report_factory = MatchReportFactory()
        events = self.get_events()
        match_report = match_report_factory.from_event_list(events)
        return match_report
