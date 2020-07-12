import logging
import unittest
from abc import ABC
from collections import defaultdict
from typing import List, Tuple

from entity import Player
from report import MatchReport
from .log_parser import LogDirectoryParser, LogParser

logging.basicConfig(level=logging.DEBUG)


class ScorerStrategy(ABC):
    def get_player_scores(
        self, match_reports: List[MatchReport]
    ) -> List[Tuple[Player, int]]:
        raise NotImplementedError("SubclassResponsibility")


class DefaultScorer(ScorerStrategy):
    """
    The default CS1.6 scoring method: kills - deaths
    """

    def get_player_scores(
        self, match_reports: List[MatchReport]
    ) -> List[Tuple[Player, int]]:
        scores = defaultdict(int)
        for report in match_reports:
            stats_by_player = report.get_all_player_stats()
            for player, stats in stats_by_player.items():
                scores[player] += stats.kills
                scores[player] -= stats.deaths
        return [(player, score) for player, score in scores.items()]


class WinRateScorer(ScorerStrategy):
    """
    Percentage of rounds won by the player
    """

    def get_player_scores(self, match_report: MatchReport) -> List[Tuple[Player, int]]:
        round_reports = match_report.get_round_reports()
        scores = {}
        for player, stats in stats.items():
            scores[player] = stats.kills - stats.deaths
        return [(player, score) for player, score in scores.items()]


class MatchStatsExtractor:
    def __init__(self, match_reports: List[MatchReport], scorer: ScorerStrategy = None):
        self._match_reports = match_reports
        self._scorer = scorer or DefaultScorer()

    def get_score_table(self):
        scores = self._scorer.get_player_scores(self._match_reports)
        sorted_score_table = sorted(scores, key=lambda kv: kv[1], reverse=True)
        return sorted_score_table

    def get_best_player(self):
        score_table = self.get_score_table()
        return score_table[0]


class StatsTestCase(unittest.TestCase):
    def test_can_get_the_default_score_from_a_single_match(self):
        # given a match report
        filename = "logs/L0409001.log"
        match_report = LogParser.from_filename(filename).get_match_report()
        # when given to the stats creator
        stats = MatchStatsExtractor([match_report])
        # we can know the best player
        player = Player("Mcd.", 538382878)
        assert stats.get_best_player()[0] == player

    def test_can_get_the_default_score_from_many_matches(self):
        # given a list of matches
        logs = "logs"
        match_reports = LogDirectoryParser(logs).get_all_match_reports()
        # when given to the stats creator
        stats = MatchStatsExtractor(match_reports)
        # we can know the best player
        player = Player("Mcd.", 538382878)
        assert stats.get_best_player()[0] == player


if __name__ == "__main__":
    unittest.main()
