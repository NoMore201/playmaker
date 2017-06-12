#!/usr/bin/env python3

from flask import Flask, render_template, request
from app import Play

# application setup
app = Flask(__name__)
service = Play()


@app.route('/')
def render_home():
    return render_template('index.html')


@app.route('/search')
def render_search():
    return render_template('search.html')


@app.route('/config')
def render_config():
    return render_template('config.html')


@app.route('/gplay/search', methods=['POST'])
def search_app():
    return service.search(request.json['search'])


@app.route('/gplay/dl', methods=['POST'])
def download_app():
    return service.download_selection(request.json['download'])

    
@app.route('/gplay/check', methods=['POST'])
def check_local():
    return service.check_local_apks()


if __name__ == '__main__':
    app.run()
