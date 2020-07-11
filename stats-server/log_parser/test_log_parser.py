import datetime
import unittest

from .log_parser import LogParser


class LogParserTests(unittest.TestCase):
    def test_can_read_the_map(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows the map name
        assert match_report.get_map_name() == 'awp_india'

    def test_can_get_a_match_start_and_end(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows it start and end time
        assert match_report.get_start_time() == datetime.datetime(2020, 4, 9, 20, 47, 30)
        assert match_report.get_end_time() == datetime.datetime(2020, 4, 9, 21, 7, 46)

    def test_can_get_a_round_start_and_end(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        first_round_report = match_report.get_rounds()[0]
        # then the first round report knows the start and end of the first round
        assert first_round_report.get_start_time() == datetime.datetime(2020, 4, 9, 20, 47, 34)
        assert first_round_report.get_end_time() == datetime.datetime(2020, 4, 9, 20, 47, 43)

    def test_can_get_a_round_first_attack(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows its first attack
        first_attack = match_report.get_first_attack()
        assert first_attack.get_attacker() == 'Mcd.<4><STEAM_0:1:538382878><CT>'

    def test_can_get_a_round_first_kill(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows its first kill
        first_attack = match_report.get_first_kill()
        assert first_attack.get_attacker() == 'Mcd.<4><STEAM_0:1:538382878><CT>'

if __name__ == '__main__':
    unittest.main()
