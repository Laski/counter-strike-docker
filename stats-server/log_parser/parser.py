import datetime
import logging
import pickle
import re
from pathlib import Path
from re import Match
from typing import Any, Dict, List, Pattern, Union

from log_parser.entity import GameEntity
from log_parser.event import Event
from log_parser.match import MatchReportFactory
from log_parser.report import MatchReport, RoundReport


class UnhandledLine(Exception):
    pass


class LogParser:
    """
    Parser of a single logfile.
    """

    @classmethod
    def from_raw_text(cls, text: str) -> 'LogParser':
        lines = text.split("\n")
        return cls(lines)

    @classmethod
    def from_filename(cls, filename: Union[str, Path]) -> 'LogParser':
        lines = cls._get_lines(filename)
        return cls(lines)

    @classmethod
    def _get_lines(cls, logfile: Union[str, Path]) -> List[str]:
        with open(logfile, "r") as file:
            lines = file.readlines()
        return lines

    def __init__(self, lines: List[str]) -> None:
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

    def _parse_line(self, line: str) -> Event:
        event_factory = EventFactory()
        event = event_factory.from_log_line(line)
        return event

    def get_match_report(self) -> MatchReport:
        match_report_factory = MatchReportFactory()
        events = self.get_events()
        match_report = match_report_factory.completed_match_report(events)
        return match_report

    def get_round_reports(self) -> List[RoundReport]:
        match_report_factory = MatchReportFactory()
        events = self.get_events()
        round_reports = match_report_factory.incomplete_match_round_reports(events)
        return round_reports


class LogDirectoryParser:
    """
    Parser of an entire directory of logs
    """

    def __init__(self, path: str) -> None:
        self._logs_path = Path(path)
        self._reports_paths = self._logs_path / 'reports'
        if not self._reports_paths.exists():
            self._reports_paths.mkdir()

    def get_all_match_reports(self) -> List['MatchReport']:
        reports = []
        log_files = (path for path in self._logs_path.iterdir() if path.name.endswith('.log'))
        for log_path in log_files:
            report = self.load_or_parse(log_path)
            reports.append(report)
        return reports

    def load_or_parse(self, log_path):
        match_report_path = self._reports_paths / log_path.name.replace('.log', '.pickle')
        if match_report_path.exists():
            report = self.load_from_file(match_report_path)
        else:
            report = self.parse_from_log(log_path)
            self.save_to_file(match_report_path, report)
        return report

    def save_to_file(self, match_report_path, report):
        with open(match_report_path, 'wb') as match_report_file:
            pickle.dump(report, match_report_file)

    def parse_from_log(self, log_path):
        logging.debug(f"Parsing {log_path}")
        parser = LogParser.from_filename(log_path)
        report = parser.get_match_report()
        return report

    def load_from_file(self, match_report_path):
        logging.debug(f"Loading report from {match_report_path}")
        with open(match_report_path, 'rb') as match_report_file:
            match_report = pickle.load(match_report_file)
        return match_report


class EventFactory:
    """
    Parser of a single log line
    """

    def get_regex_event_mapping(self) -> Dict[Pattern[str], type]:
        return {event_type.REGEX: event_type for event_type in Event.__subclasses__() if event_type.REGEX}

    def get_regex_game_entity_mapping(self) -> Dict[Pattern[str], type]:
        return {event_type.REGEX: event_type for event_type in GameEntity.__subclasses__() if event_type.REGEX}

    def from_log_line(self, line: str) -> Event:
        for regex, event_type in self.get_regex_event_mapping().items():
            regex_match = regex.search(line)
            if regex_match:
                timestamp = self._get_timestamp_from_line(line)
                event_data = self._get_data_from(regex_match)
                event = event_type(timestamp=timestamp, **event_data)
                return event
        raise UnhandledLine(line)

    def _get_timestamp_from_line(self, line: str) -> datetime.datetime:
        possible_timestamp = re.search(r"L (\d{2}\/\d{2}\/\d{4} - \d{2}:\d{2}:\d{2}):", line)
        if possible_timestamp:
            timestamp_str = possible_timestamp.group(1)
            timestamp = datetime.datetime.strptime(timestamp_str, "%m/%d/%Y - %H:%M:%S")
            return timestamp
        else:
            raise Exception("No timestamp found in line")

    def _get_data_from(self, match: Match) -> Dict[str, Any]:
        # convert the match object into a dictionary with the key/values of the matched groups
        data = {}
        for key in match.re.groupindex:
            value = match[key]
            data[key] = self._cast_to_correct_type(value)
        return data

    def _cast_to_correct_type(self, value: str) -> Union[int, str]:
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
