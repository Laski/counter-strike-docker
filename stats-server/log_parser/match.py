import logging
from typing import Dict, List

from entity import CT_team, Player, Team, Terrorist_team
from report import MatchReport, RoundReport


class RoundInProgress:
    def __init__(self, team_composition: Dict[Team, List[Player]]):
        self._events = []
        self._ended = False
        self._team_composition = team_composition
        self._winner_team = None

    def has_ended(self):
        return self._ended

    def end(self):
        self._ended = True

    def record_event(self, event: "Event"):
        self._events.append(event)

    def set_winner_team(self, team):
        self._winner_team = team

    def get_round_report(self):
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
    This represents a match that hasn't ended yet.
    It's useful to construct MatchReports while parsing a log file.
    """

    def __init__(self):
        self._map_name = ""
        self._match_events = []
        self._ended_round_reports = []
        self._team_composition = {CT_team: [], Terrorist_team: []}
        self._ongoing_round = None
        self._started = False
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
        self._ongoing_round = RoundInProgress(self._team_composition)

    def end_current_round(self):
        self._ongoing_round.end()
        round_report = self._ongoing_round.get_round_report()
        self._ended_round_reports.append(round_report)

    def impact_current_round_with(self, event: "Event"):
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

    def get_ended_round_reports(self):
        return self._ended_round_reports

    def add_player_to_team(self, team, player):
        self.remove_player_if_present(player)
        if team in self._team_composition.keys():
            self._team_composition[team].append(player)

    def remove_player_if_present(self, player):
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

    def incomplete_match_round_reports(self, events):
        match = MatchInProgress()
        for event in events:
            event.impact_match(match)
        return match.get_ended_round_reports()
