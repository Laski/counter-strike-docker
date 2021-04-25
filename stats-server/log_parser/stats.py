from collections import defaultdict
from typing import Dict, Iterable, Mapping

from log_parser.entity import Player
from log_parser.report import MatchReportCollection
from log_parser.scorer import ScorerStrategy

StatsRow = Dict[str, float]


class StatsTable:
    """
    The stats table can construct a table of stats about the players, based on many different scoring strategies.
    """

    def __init__(self, match_reports: MatchReportCollection, scorers: Iterable[ScorerStrategy]):
        self._match_reports = match_reports
        self._scorers = scorers

    def get_full_table(self) -> Mapping[Player, StatsRow]:
        table = defaultdict(dict)
        stats = {}
        for scorer in self._scorers:
            stat_name = scorer.stat_name
            stats[stat_name] = scorer.stat_explanation
            scores = scorer.get_stringified_player_scores(self._match_reports)
            for player, value in scores.items():
                table[player][stat_name] = value
        return table

    def get_stats_explanations(self) -> Mapping[str, str]:
        return {scorer.stat_name: scorer.stat_explanation for scorer in self._scorers}
