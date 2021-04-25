import logging
import unittest

from log_parser.entity import Player
from log_parser.parser import LogDirectoryParser
from log_parser.scorer import DefaultScorer, GlickoScorer, TimeSpentScorer, WinRateScorer
from log_parser.stats import StatsTable

logging.basicConfig(level=logging.DEBUG)


class StatsTableTestCase(unittest.TestCase):
    def test_can_get_the_default_score_from_many_matches(self):
        # given a list of matches and a list of scorers
        logs = "tests/logs"
        match_reports = LogDirectoryParser(logs).get_all_match_reports()
        scorers = [GlickoScorer(), DefaultScorer(), WinRateScorer(), TimeSpentScorer()]
        # when given to the stats table
        stats = StatsTable(match_reports, scorers)
        # we can know the full scoring table
        score_table = stats.get_full_table()
        print(score_table)
        self.assertEqual(score_table[Player('Laski', 53940642)]['Score'].value, -12)
        self.assertEqual(score_table[Player('Laski', 53940642)]['Score'].string, '-12')
        self.assertAlmostEqual(score_table[Player('Laski', 53940642)]['Score'].confidence, 1)
        self.assertEqual(score_table[Player('Mcd.', 538382878)]['Score'].value, 26)
        self.assertEqual(score_table[Player('Mcd.', 538382878)]['Score'].string, '26')
        self.assertAlmostEqual(score_table[Player('Mcd.', 538382878)]['Score'].confidence, 1)

    if __name__ == "__main__":
        unittest.main()
