import datetime
import logging
import unittest

from .log_parser import LogParser

logging.basicConfig(level=logging.DEBUG)

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
        assert first_attack.get_attacker().get_nickname() == 'Mcd.'

    def test_can_get_a_round_first_kill(self):
        # given a log file
        filename = 'logs/L0409001.log'
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows its first kill
        first_kill = match_report.get_first_kill()
        assert first_kill.get_attacker().get_nickname() == 'Mcd.'

    def test_can_identify_users_even_if_they_change_nicknames(self):
        # given a user changed nickname in the middle of a match
        logtext = """
        L 06/24/2020 - 03:57:58: "estoy jugando un poco mejor<3><STEAM_0:1:538855093><CT>" attacked "Rocho<34><STEAM_0:1:86787335><TERRORIST>" with "mp5navy" (damage "13") (damage_armor "7") (health "29") (armor "70")
        L 07/04/2020 - 05:42:31: "a veces juego bien a veces mal<29><STEAM_0:1:538855093><CT>" attacked "Alberto Samid<25><STEAM_0:0:542598804><TERRORIST>" with "usp" (damage "21") (damage_armor "0") (health "79") (armor "0")
        """
        # when feeded to the log parser
        parser = LogParser.from_raw_text(logtext)
        events = parser.get_events()
        # then the resulting events share the user
        first_attack, second_attack = events
        assert first_attack.get_attacker() == second_attack.get_attacker()

    def test_can_identify_weapons(self):
        # given a log line with weapon data
        logtext = """
        L 06/24/2020 - 03:57:58: "estoy jugando un poco mejor<3><STEAM_0:1:538855093><CT>" attacked "Rocho<34><STEAM_0:1:86787335><TERRORIST>" with "mp5navy" (damage "13") (damage_armor "7") (health "29") (armor "70")
        """
        # when feeded to the log parser
        parser = LogParser.from_raw_text(logtext)
        events = parser.get_events()
        # then the resulting events know the weapon
        first_attack = events[0]
        assert first_attack.get_weapon().get_name() == 'mp5navy'

if __name__ == '__main__':
    unittest.main()
