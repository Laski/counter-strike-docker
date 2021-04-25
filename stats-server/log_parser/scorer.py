import datetime
import logging
from abc import ABC
from collections import defaultdict
from typing import Collection, Dict, List, Mapping, NamedTuple, Optional, Tuple

from log_parser.entity import Player
from log_parser.glicko2 import PlayerRating
from log_parser.report import MatchReport, MatchReportCollection, PlayerTable


class FullScore(NamedTuple):
    value: float
    string: str
    confidence: float


class ScorerStrategy(ABC):
    """
    A scorer assings numbers to players given some criteria.
    """

    stat_name = None
    stat_explanation = None

    def __init__(self, filter_less_than: int = 0):
        """
        :param filter_less_than: the amount of rounds a player must have played in order to be assigned a score
        """
        self.filter_treshold = filter_less_than

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        raise NotImplementedError("SubclassResponsibility")

    def _stringify_scores(self, scores: Mapping[Player, float]) -> Mapping[Player, str]:
        return {player: str(score) for player, score in scores.items()}

    def get_confidence_in_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        """
        Returns a level of confidence in the score returned (a number between 0 and 1).
        Default calculation is 1 if the number of rounds the player was involved in is more than the filter_less_than
        parameter (and 0 otherwise).
        Other scorers may override this value, usually with  the percentage of rounds this player was involved in.
        """
        stats_by_player: PlayerTable = match_reports.collect_stats()

        confidence_table = {}
        for player, stats in stats_by_player.items():
            player_rounds = stats.total_rounds_played()
            confidence_table[player] = 1 if player_rounds >= self.filter_treshold else 0
        return confidence_table

    def get_full_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, FullScore]:
        """
        Returns, for each player, all three characteristics of the score: value, string and confidence
        """
        score_values = self.get_player_scores(match_reports)
        string_values = self._stringify_scores(score_values)
        confidence_values = self.get_confidence_in_player_scores(match_reports)
        full_scores = {}
        for player in score_values:
            value = score_values[player]
            string = string_values[player]
            confidence = confidence_values[player]
            full_scores[player] = FullScore(value, string, confidence)
        return full_scores


class DefaultScorer(ScorerStrategy):
    """
    The default CS1.6 scoring method: kills - deaths
    """

    stat_name = "Classic\u00A0score"
    stat_explanation = "kills - deaths"

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        scores: Dict[Player, int] = defaultdict(int)
        stats_by_player: PlayerTable = match_reports.collect_stats()
        for player, stats in stats_by_player.items():
            scores[player] += stats.kills
            scores[player] -= stats.deaths
        return scores

    def get_confidence_in_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        # we always have full confidence in this value
        return defaultdict(lambda: 1)


class WinRateScorer(ScorerStrategy):
    """
    Percentage of rounds won by the player
    """

    stat_name = "Win rate"
    stat_explanation = "Porcentaje de rondas ganadas por el jugador."

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        scores: Dict[Player, float] = defaultdict(int)
        stats_by_player: PlayerTable = match_reports.collect_stats()
        for player, stats in stats_by_player.items():
            rounds_played = stats.total_rounds_played()
            if rounds_played:
                rounds_won = stats.rounds_won
                scores[player] = rounds_won / rounds_played
        return scores

    def _stringify_scores(self, scores: Mapping[Player, float]) -> Mapping[Player, str]:
        return {player: f"{score * 100:.2f}%" for player, score in scores.items()}


class TimeSpentScorer(ScorerStrategy):
    """
    Time spent in the server
    """

    stat_name = "Time spent"
    stat_explanation = "Horas pasadas en el server"

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        stats_by_player: PlayerTable = match_reports.collect_stats()
        scores = {player: stats.time_spent_in_hours() for player, stats in stats_by_player.items()}
        return scores

    def _stringify_scores(self, scores: Mapping[Player, float]) -> Mapping[Player, str]:
        def _hours_to_string(hours: float) -> str:
            timedelta = datetime.timedelta(seconds=hours * 3600)
            seconds = timedelta.total_seconds()
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return f'{h:0.0f}:{m:0.0f}:{s:0.0f}'

        scores = {player: _hours_to_string(hours) for player, hours in scores.items()}
        return scores

    def get_confidence_in_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        # we always have full confidence in this value
        return defaultdict(lambda: 1)


class KillsScorer(ScorerStrategy):
    stat_name = "Kills"
    stat_explanation = "Kills totales del jugador"

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        stats_by_player: PlayerTable = match_reports.collect_stats()
        scores = {player: stats.kills for player, stats in stats_by_player.items()}
        return scores

    def get_confidence_in_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        # we always have full confidence in this value
        return defaultdict(lambda: 1)


class DeathsScorer(ScorerStrategy):
    stat_name = "Deaths"
    stat_explanation = "Deaths totales del jugador"

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        stats_by_player: PlayerTable = match_reports.collect_stats()
        scores = {player: stats.deaths for player, stats in stats_by_player.items()}
        return scores

    def get_confidence_in_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        # we always have full confidence in this value
        return defaultdict(lambda: 1)


class TotalRoundsScorer(ScorerStrategy):
    stat_name = "Total rounds"
    stat_explanation = "Cantidad de rondas terminadas"

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        stats_by_player: PlayerTable = match_reports.collect_stats()
        scores = {player: stats.total_rounds_played() for player, stats in stats_by_player.items()}
        return scores

    def get_confidence_in_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        # we always have full confidence in this value
        return defaultdict(lambda: 1)


class GlickoScorer(ScorerStrategy):
    """
    Each kill represents a match between the two involved players, with the killer as the winner.
    Both players recieve an Glicko ranking update after each kill.
    """

    stat_name = "ELO ranking"
    stat_explanation = "Puntaje dinámico similar al ELO del ajedrez. Matar a un jugador muy por encima de tu ranking te da más puntos, morir a manos de un jugador por debajo te resta más puntos."

    def _calculate_rankings(self, match_reports: MatchReportCollection) -> Mapping[Player, PlayerRating]:
        rankings: Mapping[Player, PlayerRating] = defaultdict(PlayerRating)
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
        return rankings

    def get_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, float]:
        rankings = self._calculate_rankings(match_reports)
        return {player: ranking.rating for player, ranking in rankings.items()}

    def _stringify_scores(self, scores: Mapping[Player, float]) -> Mapping[Player, str]:
        raise NotImplementedError  # this can't be done correctly here, as we need the standard deviance too. see below.

    def get_full_player_scores(self, match_reports: MatchReportCollection) -> Mapping[Player, FullScore]:
        # we override the parent method because we can't calculate the strings from the final scores only.
        rankings = self._calculate_rankings(match_reports)
        confidence_values = self.get_confidence_in_player_scores(match_reports)
        full_scores = {}
        for player, ranking in rankings.items():
            value = ranking.rating
            lower, top = value - 1.96 * ranking.rd, value + 1.96 * ranking.rd
            string = f"[{lower:.2f},\u00A0{top:.2f}]"  # non-breaking space
            confidence = confidence_values[player]
            value = lower  # sorting by lower value possible makes more sense?
            full_scores[player] = FullScore(value, string, confidence)
        return full_scores


class MatchStatsExtractor:
    """
    The stats extractor makes a list of scores for each player given a scoring strategy (see above).
    """

    def __init__(
        self,
        match_reports: Collection[MatchReport],
        scorer: Optional[ScorerStrategy] = None,
    ):
        self._match_reports = MatchReportCollection(match_reports)
        self._scorer = scorer or DefaultScorer()

    def get_sorted_score_table(self) -> List[Tuple[Player, float]]:
        scores = self._scorer.get_player_scores(self._match_reports)
        sorted_score_table = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return sorted_score_table

    def get_best_player(self) -> Tuple[Player, float]:
        score_table = self.get_sorted_score_table()
        return score_table[0]
