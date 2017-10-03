import os
import tornado

from tornado import web
from tornado.concurrent import run_on_executor
from tornado.web import MissingArgumentError
from concurrent.futures import ThreadPoolExecutor


MAX_WORKERS=4
app_dir = os.path.dirname(os.path.realpath(__file__))
static_dir = os.path.join(app_dir, 'static')
fdroid_instance = {}

def createServer(service):

    class HomeHandler(web.RequestHandler):
        def get(self):
            with open(app_dir + '/index.html', 'r') as f:
                self.write(f.read())


    class ApiHandler(web.RequestHandler):
        executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

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
        def login(self):
            data = tornado.escape.json_decode(self.request.body)
            if len(data) == 0:
                return 'OK' if service.loggedIn else { 'error' : 'Not logged in' }
            res = service.login(data['cyphertext'], data['password'])
            return res

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
            else:
                self.set_status(404)
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
            elif path == 'login':
                result = yield self.login()
                print(result)
                if not isinstance(result, str):
                    self.clear()
                    self.set_status(400)
                self.write(result)
            elif path == 'fdroid':
                global fdroid_instance
                if fdroid_instance != {}:
                    self.write('PENDING')
                else:
                    fdroid_instance = self
                    result = yield self.update_fdroid()
                    if not isinstance(result, str):
                        self.clear()
                        self.set_status(500)
                    self.write(result)
                    fdroid_instance = {}
            else:
                self.set_status(404)
            self.finish()

        @tornado.gen.coroutine
        def delete(self, path):
            if path == 'delete':
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
            else:
                self.set_status(404)
            self.finish()

    app = web.Application([
        (r'/', HomeHandler),
        (r'/api/(.*?)/?', ApiHandler),
        (r'/static/(.*)', web.StaticFileHandler, {'path': static_dir}),
        (r'/views/(.*)', web.StaticFileHandler, {'path': app_dir + '/views'}),
    ], debug=True)

    # overwrite settings
    app.settings['static_path'] = ''
    return app
