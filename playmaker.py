#!/usr/bin/env python3

from flask import Flask, render_template, request
from service import Play

import json, os

# application setup
app = Flask(__name__, static_folder='static', template_folder='templates')
service = Play()


@app.route('/')
def render_home():
    return render_template('index.html')


@app.route('/search')
def render_search():
    return render_template('search.html')


@app.route('/api/search', methods=['GET'])
def search_app():
    number = request.args.get('numEntries')
    if number is not None:
        return json.dumps(service.search(request.args.get('search'),
                                         int(number)))
    return json.dumps(service.search(request.args.get('search')))


@app.route('/api/download', methods=['POST'])
def download_app():
    toDownload = service.download_selection(request.json['download'])
    return json.dumps(toDownload)


@app.route('/api/check', methods=['POST'])
def check_local():
    return json.dumps(service.check_local_apks())


@app.route('/api/fdroid', methods=['POST'])
def update_fdroid():
    result = service.fdroid_update()
    if result is True:
        return 'OK'
    else:
        abort(500)


@app.route('/api/apks', methods=['GET'])
def get_apks():
    apps = sorted(service.currentSet, key=lambda k: k['title'])
    return json.dumps(apps)


@app.route('/api/delete', methods=['POST'])
def delete_app():
    res = service.remove_local_app(request.json['delete'])
    if res:
        return 'OK'
    else:
        abort(500)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
