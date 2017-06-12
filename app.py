from googleplay_api.googleplay import GooglePlayAPI, LoginError
from google.protobuf.message import DecodeError
from pyaxmlparser import APK

import configparser
import urllib.request
from urllib.error import URLError
import os
import sys
import json


def get_token(config):
    print('Retrieving token from %s' % config['tokenurl'])
    r = urllib.request.urlopen(config['tokenurl'])
    token = r.read().decode('utf-8')
    config['token'] = token
    return token


class Play(object):
    def __init__(self):
        self.configparser = configparser.ConfigParser()
        config_paths = [
            os.path.expanduser('~') + '/.config/playmaker.conf',
            '/etc/playmaker.conf',
            'playmaker.conf'
        ]
        while not os.path.isfile(config_paths[0]):
            config_paths.pop(0)
            if len(config_paths) == 0:
                raise OSError('No configuration file found')
                sys.exit(1)
        self.configparser.read(config_paths[0])
        self.config = dict()
        for key, value in self.configparser.items('Main'):
            self.config[key] = value
        self.set_download_folder('.')
        self.service = GooglePlayAPI(self.config['id'], 'en_US', True)
        if self.config['token'] == '':
            try:
                for i in range(1, 4):
                    # TODO: add verbose log
                    print('#%d try' % i)
                    token = get_token(self.config)
                    if token == "":
                        continue
                    else:
                        break
                if token == "":
                    raise LoginError()
                    sys.exit(1)
                self.service.login(None, None, token)
            except URLError:
                print('Failed to fetch url, try again in a few minutes')
                sys.exit(1)
            except LoginError:
                print('Login failed')
                sys.exit(1)
        else:
            try:
                self.service.login(None, None, self.config['token'])
            except LoginError:
                print('Login failed')
                sys.exit(1)

    def search(self, appName, numItems=5):
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
                'size': self.file_size(appDetails.installationSize),
                'docId': result.docid,
                'numDownloads': appDetails.numDownloads,
                'uploadDate': appDetails.uploadDate,
                'stars': '%.2f' % result.aggregateRating.starRating
            }
            all_apps.append(app)
        return json.dumps(all_apps)

    def set_download_folder(self, folder):
        self.config['download_path'] = folder

    def file_size(self, num):
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f%s" % (num, x)
            num /= 1024.0

    def get_bulk_details(self, apksList):
        try:
            results = self.service.bulkDetails(apksList)
        except DecodeError:
            print('Cannot decode data')
            return {}
        details = dict()
        for pos, apk in enumerate(apksList):
            current = results.entry[pos]
            doc = current.doc
            appDetails = doc.details.appDetails
            details[apk] = {
               'title': doc.title,
               'developer': doc.creator,
               'size': self.file_size(appDetails.installationSize),
               'numDownloads': appDetails.numDownloads,
               'uploadDate': appDetails.uploadDate,
               'docId': doc.docid,
               'version': appDetails.versionCode,
               'stars': '%.2f' % doc.aggregateRating.starRating
            }
        return details

    def download_selection(self, apksList):
        success = list()
        failed = list()
        unavail = list()

        downloadPath = self.config['download_path']
        if not os.path.isdir(downloadPath):
            os.mkdir(downloadPath)
        details = self.get_bulk_details(apksList)
        for appname, appdetails in details.items():
            print('Downloading %s' % appname)
            try:
                data = self.service.download(appname, appdetails['version'])
                success.append(appname)
                print('Done!')
            except IndexError as exc:
                print('Package %s does not exists' % appname)
                unavail.append(appname)
            except Exception as exc:
                print('Failed to download %s' % appname)
                failed.append(appname)
            else:
                filename = appname + '.apk'
                filepath = os.path.join(downloadPath, filename)
                try:
                    open(filepath, 'wb').write(data)
                except IOError as exc:
                    print('Error while writing %s: %s' % (filename, exc))
                    failed.append(appname)
        return json.dumps({
            'success': success,
            'failed': failed,
            'unavail': unavail
        })

    def check_local_apks(self):
        downloadPath = self.config['download_path']
        print(os.listdir(downloadPath))
        apksList = [apk for apk in os.listdir(downloadPath)
                    if os.path.splitext(apk)[1] == '.apk']
        if len(apksList) > 0:
            # TODO: add verbose log
            print('Checking local apks..')
            toSearch = list()
            for apk in apksList:
                filepath = os.path.join(downloadPath, apk)
                a = APK(filepath)
                packageName = a.package
                toSearch.append(packageName)
            if len(toSearch) == 0:
                raise Exception('Error retrieving package names from apk')
                sys.exit(1)
            details = self.get_bulk_details(toSearch)
            toUpdate = list()
            for apk in apksList:
                filepath = os.path.join(downloadPath, apk)
                a = APK(filepath)
                localVersion = int(a.version_code)
                packageName = a.package
                onlineVersion = details.get(packageName)['version']
                print('%d == %d ?' % (localVersion, onlineVersion))
                if localVersion != onlineVersion:
                    print('Package %s needs to be updated' % packageName)
                    toUpdate.append(packageName)
                else:
                    print('Package %s is up to date' % packageName)
            return json.dumps(toUpdate)
        else:
            return '[]'
