from gpapi.googleplay import GooglePlayAPI, LoginError
from google.protobuf.message import DecodeError
from pyaxmlparser import APK

import concurrent.futures
import configparser
import urllib.request
from urllib.error import URLError
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
            self.fdroid_exe = '/usr/bin/fdroid'
            self.fdroid_path = os.getcwd()
            self.fdroid_init()

        self.service = GooglePlayAPI(self.config['id'], 'en', self.debug)
        self.login()

    def fdroid_init(self):
        if not os.path.isfile(self.fdroid_exe):
            print('Please install fdroid from repo')
            sys.exit(1)
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
        print(self.config['token'])
        try:
            token = ''
            if self.config['token'] != '':
                token = self.config['token']
                if self.debug:
                    print('Reusing saved token')
            else:
                if self.debug:
                    print('Fetching new token')
                token = self.fetch_new_token()
            self.service.login(None, None, token)
            self.config['token'] = token
            self.save_config()
            self.update_state()
        except URLError:
            print('Failed to fetch url')
            sys.exit(1)
        except LoginError:
            print('Login failed, resetting the token')
            self.config['token'] = ''
            self.save_config()
            sys.exit(1)
        except DecodeError:
            print('Invalid token')
            self.config['token'] = ''
            self.save_config()
            self.login()

    def update_state(self):

        def get_details_from_apk(details):
            filepath = os.path.join(self.download_path,
                                    details['docId'] + '.apk')
            a = APK(filepath)
            details['version'] = int(a.version_code)
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
        results = self.service.search(appName, numItems, None).doc
        all_apps = []
        if len(results) < 1:
            return {
                'result': []
            }
        # takes an array of iterables and joins all the elements in
        # a single iterable
        apps = itertools.chain.from_iterable([doc.child for doc in results])
        for x in apps:
            if x.offer[0].checkoutFlowRequired:
                continue
            details = x.details.appDetails
            app = {
                'title': x.title,
                'developer': x.creator,
                'version': details.versionCode,
                'size': file_size(details.installationSize),
                'docId': x.docid,
                'numDownloads': details.numDownloads,
                'uploadDate': details.uploadDate,
                'stars': '%.2f' % x.aggregateRating.starRating
            }
            if len(all_apps) <= numItems:
                all_apps.append(app)
            else:
                break
        return {
            'result': all_apps
        }

    def get_bulk_details(self, apksList):
        results = self.service.bulkDetails(apksList)
        if len(results.entry) == 0:
            return []

        def from_entry_to_dict(e):
            doc = e.doc
            details = doc.details.appDetails
            title = doc.title
            if len(title) > 40:
                title = title[0:36] + '...'
            return {
                'title': title,
                'developer': doc.creator,
                'size': file_size(details.installationSize),
                'numDownloads': details.numDownloads,
                'uploadDate': details.uploadDate,
                'docId': doc.docid,
                'version': details.versionCode,
                'stars': '%.2f' % doc.aggregateRating.starRating
            }

        a = [entry for entry in results.entry]
        result = list(map(from_entry_to_dict, a))
        return result

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
                data = self.service.download(appname, appdetails['version'])
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
                    print('%d == %d ?' % (local['version'], online['version']))
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
