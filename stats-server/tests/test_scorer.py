import logging
import unittest

from log_parser.entity import Player
from log_parser.parser import LogDirectoryParser, LogParser
from log_parser.report import MatchReportCollection
from log_parser.scorer import DefaultScorer, GlickoScorer, TimeSpentScorer, WinRateScorer

logging.basicConfig(level=logging.INFO)


class ScorerTestCase(unittest.TestCase):
    def test_can_get_the_default_score_from_a_single_match(self):
        # given a match report
        filename = "tests/logs/L0409001.log"
        match_report = LogParser.from_filename(filename).get_match_report()
        # when given to the stats extractor
        scorer = DefaultScorer()
        stats = MatchReportCollection([match_report])
        # we can know the best player
        player = Player("Mcd.", 538382878)
        assert stats.get_best_player(scorer)[0] == player

    def test_can_get_the_default_score_from_many_matches(self):
        # given a list of matches
        logs = "tests/logs"
        match_reports = LogDirectoryParser(logs).get_all_match_reports()
        # when given to the stats extractor
        scorer = DefaultScorer()
        stats = MatchReportCollection(match_reports)
        # we can know the best player
        score_table = stats.get_sorted_score_table(scorer)
        print(score_table)
        player = Player("Mcd.", 538382878)
        best_player = score_table[0][0]
        assert best_player == player

    def test_can_filter_players_with_less_than_n_rounds(self):
        # given a list of matches
        logs = "tests/logs"
        match_reports = LogDirectoryParser(logs).get_all_match_reports()
        # when given to the stats extractor with a filter
        scorer = WinRateScorer(filter_less_than=10)
        stats = MatchReportCollection(match_reports)
        # we can know the best player
        score_table = stats.get_sorted_score_table(scorer)
        print(score_table)
        player = Player("Rocho", 86787335)
        best_player = score_table[0][0]
        assert best_player == player

    def test_can_get_time_spent_in_the_server_per_player(self):
        # given a list of matches
        logs = "tests/logs"
        match_reports = LogDirectoryParser(logs).get_all_match_reports()
        # when given to the stats extractor
        scorer = TimeSpentScorer()
        stats = MatchReportCollection(match_reports)
        # we can know the player that spent more time in the server
        score_table = stats.get_sorted_score_table(scorer)
        print(score_table)
        player = Player("Rocho", 86787335)
        best_player = score_table[0][0]
        assert best_player == player

    def test_can_get_glicko_ranking_per_player(self):
        # given a list of matches
        logs = "tests/logs"
        match_reports = LogDirectoryParser(logs).get_all_match_reports()
        # when given to the stats extractor
        scorer = GlickoScorer()
        stats = MatchReportCollection(match_reports)
        # we can know the player that has the best ranking
        score_table = stats.get_sorted_score_table(scorer)
        print(score_table)
        player = Player("Mcd.", 538382878)
        best_player = score_table[0][0]
        assert best_player == player


if __name__ == "__main__":
    unittest.main()
