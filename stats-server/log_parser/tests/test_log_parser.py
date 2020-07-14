import datetime
import logging
import unittest

from entity import CT_team, Player, Terrorist_team, Weapon
from parser import LogDirectoryParser, LogParser

logging.basicConfig(level=logging.DEBUG)


class LogParserTests(unittest.TestCase):
    def test_can_read_the_map(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows the map name
        assert match_report.get_map_name() == "awp_india"

    def test_can_get_a_match_start_and_end(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows it start and end time
        assert match_report.get_start_time() == datetime.datetime(
            2020, 4, 9, 20, 47, 30
        )
        assert match_report.get_end_time() == datetime.datetime(2020, 4, 9, 21, 7, 51)

    def test_can_get_a_round_start_and_end(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        first_round_report = match_report.get_round_reports()[0]
        # then the first round report knows the start and end of the first round
        assert first_round_report.get_start_time() == datetime.datetime(
            2020, 4, 9, 20, 47, 34
        )
        assert first_round_report.get_end_time() == datetime.datetime(
            2020, 4, 9, 20, 47, 43
        )

    def test_can_get_a_round_first_attack(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows its first attack
        first_attack = match_report.get_first_attack()
        assert first_attack.get_attacker().get_nickname() == "Mcd."

    def test_can_get_a_round_first_kill(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows its first kill
        first_kill = match_report.get_first_kill()
        assert first_kill.get_attacker().get_nickname() == "Mcd."

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
        assert first_attack.get_weapon().get_name() == "mp5navy"

    def test_can_know_which_players_where_in_each_team_in_a_round(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting round report knows the players in each team
        second_round_report = match_report.get_round_reports()[1]
        assert len(second_round_report.get_ct_team_composition()) == 2
        assert len(second_round_report.get_terrorist_team_composition()) == 2

    def test_disconnected_players_leave_its_team(self):
        # given a log line with a player that disconnects
        logtext = """
        L 04/09/2020 - 20:47:39: "Rubimaister<2><STEAM_0:0:538627351><>" joined team "TERRORIST"
        L 04/09/2020 - 20:47:42: "Payvon<1><STEAM_0:1:539551953><>" joined team "CT"
        L 04/09/2020 - 20:48:29: World triggered "Round_Start"
        L 04/09/2020 - 20:47:45: "Mcd.<4><STEAM_0:1:538382878><>" joined team "CT"
        L 04/09/2020 - 20:47:50: "Rocho<6><STEAM_0:1:86787335><>" joined team "TERRORIST"
        L 04/09/2020 - 20:48:37: "triple_de_miga<7><STEAM_0:0:479244024><>" joined team "TERRORIST"
        L 04/09/2020 - 20:49:22: "triple_de_miga<7><STEAM_0:0:479244024><TERRORIST>" disconnected
        L 04/09/2020 - 20:48:29: World triggered "Round_End"
        """
        # when feeded to the log parser
        parser = LogParser.from_raw_text(logtext)
        round_reports = parser.get_round_reports()
        # then the resulting round report knows the player is not in a team anymore
        first_round_report = round_reports[0]
        assert len(first_round_report.get_ct_team_composition()) == 2
        assert len(first_round_report.get_terrorist_team_composition()) == 2

    def test_spectators_are_ignored(self):
        # given a log line with a player that becomes spectator
        logtext = """
        L 04/09/2020 - 20:47:39: "Rubimaister<2><STEAM_0:0:538627351><>" joined team "TERRORIST"
        L 04/09/2020 - 20:47:42: "Payvon<1><STEAM_0:1:539551953><>" joined team "CT"
        L 04/09/2020 - 20:48:29: World triggered "Round_Start"
        L 04/09/2020 - 21:48:38: "Laski<3><STEAM_0:0:53940642><>" joined team "CT"
        L 04/09/2020 - 21:48:38: "Laski<3><STEAM_0:0:53940642><>" joined team "SPECTATOR"
        L 04/09/2020 - 20:47:45: "Mcd.<4><STEAM_0:1:538382878><>" joined team "CT"
        L 04/09/2020 - 20:47:50: "Rocho<6><STEAM_0:1:86787335><>" joined team "TERRORIST"
        L 04/09/2020 - 20:48:29: World triggered "Round_End"
        """
        # when feeded to the log parser
        parser = LogParser.from_raw_text(logtext)
        round_reports = parser.get_round_reports()
        # then the resulting round report knows the player is not in a team
        first_round_report = round_reports[0]
        assert len(first_round_report.get_ct_team_composition()) == 2
        assert len(first_round_report.get_terrorist_team_composition()) == 2

    def test_can_know_the_final_match_score(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting round report knows the players in each team
        assert match_report.get_team_score(CT_team) == 28
        assert match_report.get_team_score(Terrorist_team) == 5

    def test_can_know_a_player_round_stats(self):
        # given a log where a player inflicted damage and killed an opponent
        logtext = """
        L 04/09/2020 - 20:48:29: World triggered "Round_Start"
        L 04/09/2020 - 20:47:45: "Mcd.<4><STEAM_0:1:538382878><>" joined team "CT"
        L 04/09/2020 - 21:07:39: "Mcd.<4><STEAM_0:1:538382878><CT>" attacked "triple_de_miga<11><STEAM_0:0:479244024><TERRORIST>" with "awp" (damage "106") (damage_armor "2") (health "-6") (armor "98")
        L 04/09/2020 - 21:07:39: "Mcd.<4><STEAM_0:1:538382878><CT>" killed "triple_de_miga<11><STEAM_0:0:479244024><TERRORIST>" with "awp"
        L 04/09/2020 - 21:07:41: "Mcd.<4><STEAM_0:1:538382878><CT>" attacked "Laski<3><STEAM_0:0:53940642><TERRORIST>" with "awp" (damage "52") (damage_armor "1") (health "48") (armor "99")
        L 04/09/2020 - 20:49:23: "Laski<3><STEAM_0:0:53940642><TERRORIST>" attacked "Mcd.<4><STEAM_0:1:538382878><CT>" with "knife" (damage "12") (damage_armor "2") (health "88") (armor "98")
        L 04/09/2020 - 20:48:29: World triggered "Round_End"
        """
        # when feeded to the log parser
        parser = LogParser.from_raw_text(logtext)
        round_reports = parser.get_round_reports()
        # then the resulting round report knows the round stats for the player
        first_round_report = round_reports[0]
        player = Player("Mcd.", 538382878)
        weapon = Weapon("awp")
        player_stats = first_round_report.get_player_stats(player)
        assert player_stats.damage_inflicted == 106 + 52
        assert player_stats.damage_inflicted_by_weapon[weapon] == 106 + 52
        assert player_stats.damage_received == 12
        assert player_stats.kills == 1

    def test_can_know_a_player_match_stats(self):
        # given a log file
        filename = "logs/L0409001.log"
        # when feeded to the log parser
        parser = LogParser.from_filename(filename)
        match_report = parser.get_match_report()
        # then the resulting match report knows the total match stats for the player
        player = Player("Mcd.", 538382878)
        player_stats = match_report.get_player_stats(player)
        awp = Weapon("awp")
        knife = Weapon("knife")
        assert player_stats.damage_inflicted == 5948
        assert player_stats.damage_inflicted_by_weapon == {awp: 5496, knife: 452}
        assert player_stats.damage_received == 1928
        assert player_stats.kills == 36
        assert player_stats.deaths == 10

    @unittest.skip
    def test_can_read_the_logs_from_an_entire_directory(self):
        # given a directory with many logs
        logs_path = "logs"
        # when the log parser tries to read them all
        # then it does not fail
        LogDirectoryParser(logs_path).get_all_match_reports()


if __name__ == "__main__":
    unittest.main()
