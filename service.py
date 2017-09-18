from gpapi.googleplay import GooglePlayAPI, LoginError, RequestError
from pyaxmlparser import APK

import concurrent.futures
import configparser
import urllib.request
from subprocess import Popen, PIPE
import os
import sys
import itertools


def file_size(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0


class Play(object):
    def __init__(self, debug=True, fdroid=False):
        self.currentSet = []
        self.debug = debug
        self.fdroid = fdroid

        # config parser
        self.configparser = configparser.ConfigParser()
        config_paths = [
            'playmaker.conf',
            '/etc/playmaker.conf',
            os.path.expanduser('~') + '/.config/playmaker.conf'
        ]
        while not os.path.isfile(config_paths[0]):
            config_paths.pop(0)
            if len(config_paths) == 0:
                raise OSError('No configuration file found')
                sys.exit(1)
        self.configfile = config_paths[0]
        self.configparser.read(config_paths[0])
        self.config = {}
        for key, value in self.configparser.items('Main'):
            self.config[key] = value

        # configuring download folder
        if self.fdroid:
            self.download_path = os.path.join(os.getcwd(), 'repo')
        else:
            self.download_path = os.getcwd()

        # configuring fdroid data
        if self.fdroid:
            self.fdroid_exe = 'fdroid'
            self.fdroid_path = os.getcwd()
            self.fdroid_init()

        self.service = GooglePlayAPI(self.debug)
        self.login()

    def fdroid_init(self):
        found = False
        for path in ['/usr/bin', '/usr/local/bin']:
            exe = os.path.join(path, self.fdroid_exe)
            if os.path.isfile(exe):
                found = True
        if not found:
            print('Please install fdroid')
            sys.exit(1)
        elif os.path.isdir('./repo'):
            print('Repo already initalized, skipping')
        else:
            p = Popen([self.fdroid_exe, 'init'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                sys.stderr.write("error initializing fdroid repository " +
                                 stderr.decode('utf-8'))
                sys.exit(1)
            else:
                print('Fdroid repo initialized successfully')

    def fdroid_update(self):
        if self.fdroid:
            try:
                p = Popen([self.fdroid_exe, 'update', '-c', '--clean'],
                          stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    sys.stderr.write("error updating fdroid repository " +
                                     stderr.decode('utf-8'))
                    return False
                else:
                    print('Fdroid repo updated successfully')
                    return True
            except:
                return False
        else:
            return True

    def get_apps(self):
        return {
            'result': sorted(self.currentSet, key=lambda k: k['title'])
        }

    def fetch_new_token(self):

        def get_token(config):
            print('Retrieving token from %s' % config['tokenurl'])
            r = urllib.request.urlopen(config['tokenurl'])
            token = r.read().decode('utf-8')
            return token

        token = ""
        for i in range(1, 4):
            if self.debug:
                print('#%d try' % i)
            token = get_token(self.config)
            if token == "":
                continue
            else:
                break
        if token == "":
            raise LoginError()
            sys.exit(1)
        return token

    def save_config(self):
        with open(self.configfile, 'w') as configfile:
            self.configparser['Main'] = self.config
            self.configparser.write(configfile)

    def login(self):
        try:
            if self.config['ac2dmtoken'] != '' and self.config['gsfid'] != 0:
                if self.config['authtoken'] == '':
                    self.service.login(self.config['email'],
                                       self.config['password'],
                                       self.config['ac2dmtoken'],
                                       int(self.config['gsfid']))
                else:
                    # we have all information we need, update the state of
                    # self.service and skip login
                    self.service.authSubToken = self.config['authtoken']
                    self.service.ac2dmToken = self.config['ac2dmtoken']
                    self.service.gsfId = int(self.config['gsfid'])
            else:
                self.service.login(self.config['email'],
                                   self.config['password'],
                                   None, None)
        except LoginError as e:
            print(e)
            sys.exit(1)
        except RequestError as e:
            # probably tokens are invalid, so it is better to
            # invalidate them
            print(e)
            self.config['ac2dmtoken'] = ''
            self.config['authtoken'] = ''
            self.config['gsfid'] = 0
            self.save_config()
            # try another login
            self.login()

        self.config['ac2dmtoken'] = self.service.ac2dmToken
        self.config['gsfid'] = self.service.gsfId
        self.config['authtoken'] = self.service.authSubToken
        self.save_config()
        self.update_state()

    def update_state(self):

        def get_details_from_apk(details):
            filepath = os.path.join(self.download_path,
                                    details['docId'] + '.apk')
            a = APK(filepath)
            details['versionCode'] = int(a.version_code)
            return details

        def fetch_details_for_local_apps():

            # get application ids from apk files
            appList = [os.path.splitext(apk)[0]
                       for apk in os.listdir(self.download_path)
                       if os.path.splitext(apk)[1] == '.apk']
            toReturn = []
            if len(appList) > 0:
                details = self.get_bulk_details(appList)
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
                futures = {executor.submit(get_details_from_apk, app):
                           app for app in details}
                for future in concurrent.futures.as_completed(futures):
                    app = future.result()
                    toReturn.append(app)
                    if self.debug:
                        print('Added %s to cache' % app['docId'])
            return toReturn

        print('Updating cache')
        self.currentSet = fetch_details_for_local_apps()

    def get_apps_from_state(self):
        return [app['docId'] for app in self.currentSet]

    def insert_app_into_state(self, newApp):
        found = False
        result = filter(lambda x: x['docId'] == newApp['docId'],
                        self.currentSet)
        result = list(result)
        if len(result) > 0:
            found = True
            if self.debug:
                print('%s is already cached, updating..' % newApp['docId'])
                i = self.currentSet.index(result[0])
                self.currentSet[i] = newApp
        if not found:
            if self.debug:
                print('Adding %s into cache..' % newApp['docId'])
            self.currentSet.append(newApp)

    def search(self, appName, numItems=15):
        try:
            apps = self.service.search(appName, numItems, None)
        except Exception as e:
            print(e)
            return []
        return {
            'result': apps
        }

    def get_bulk_details(self, apksList):
        try:
            apps = self.service.bulkDetails(apksList)
        except Exception as e:
            print(e)
        return apps

    def download_selection(self, appNames):
        success = []
        failed = []
        unavail = []

        details = self.get_bulk_details(appNames)

        for appname, appdetails in zip(appNames, details):
            if appdetails['docId'] == '':
                print('Package does not exits')
                unavail.append(appname)
                continue
            print('Downloading %s' % appname)
            try:
                data = self.service.download(appname, appdetails['versionCode'])
                success.append(appdetails)
                print('Done!')
            except IndexError as exc:
                print('Package %s does not exists' % appname)
                unavail.append(appname)
            except Exception as exc:
                print('Failed to download %s' % appname)
                failed.append(appname)
            else:
                filename = appname + '.apk'
                filepath = os.path.join(self.download_path, filename)
                try:
                    open(filepath, 'wb').write(data)
                except IOError as exc:
                    print('Error while writing %s: %s' % (filename, exc))
                    failed.append(appname)
        for x in success:
            self.insert_app_into_state(x)
        return {
            'success': success,
            'failed': failed,
            'unavail': unavail
        }

    def check_local_apks(self):
        localDetails = self.currentSet
        onlineDetails = self.get_bulk_details(self.get_apps_from_state())
        if len(localDetails) == 0 or len(onlineDetails) == 0:
            print('There is no package locally')
            return {
                'result': []
            }
        else:
            toUpdate = list()
            for local, online in zip(localDetails, onlineDetails):
                if self.debug:
                    print('Checking %s' % local['docId'])
                    print('%d == %d ?' % (local['versionCode'], online['versionCode']))
                if local['version'] != online['version']:
                    toUpdate.append(online['docId'])
            return {
                'result': toUpdate
            }

    def remove_local_app(self, appName):
        apkName = appName + '.apk'
        apkPath = os.path.join(self.download_path, apkName)
        if os.path.isfile(apkPath):
            os.remove(apkPath)
            for pos, app in enumerate(self.currentSet):
                if app['docId'] == appName:
                    del self.currentSet[pos]
            return True
        return False
