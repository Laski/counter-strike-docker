import logging
from abc import ABC
from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from log_parser.entity import Player
from log_parser.report import MatchReport, PlayerStats


class ScorerStrategy(ABC):
    def get_player_scores(self, match_reports: Iterable[MatchReport]) -> Mapping[Player, float]:
        raise NotImplementedError("SubclassResponsibility")

    def collect_stats(self, match_reports: Iterable[MatchReport]) -> Dict[Player, PlayerStats]:
        stats_by_player: Dict[Player, PlayerStats] = defaultdict(PlayerStats)
        for report in match_reports:
            report.add_to_player_stats_table(stats_by_player)
            logging.debug(f"Stats collected for match {report}")
        return stats_by_player


class DefaultScorer(ScorerStrategy):
    """
    The default CS1.6 scoring method: kills - deaths
    """

    def get_player_scores(self, match_reports: Iterable[MatchReport]) -> Mapping[Player, float]:
        scores: Dict[Player, int] = defaultdict(int)
        stats_by_player = self.collect_stats(match_reports)
        for player, stats in stats_by_player.items():
            scores[player] += stats.kills
            scores[player] -= stats.deaths
        return scores


class WinRateScorer(ScorerStrategy):
    """
    Percentage of rounds won by the player
    """

    def get_player_scores(self, match_reports: Iterable[MatchReport]) -> Mapping[Player, float]:
        scores: Dict[Player, float] = defaultdict(int)
        stats_by_player = self.collect_stats(match_reports)
        for player, stats in stats_by_player.items():
            rounds_played = stats.rounds_won + stats.rounds_lost
            if rounds_played:
                scores[player] = stats.rounds_won / rounds_played
        return scores


class MatchStatsExtractor:
    def __init__(self, match_reports: Iterable[MatchReport], scorer: Optional[ScorerStrategy] = None):
        self._match_reports = match_reports
        self._scorer = scorer or DefaultScorer()

    def get_sorted_score_table(self) -> List[Tuple[Player, float]]:
        scores = self._scorer.get_player_scores(self._match_reports)
        sorted_score_table = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return sorted_score_table

    def get_best_player(self) -> Tuple[Player, float]:
        score_table = self.get_sorted_score_table()
        return score_table[0]
