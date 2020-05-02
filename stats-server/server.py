import logging
import subprocess

from flask import Flask, send_file, send_from_directory


def update_table():
    logging.debug("Regenerating table")
    with open("stats.html", 'w') as output:
        subprocess.call(["./read-csdata.pl", "csstats.dat"], stdout=output)


def create_app():
    app = Flask(__name__)

    @app.route('/stats.html')
    def stats():
        update_table()
        response = send_file('stats.html', cache_timeout=0)
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
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()
    app.run()
