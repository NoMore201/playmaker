from googleplay_api.googleplay import GooglePlayAPI, LoginError, RequestError
from google.protobuf.message import DecodeError
from pyaxmlparser import APK

import configparser
import urllib.request
from urllib.error import URLError
import os
import sys


def get_token(config):
    print('Retrieving token from %s' % config['tokenurl'])
    r = urllib.request.urlopen(config['tokenurl'])
    token = r.read().decode('utf-8')
    config['token'] = token
    return token


class Play(object):
    def __init__(self):
        self.currentSet = list()
        self.configparser = configparser.ConfigParser()
        config_paths = [
            '/etc/playmaker.conf',
            os.path.expanduser('~') + '/.config/playmaker.conf',
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
        self.login()


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


    def login(self):
        try:
            token = self.fetch_new_token()
            self.service.login(None, None, token)
            self.update_state()
        except URLError:
            print('Failed to fetch url, try again in a few minutes')
            sys.exit(1)
        except LoginError:
            print('Login failed')
            sys.exit(1)


    #
    # HELPERS
    #

    def set_download_folder(self, folder):
        self.config['download_path'] = folder


    def file_size(self, num):
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f%s" % (num, x)
            num /= 1024.0


    def get_local_apks(self):
        """
        Return apk files found in download_path
        """
        downloadPath = self.config['download_path']
        return [apk for apk in os.listdir(downloadPath)
                    if os.path.splitext(apk)[1] == '.apk']


    def get_local_apps(self):
        """
        Returns a list of package names currently
        downloaded (that is file name without '.apk')
        """
        downloadPath = self.config['download_path']
        return [os.path.splitext(apk)[0] for apk in os.listdir(downloadPath)
                if os.path.splitext(apk)[1] == '.apk']


    def fetch_details_for_local_apps(self):
        """
        Return list of details of the currently downloaded apps.
        Details are fetched from the google server. Don't use this
        function to get names of downloaded apps (use get_local_apps instead)
        """
        downloadPath = self.config['download_path']
        appList = self.get_local_apps()
        details = self.get_bulk_details(appList)
        toReturn = list()
        if len(appList) > 0:
            for appName, appDetails in zip(appList, details):
                filepath = os.path.join(downloadPath, appName + '.apk')
                a = APK(filepath)
                appDetails['version'] = int(a.version_code)
                toReturn.append(appDetails)
        return toReturn

    def update_state(self):
        print('Updating local app state')
        self.currentSet = self.fetch_details_for_local_apps()

    def insert_app_into_state(self, newApp):
        found = False
        for pos, app in enumerate(self.currentSet):
            if app['docId'] == newApp['docId']:
                found = True
                self.currentSet[pos] = newApp
                break
        if found is False:
            self.currentSet.append(newApp)


    #
    # MAIN SERVER FUNCTIONS
    #

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
                'size': self.file_size(appDetails.installationSize),
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
        except DecodeError:
            print('Cannot decode data')
            return []
        details = list()
        for pos, apk in enumerate(apksList):
            current = results.entry[pos]
            doc = current.doc
            appDetails = doc.details.appDetails
            details.append({
               'title': doc.title,
               'developer': doc.creator,
               'size': self.file_size(appDetails.installationSize),
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

        downloadPath = self.config['download_path']
        if not os.path.isdir(downloadPath):
            os.mkdir(downloadPath)
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
                filepath = os.path.join(downloadPath, filename)
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
        downloadPath = self.config['download_path']
        localDetails = self.currentSet
        onlineDetails = self.get_bulk_details(self.get_local_apps())
        if len(localDetails) == 0 or len(onlineDetails) == 0:
            print('There is no package locally')
            return []
        else:
            toUpdate = list()
            for local, online in zip(localDetails, onlineDetails):
                print('Checking %s' % online['docId'])
                if local['version'] != online['version']:
                    toUpdate.append(online['docId'])
            return toUpdate

    def remove_local_app(self, appName):
        apkName = appName + '.apk'
        downloadPath = self.config['download_path']
        apkPath = os.path.join(downloadPath, apkName)
        if os.path.isfile(apkPath):
            os.remove(apkPath)
            for pos, app in enumerate(self.currentSet):
                if app['docId'] == appName:
                    del self.currentSet[pos]
            return True
        return False
