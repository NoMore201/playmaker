#!/usr/bin/env python3

from service import Play
import tornado
from tornado import ioloop as io
from tornado import web
from tornado import httpserver
from tornado.concurrent import run_on_executor
from tornado.web import MissingArgumentError
from concurrent.futures import ThreadPoolExecutor

import os
import argparse

# arguments parsing
ap = argparse.ArgumentParser(description='Apk and fdroid repository ' +
                             'manager with a web interface.')
ap.add_argument('-f', '--fdroid', dest='fdroid',
                action='store_true', default=False,
                help='Enable fdroid integration')
ap.add_argument('-d', '--debug', dest='debug',
                action='store_true', default=False,
                help='Enable debug output')
args = ap.parse_args()
service = Play(debug=args.debug, fdroid=args.fdroid)

# tornado setup
MAX_WORKERS = 4
app_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(app_dir, 'static')


class HomeHandler(web.RequestHandler):
    def get(self):
        with open(app_dir + '/index.html', 'r') as f:
            self.write(f.read())


class ApiHandler(web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    fdroid_instance = {}

    @run_on_executor
    def get_apps(self):
        return service.get_apps()

    @run_on_executor
    def search(self):
        try:
            keyword = self.get_argument('search')
        except MissingArgumentError:
            return None
        return service.search(keyword)

    @run_on_executor
    def download(self):
        data = tornado.escape.json_decode(self.request.body)
        if data.get('download') is None:
            return None
        apps = service.download_selection(data['download'])
        return apps

    @run_on_executor
    def check(self):
        apps = service.check_local_apks()
        return apps

    @run_on_executor
    def remove_app(self, app):
        return service.remove_local_app(app)

    @run_on_executor
    def update_fdroid(self):
        return service.fdroid_update()

    @tornado.gen.coroutine
    def get(self, path):
        if path == 'apps':
            apps = yield self.get_apps()
            self.write(apps)
        elif path == 'search':
            apps = yield self.search()
            if apps is not None:
                self.write(apps)
            else:
                self.clear()
                self.set_status(400)
        self.finish()

    @tornado.gen.coroutine
    def post(self, path):
        if path == 'download':
            result = yield self.download()
            if result is None:
                self.clear()
                self.set_status(400)
            else:
                self.write(result)
        elif path == 'check':
            result = yield self.check()
            self.write(result)
        elif path == 'fdroid':
            if self.fdroid_instance != {}:
                self.write('PENDING')
            else:
                self.fdroid_instance = self
                result = yield self.update_fdroid()
                if result:
                    self.write('OK')
                    self.fdroid_instance = {}
                else:
                    self.clear()
                    self.set_status(500)
                    self.fdroid_instance = {}
        self.finish()

    @tornado.gen.coroutine
    def delete(self):
        data = tornado.escape.json_decode(self.request.body)
        if data.get('delete') is None:
            self.clear()
            self.set_status(400)
        else:
            result = yield self.remove_app(data['delete'])
            if result:
                self.write('OK')
            else:
                self.set_status(500)
        self.finish()


app = web.Application([
    (r'/', HomeHandler),
    (r'/api/(.*?)/?', ApiHandler),
    (r'/static/(.*)', web.StaticFileHandler, {'path': static_dir}),
    (r'/views/(.*)', web.StaticFileHandler, {'path': app_dir + '/views'}),
], debug=args.debug)

# overwrite settings
app.settings['static_path'] = ''

if __name__ == '__main__':
    server = httpserver.HTTPServer(app)
    server.listen(5000, address='0.0.0.0')
    io.IOLoop.instance().start()
