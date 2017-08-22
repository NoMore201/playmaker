#!/usr/bin/env python3

from service import Play
import tornado
from tornado import ioloop as io
from tornado import web
from tornado import httpserver
from tornado.concurrent import run_on_executor
from tornado.web import MissingArgumentError
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

MAX_WORKERS = 4

class HomeHandler(web.RequestHandler):
    def get(self):
        self.render('index.html', title='Playmaker')

class SearchHandler(web.RequestHandler):
    def get(self):
        self.render('search.html', title='Playmaker')


class ApiApksHandler(web.RequestHandler):

    def get(self):
        apps = sorted(service.currentSet, key=lambda k: k['title'])
        apps = json.dumps(apps)
        self.write(apps)
        self.finish()


class ApiSearchHandler(web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @run_on_executor
    def search(self):
        try:
            keyword = self.get_argument('search')
        except MissingArgumentError:
            return None
        return json.dumps(service.search(self.get_argument('search')))

    @tornado.gen.coroutine
    def get(self):
        apps = yield self.search()
        if apps is not None:
            self.write(apps)
            self.finish()
        else:
            self.clear()
            self.set_status(400)
            self.finish()


class ApiDownloadHandler(web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    @run_on_executor
    def download(self):
        data = tornado.escape.json_decode(self.request.body)
        if data.get('download') is None:
            return None
        apps = service.download_selection(data['download'])
        return json.dumps(apps)

    @tornado.gen.coroutine
    def post(self):
        result = yield self.download()
        if result is None:
            self.clear()
            self.set_status(400)
            self.finish()
        else:
            self.write(result)
            self.finish()

class ApiCheckHandler(web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=1)

    @run_on_executor
    def check(self):
        apps = service.check_local_apks()
        return json.dumps(apps)

    @tornado.gen.coroutine
    def post(self):
        result = yield self.check()
        self.write(result)
        self.finish()


class ApiDeleteHandler(web.RequestHandler):

    def delete(self):
        data = tornado.escape.json_decode(self.request.body)
        if data.get('delete') is None:
            self.clear()
            self.set_status(400)
            self.finish()
        else:
            result = service.remove_local_app(data['delete'])
            if result:
                self.write('OK')
                self.finish()
            else:
                self.clear()
                self.set_status(500)
                self.finish()

singleton = {}

class ApiFdroidHandler(web.RequestHandler):
    executor = ThreadPoolExecutor(max_workers=1)

    @run_on_executor
    def update(self):
        return service.fdroid_update()

    @tornado.gen.coroutine
    def post(self):
        global singleton
        if singleton != {}:
            self.write('PENDING')
            self.finish()
            return
        singleton = self
        result = yield self.update()
        if result:
            self.write('OK')
            self.finish()
            singleton = {}
        else:
            self.clear()
            self.set_status(500)
            self.finish()
            singleton = {}


app_dir = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(app_dir, 'templates')
static_dir = os.path.join(app_dir, 'static')

app = web.Application([
    (r'/', HomeHandler),
    (r'/search', SearchHandler),
    (r'/api/apks', ApiApksHandler),
    (r'/api/search', ApiSearchHandler),
    (r'/api/download', ApiDownloadHandler),
    (r'/api/check', ApiCheckHandler),
    (r'/api/delete', ApiDeleteHandler),
    (r'/api/fdroid', ApiFdroidHandler),
    (r'/static/(.*)', web.StaticFileHandler, {'path': static_dir}),
], debug=True)

# overwrite settings
app.settings['template_path'] = template_dir
app.settings['static_path'] = ''

if __name__ == '__main__':
    server = httpserver.HTTPServer(app)
    server.listen(5000)
    io.IOLoop.instance().start()
