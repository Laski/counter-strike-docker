import logging
import subprocess
from pathlib import Path

from flask import Flask, make_response, redirect, render_template, send_from_directory, url_for

from log_parser.parser import LogDirectoryParser
from log_parser.report import MatchReportCollection
from log_parser.scorer import (
    DefaultScorer,
    GlickoScorer,
    TimeSpentScorer,
    TotalRoundsScorer,
    WinRateScorer,
)
from log_parser.stats import StatsTable

LOGS_PATH = "logs"
STATS_CACHE = {}


def update_table():
    logging.debug("Regenerating table")
    with open("stats.html", 'w') as output:
        subprocess.call(["./read-csdata.pl", "csstats.dat"], stdout=output)


def parse_logs(logs_path):
    logging.debug("Parsing logs")
    match_reports = LogDirectoryParser(logs_path).get_all_match_reports()
    return match_reports


def get_stats_for_season(season_logs_path):
    match_reports = parse_logs(season_logs_path)
    total_amount_of_rounds = MatchReportCollection(match_reports).get_total_number_of_rounds()
    filter_threshold = max(100, total_amount_of_rounds / 100)
    scorers = [
        GlickoScorer(filter_threshold),
        DefaultScorer(filter_threshold),
        WinRateScorer(filter_threshold),
        TotalRoundsScorer(filter_threshold),
        TimeSpentScorer(filter_threshold),
    ]
    stats = StatsTable(match_reports, scorers)
    table = stats.get_full_table()
    stat_names = [scorer.stat_name for scorer in scorers]
    stat_details = [(scorer.stat_name, scorer.stat_explanation) for scorer in scorers]

    def flatten_player_row(table, player):
        return [table[player].get(stat_name) for stat_name in stat_names]

    flat_table = {player.get_nickname(): flatten_player_row(table, player) for player in table}
    return stat_details, flat_table


def get_last_season_number():
    old_seasons_path = Path(LOGS_PATH) / "seasons"
    if old_seasons_path.exists():
        last_archived_season = max(
            int(path.name.lstrip('s')) for path in old_seasons_path.iterdir() if path.name.startswith("s")
        )
        return last_archived_season + 1
    else:
        return 1


def get_season_logs_path(season_id):
    return Path(LOGS_PATH) / "seasons" / f"s{season_id:02d}"  # zero-padded two places int


def get_or_create_stats_from_previous_season(season_id):
    if season_id in STATS_CACHE:
        return STATS_CACHE[season_id]
    season_logs_path = get_season_logs_path(season_id)
    STATS_CACHE[season_id] = get_stats_for_season(season_logs_path)
    return get_or_create_stats_from_previous_season(season_id)


def create_app():
    app = Flask(__name__)

    @app.route('/<path>')
    def statics(path):
        return send_from_directory('static', path)

    @app.route('/season/<int:season_id>')
    def season(season_id):
        if season_id != get_last_season_number():
            # previous season is probably cached
            stat_details, score_table = get_or_create_stats_from_previous_season(season_id)
        else:
            season_logs_path = LOGS_PATH  # latest season logs go to main logs dir
            stat_details, score_table = get_stats_for_season(season_logs_path)
        response = make_response(render_template('layout.html', stat_details=stat_details, score_table=score_table))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response

    @app.route('/')
    def root():
        last_season_id = get_last_season_number()
        return redirect(url_for('season', season_id=last_season_id))

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()
    app.run()
