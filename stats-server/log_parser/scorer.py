import logging
from abc import ABC
from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from log_parser.entity import Player
from log_parser.glicko2 import PlayerRating
from log_parser.report import MatchReport, PlayerStats

PlayerTable = Dict[Player, PlayerStats]


class ScorerStrategy(ABC):
    """
    A scorer assings numbers to players given some criteria.
    """

    def collect_stats(self, match_reports: Iterable[MatchReport]) -> PlayerTable:
        stats_by_player: PlayerTable = defaultdict(PlayerStats)
        for report in match_reports:
            report.add_to_player_stats_table(stats_by_player)
            logging.debug(f"Stats collected for match {report}")
        stats_by_player = self._filter(stats_by_player)
        return stats_by_player

    def get_player_scores(self, match_reports: Iterable[MatchReport]) -> Mapping[Player, float]:
        raise NotImplementedError("SubclassResponsibility")

    def _filter(self, stats_by_player: PlayerTable) -> PlayerTable:
        # by default we do not filter
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
            rounds_played = stats.total_rounds_played()
            if rounds_played:
                rounds_won = stats.rounds_won
                scores[player] = rounds_won / rounds_played
        return scores

    def _filter(self, stats_by_player: PlayerTable) -> PlayerTable:
        # only players with more than 100 rounds
        return {player: stats for player, stats in stats_by_player.items() if stats.total_rounds_played() > 100}


class TimeSpentScorer(ScorerStrategy):
    """
    Time spent in the server
    """

    def get_player_scores(self, match_reports: Iterable[MatchReport]) -> Mapping[Player, float]:
        stats_by_player = self.collect_stats(match_reports)
        scores = {player: stats.time_spent_in_hours() for player, stats in stats_by_player.items()}
        return scores


class GlickoScorer(ScorerStrategy):
    """
    Each kill represents a match between the two involved players, with the killer as the winner.
    Both players recieve an Glicko ranking update after each kill.
    """

    def get_player_scores(self, match_reports: Iterable[MatchReport]) -> Mapping[Player, Tuple[float]]:
        rankings = defaultdict(PlayerRating)
        valid_matches = [report for report in match_reports if len(report.get_round_reports()) >= 2]
        for match in valid_matches:
            for kill in match.get_all_kills():
                attacker = kill.get_attacker()
                victim = kill.get_victim()
                attacker_ranking = rankings[attacker]
                victim_ranking = rankings[victim]
                logging.debug(f"Updating ranking of {attacker}[{attacker_ranking}] vs {victim}[{victim_ranking}]")
                attacker_ranking.register_win(victim_ranking)
            for player in rankings.keys():
                if player not in match.get_all_players():
                    rankings[player].did_not_compete()  # updates variance
        return {player: ranking.to_tuple() for player, ranking in rankings.items()}


class MatchStatsExtractor:
    """
    The stats extractor gets a list of scores for each player given a scoring strategy (see above).
    """

    def __init__(
        self, match_reports: Iterable[MatchReport], scorer: Optional[ScorerStrategy] = None,
    ):
        self._match_reports = match_reports
        self._scorer = scorer or DefaultScorer()

    def get_sorted_score_table(self) -> List[Tuple[Player, float]]:
        scores = self._scorer.get_player_scores(self._match_reports)
        sorted_score_table = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return sorted_score_table

    def get_best_player(self) -> Tuple[Player, float]:
        score_table = self.get_sorted_score_table()
        return score_table[0]
