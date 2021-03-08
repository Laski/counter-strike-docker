import logging
import subprocess

from flask import Flask, make_response, send_file, send_from_directory

from log_parser.parser import LogDirectoryParser
from log_parser.scorer import GlickoScorer, MatchStatsExtractor


def update_table():
    logging.debug("Regenerating table")
    with open("stats.html", 'w') as output:
        subprocess.call(["./read-csdata.pl", "csstats.dat"], stdout=output)


def parse_logs():
    logging.debug("Parsing logs")
    logs_path = "logs"
    match_reports = LogDirectoryParser(logs_path).get_all_match_reports()
    scorer = GlickoScorer()
    stats = MatchStatsExtractor(match_reports, scorer=scorer)
    score_table = stats.get_sorted_score_table()
    response = ""
    for score in score_table:
        player, glicko = score
        ranking, variance = glicko
        response += f"{player.get_nickname()}: {ranking:.2f} (± {variance*1.96:.2f}"
        response += "<br>"
    return response


def create_app():
    app = Flask(__name__)

    @app.route('/stats.html')
    def stats():
        update_table()
        response = send_file('stats.html', cache_timeout=0)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response

    @app.route('/elo.html')
    def logs():
        response = make_response(parse_logs())
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response

    @app.route('/<path>')
    def statics(path):
        return send_from_directory('static', path)

    @app.route('/')
    def root():
        return app.send_static_file('index.html')

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.run()
