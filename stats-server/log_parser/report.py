import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from frozendict import frozendict

from entity import CT_team, Player, Team, Terrorist_team, Weapon
from event import Event


@dataclass
class PlayerStats:
    damage_inflicted: int = 0
    damage_received: int = 0
    kills: int = 0
    deaths: int = 0
    damage_inflicted_by_weapon: Dict["Weapon", int] = field(
        default_factory=lambda: defaultdict(int)
    )


class RoundReport:
    def __init__(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        events: List[Event],
        team_composition: Dict[Team, List[Player]],
        winner_team: Optional[Team],
    ):
        self._start_time = start_time
        self._end_time = end_time
        # copy and freeze the mutable objects
        self._events: Tuple[Event, ...] = tuple(events)
        self._team_composition = frozendict(
            {team: tuple(players) for team, players in team_composition.items()}
        )
        self._winner_team = winner_team

    def get_start_time(self) -> datetime.datetime:
        return self._start_time

    def get_end_time(self) -> datetime.datetime:
        return self._end_time

    def get_events(self) -> Tuple[Event, ...]:
        return self._events

    def get_ct_team_composition(self) -> Tuple[Player, ...]:
        return self._team_composition[CT_team]

    def get_terrorist_team_composition(self) -> Tuple[Player, ...]:
        return self._team_composition[Terrorist_team]

    def get_winner_team(self) -> Optional[Team]:
        return self._winner_team

    def get_all_players(self):
        return (
            player for players in self._team_composition.values() for player in players
        )

    def get_player_stats(self, player: Player) -> "PlayerStats":
        assert player in self.get_all_players()
        stats = PlayerStats()
        self.add_to_player_stats(player, stats)
        return stats

    def add_to_player_stats(self, player: Player, stats: PlayerStats):
        for event in self.get_events():
            event.impact_player_stats(player, stats)


class MatchReport:
    """
    An inmutable representation of an ended match.
    A match is a sequence of rounds happening in a given map.
    Every log file contains one match.
    """

    def __init__(self, match_events, map_name, rounds):
        self._match_events = match_events
        self._map_name = map_name
        self._round_reports = tuple(rounds)  # make inmutable

    def get_round_reports(self):
        return self._round_reports

    def get_first_attack(self):
        for event in self._all_round_events():
            if event.is_attack():
                return event
        raise Exception("There's no blood in this game")

    def get_first_kill(self):
        for event in self._all_round_events():
            if event.is_kill():
                return event
        raise Exception("There's no kills in this game")

    def get_map_name(self):
        return self._map_name

    def get_start_time(self):
        first_event = self._match_events[0]
        start_time = first_event.get_timestamp()
        return start_time

    def get_end_time(self):
        last_event = self._match_events[-1]
        end_time = last_event.get_timestamp()
        return end_time

    def get_rounds_by_winner_team(self):
        rounds_by_winner_team = {CT_team: [], Terrorist_team: []}
        for round_report in self.get_round_reports():
            winner_team = round_report.get_winner_team()
            if winner_team:
                rounds_by_winner_team[winner_team].append(round)
        return rounds_by_winner_team

    def get_scores(self):
        return {
            team: len(rounds_won)
            for team, rounds_won in self.get_rounds_by_winner_team().items()
        }

    def get_team_score(self, team):
        return self.get_scores()[team]

    def get_player_stats(self, player):
        stats = PlayerStats()
        for round in self.get_round_reports():
            round.add_to_player_stats(player, stats)
        return stats

    def get_all_player_stats(self):
        return {
            player: self.get_player_stats(player) for player in self.get_all_players()
        }

    def get_all_players(self):
        return (
            player
            for round in self.get_round_reports()
            for player in round.get_all_players()
        )

    def _all_round_events(self):
        return (
            event for round in self.get_round_reports() for event in round.get_events()
        )
