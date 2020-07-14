import datetime
import logging
import re
from pathlib import Path
from typing import List

from entity import GameEntity
from event import Event
from match import MatchReportFactory


class UnhandledLine(Exception):
    pass


class LogParser:
    """
    Parser of a single logfile.
    """

    @classmethod
    def from_raw_text(cls, text):
        lines = text.split("\n")
        return cls(lines)

    @classmethod
    def from_filename(cls, filename):
        lines = cls._get_lines(filename)
        return cls(lines)

    @classmethod
    def _get_lines(cls, logfile):
        with open(logfile, "r") as file:
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
                logging.debug(f"Ignoring line: {line}")
                continue
        return events

    def _parse_line(self, line) -> Event:
        event_factory = EventFactory()
        event = event_factory.from_log_line(line)
        return event

    def get_match_report(self):
        match_report_factory = MatchReportFactory()
        events = self.get_events()
        match_report = match_report_factory.completed_match_report(events)
        return match_report

    def get_round_reports(self):
        match_report_factory = MatchReportFactory()
        events = self.get_events()
        round_reports = match_report_factory.incomplete_match_round_reports(events)
        return round_reports


class LogDirectoryParser:
    """
    Parser of an entire directory of logs
    """

    def __init__(self, path):
        self._path = Path(path)

    def get_all_match_reports(self):
        reports = []
        for file in self._path.iterdir():
            logging.info(f"Parsing {file}")
            parser = LogParser.from_filename(file)
            report = parser.get_match_report()
            reports.append(report)
        return reports


class EventFactory:
    """
    Parser of a single log line
    """

    def get_regex_event_mapping(self):
        return {event_type.REGEX: event_type for event_type in Event.__subclasses__()}

    def get_regex_game_entity_mapping(self):
        return {
            event_type.REGEX: event_type for event_type in GameEntity.__subclasses__()
        }

    def from_log_line(self, line):
        for regex, event_type in self.get_regex_event_mapping().items():
            regex_match = regex.search(line)
            if regex_match:
                timestamp = self._get_timestamp_from_line(line)
                event_data = self._get_data_from(regex_match)
                event = event_type(timestamp=timestamp, **event_data)
                return event
        raise UnhandledLine(line)

    def _get_timestamp_from_line(self, line):
        timestamp_str = re.search(
            r"L (\d{2}\/\d{2}\/\d{4} - \d{2}:\d{2}:\d{2}):", line
        ).group(1)
        timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%Y - %H:%M:%S")
        return timestamp

    def _get_data_from(self, match):
        # convert the match object into a dictionary with the key/values of the matched groups
        data = {}
        for key in match.re.groupindex:
            value = match[key]
            data[key] = self._cast_to_correct_type(value)
        return data

    def _cast_to_correct_type(self, value):
        for regex, game_entity_type in self.get_regex_game_entity_mapping().items():
            regex_match = regex.search(value)
            if regex_match:
                entity_data = self._get_data_from(regex_match)
                entity = game_entity_type(**entity_data)
                return entity
        # no regex match found
        try:
            return int(value)
        except ValueError:
            # logging.debug(f"Entity not found, using as raw string: {value}")
            return value
