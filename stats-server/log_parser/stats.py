from collections import defaultdict
from typing import Collection, Dict, Iterable, Mapping

from log_parser.entity import Player
from log_parser.report import MatchReport, MatchReportCollection
from log_parser.scorer import FullScore, ScorerStrategy

StatsRow = Dict[str, FullScore]


class StatsTable:
    """
    The stats table can construct a table of stats about the players, based on many different scoring strategies.
    """

    def __init__(self, match_reports: Collection[MatchReport], scorers: Collection[ScorerStrategy]):
        self._match_reports = MatchReportCollection(match_reports)
        self._scorers = scorers

    def get_full_table(self) -> Mapping[Player, StatsRow]:
        table = defaultdict(dict)
        stats = {}
        for scorer in self._scorers:
            stat_name = scorer.stat_name
            stats[stat_name] = scorer.stat_explanation
            scores = self._match_reports.get_full_player_scores(scorer)
            for player, value in scores.items():
                table[player][stat_name] = value
        filtered_table = {player: row for player, row in table.items() if len(row) == len(self._scorers)}
        return filtered_table

    def get_stats_explanations(self) -> Mapping[str, str]:
        return {scorer.stat_name: scorer.stat_explanation for scorer in self._scorers}
