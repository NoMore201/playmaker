#!/usr/bin/env python3

from service import Play
import tornado
from tornado import ioloop as io
from tornado import web
from tornado import httpserver
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import json
import os
import argparse

# arguments
ap = argparse.ArgumentParser(description='Apk and fdroid repository manager with a web interface.')
ap.add_argument('-f', '--fdroid', dest='fdroid', action='store_true', default=False,
                help='Enable fdroid integration')
ap.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
                help='Enable debug output')
args = ap.parse_args()
service = Play(debug=args.debug, fdroid=args.fdroid)

# tornado setup

global_executor = ThreadPoolExecutor(max_workers=4)

class HomeHandler(web.RequestHandler):
    def get(self):
        self.render('index.html', title='Playmaker')

class SearchHandler(web.RequestHandler):
    def get(self):
        self.render('search.html', title='Playmaker')

class ApiApksHandler(web.RequestHandler):
    executor = global_executor

    @run_on_executor
    def get_apps(self):
        apps = sorted(service.currentSet, key=lambda k: k['title'])
        return apps

    @tornado.gen.coroutine
    def get(self):
        apps = yield self.get_apps()
        self.write(json.dumps(apps))
        self.finish()


app = web.Application([
    (r'/', HomeHandler),
    (r'/search', SearchHandler),
    (r'/api/apks', ApiApksHandler),
    (r'/static/(.*)', web.StaticFileHandler, {'path': 'static'}),
], debug=True)
app.settings['template_path'] = './templates'
app.settings['static_path'] = ''
server = httpserver.HTTPServer(app)
server.listen(5000)
io.IOLoop.instance().start()



"""
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
"""
