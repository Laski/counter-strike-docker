import logging
from typing import Any, Dict, List, Optional

from log_parser.entity import CT_team, Player, Team, Terrorist_team
from log_parser.event import Event
from log_parser.report import MatchReport, RoundReport


class RoundInProgress:
    def __init__(self, team_composition: Dict[Team, List[Player]]):
        self._events: List[Event] = []
        self._ended = False
        self._team_composition = team_composition
        self._winner_team = None

    def has_ended(self):
        return self._ended

    def end(self) -> None:
        self._ended = True

    def record_event(self, event: Event):
        self._events.append(event)

    def set_winner_team(self, team):
        self._winner_team = team

    def get_round_report(self) -> RoundReport:
        assert self._ended
        first_event = self._events[0]
        start_time = first_event.get_timestamp()
        last_event = self._events[-1]
        end_time = last_event.get_timestamp()
        return RoundReport(
            start_time=start_time,
            end_time=end_time,
            events=self._events,
            team_composition=self._team_composition,
            winner_team=self._winner_team,
        )


class MatchInProgress:
    """
    A match is a sequence of rounds happening in a given map.
    It's useful to construct MatchReports while parsing a log file.
    """

    def __init__(self) -> None:
        self._map_name = ""
        self._match_events: List[Event] = []
        self._ended_round_reports: List[RoundReport] = []
        self._team_composition: Dict[Team, List[Player]] = {CT_team: [], Terrorist_team: []}
        self._ongoing_round: Optional[RoundInProgress] = None
        self._started = False
        self._ended = False

    def set_map_name(self, map_name):
        self._map_name = map_name

    def record_match_event(self, event: Event) -> None:
        self._match_events.append(event)

    def record_round_event(self, event: Event) -> None:
        assert self._ongoing_round
        self._ongoing_round.record_event(event)

    def start_new_round(self) -> None:
        if self._ongoing_round:
            assert self._ongoing_round.has_ended()
        self._ongoing_round = RoundInProgress(self._team_composition)

    def end_current_round(self) -> None:
        assert self._ongoing_round
        self._ongoing_round.end()
        round_report = self._ongoing_round.get_round_report()
        self._ended_round_reports.append(round_report)

    def impact_current_round_with(self, event: Event):
        assert self._ongoing_round
        event.impact_round(self._ongoing_round)

    def start(self):
        self._started = True

    def end(self):
        self._ended = True

    def get_match_report(self):
        assert self._ended or not self._started

        report = MatchReport(
            match_events=self._match_events,
            map_name=self._map_name,
            rounds=self._ended_round_reports,
        )
        return report

    def get_ended_round_reports(self) -> List[RoundReport]:
        return self._ended_round_reports

    def add_player_to_team(self, team: Team, player: Player) -> None:
        self.remove_player_if_present(player)
        if team in self._team_composition.keys():
            self._team_composition[team].append(player)

    def remove_player_if_present(self, player: Player) -> None:
        if player in self._team_composition[CT_team]:
            self._team_composition[CT_team].remove(player)
        if player in self._team_composition[Terrorist_team]:
            self._team_composition[Terrorist_team].remove(player)


class MatchReportFactory:
    def completed_match_report(self, events):
        match = MatchInProgress()
        for event in events:
            logging.debug(f"Resolving event: {event}")
            event.impact_match(match)
        return match.get_match_report()

    def incomplete_match_round_reports(self, events: List[Any]) -> List[RoundReport]:
        match = MatchInProgress()
        for event in events:
            event.impact_match(match)
        return match.get_ended_round_reports()
