from gpapi.googleplay import GooglePlayAPI, LoginError, RequestError
from google.protobuf.message import DecodeError
from pyaxmlparser import APK

import configparser
import urllib.request
from urllib.error import URLError
from subprocess import Popen, PIPE
import os
import sys


def get_token(config):
    print('Retrieving token from %s' % config['tokenurl'])
    r = urllib.request.urlopen(config['tokenurl'])
    token = r.read().decode('utf-8')
    return token


def file_size(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0


class Play(object):
    def __init__(self):
        self.currentSet = list()

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
        self.config = dict()
        for key, value in self.configparser.items('Main'):
            self.config[key] = value

        # configuring download folder
        self.download_path = os.path.join(os.getcwd(), 'repo')

        # configuring fdroid data
        self.fdroid_exe = '/usr/bin/fdroid'
        self.fdroid_path = os.getcwd()
        self.fdroid_init()

        # no need of creating dir, fdroid will take care
        #if not os.path.isdir(self.config['download_path']):
        #    os.mkdir(self.config['download_path'])
        self.service = GooglePlayAPI(self.config['id'], 'en', True)
        self.login()


    def fdroid_init(self):
        if not os.path.isfile(self.fdroid_exe):
            raise OSError('Please install fdroid from repo')
            sys.exit(1)
        else:
            p = Popen([self.fdroid_exe, 'init'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                sys.stderr.write("error while initializing fdroid repository " + stderr.decode('utf-8'))
                sys.exit(1)
            else:
                print('Fdroid repo initialized successfully')


    def fdroid_update(self):
        try:
            p = Popen([self.fdroid_exe, 'update', '-c', '--clean'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                sys.stderr.write("error while updating fdroid repository " + stderr.decode('utf-8'))
                return False
            else:
                print('Fdroid repo updated successfully')
                return True
        except:
            print(stderr)
            return False


    def fetch_new_token(self):
        token = ""
        for i in range(1, 4):
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
            token = ''
            if self.config['token'] != '':
                token = self.config['token']
            else:
                token = self.fetch_new_token()
            self.service.login(None, None, token)
            self.update_state()
        except URLError:
            print('Failed to fetch url')
            sys.exit(1)
        except LoginError:
            print('Login failed, trying with credentials in playmaker.conf')
            sys.exit(1)


    def fetch_details_for_local_apps(self):
        """
        Return list of details of the currently downloaded apps.
        Details are fetched from the google server. Don't use this
        function to get names of downloaded apps (use get_state() instead)
        """
        # get application ids from apk files
        appList = [os.path.splitext(apk)[0] for apk in os.listdir(self.download_path)
                   if os.path.splitext(apk)[1] == '.apk']
        toReturn = list()
        if len(appList) > 0:
            details = self.get_bulk_details(appList)
            for appdetails in details:
                filepath = os.path.join(self.download_path, appdetails['docId'] + '.apk')
                a = APK(filepath)
                appdetails['version'] = int(a.version_code)
                toReturn.append(appdetails)
        return toReturn


    def update_state(self):
        print('Updating local app state')
        self.currentSet = self.fetch_details_for_local_apps()


    def get_state(self):
        return [app['docId'] for app in self.currentSet]


    def insert_app_into_state(self, newApp):
        found = False
        for pos, app in enumerate(self.currentSet):
            if app['docId'] == newApp['docId']:
                found = True
                print('%s is already in currentState, updating..' % newApp['docId'])
                self.currentSet[pos] = newApp
                break
        if found is False:
            print('Adding %s into currentState..' % newApp['docId'])
            self.currentSet.append(newApp)


    def search(self, appName, numItems=20):
        results = self.service.search(appName, numItems, None).doc
        all_apps = []
        if len(results) > 0:
            results = results[0].child
        else:
            return "[]"
        for result in results:
            if result.offer[0].checkoutFlowRequired:
                continue
            appDetails = result.details.appDetails
            app = {
                'title': result.title,
                'developer': result.creator,
                'version': appDetails.versionCode,
                'size': file_size(appDetails.installationSize),
                'docId': result.docid,
                'numDownloads': appDetails.numDownloads,
                'uploadDate': appDetails.uploadDate,
                'stars': '%.2f' % result.aggregateRating.starRating
            }
            all_apps.append(app)
        return all_apps


    def get_bulk_details(self, apksList):
        try:
            results = self.service.bulkDetails(apksList)
            if len(results.entry) == 0:
                print('Authentication error, try to reset the token')
                sys.exit(1)
        except DecodeError:
            print('Cannot decode data')
            return []
        details = list()
        for pos, apk in enumerate(apksList):
            current = results.entry[pos]
            doc = current.doc
            appDetails = doc.details.appDetails
            if doc.docid != apk:
                raise Error('Wrong order in get_bulk_details')
                sys.exit(1)
            details.append({
               'title': doc.title,
               'developer': doc.creator,
               'size': file_size(appDetails.installationSize),
               'numDownloads': appDetails.numDownloads,
               'uploadDate': appDetails.uploadDate,
               'docId': doc.docid,
               'version': appDetails.versionCode,
               'stars': '%.2f' % doc.aggregateRating.starRating
            })
        return details


    def download_selection(self, appNames):
        success = list()
        failed = list()
        unavail = list()

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
        # Now we should save the new app into the currentSet, we can
        # 1) just fire update_state, (more computation) or
        # 2) add objects in the success list to currentSet (taking care of duplicates)
        for x in success:
            self.insert_app_into_state(x)
        return {
            'success': success,
            'failed': failed,
            'unavail': unavail
        }


    def check_local_apks(self):
        localDetails = self.currentSet
        onlineDetails = self.get_bulk_details(self.get_state())
        if len(localDetails) == 0 or len(onlineDetails) == 0:
            print('There is no package locally')
            return []
        else:
            toUpdate = list()
            for local, online in zip(localDetails, onlineDetails):
                print('Checking %s - %s' % (local['docId'], online['docId']))
                print('%d == %d ?' % (local['version'], online['version']))
                if local['version'] != online['version']:
                    toUpdate.append(online['docId'])
            return toUpdate

    def remove_local_app(self, appName):
        apkName = appName + '.apk'
        apkPath = os.path.join(self.download_path, apkName)
        if os.path.isfile(apkPath):
            os.remove(apkPath)
            for pos, app in enumerate(self.currentSet):
                if app['docId'] == appName:
                    del self.currentSet[pos]
                    print(str(self.currentSet))
            return True
        return False
