from gpapi.googleplay import GooglePlayAPI, LoginError, RequestError
from pyaxmlparser import APK
from subprocess import Popen, PIPE
from Crypto.Cipher import AES

import concurrent.futures
import base64
import os
import sys

class Play(object):
    def __init__(self, debug=True, fdroid=False):
        self.currentSet = []
        self.debug = debug
        self.fdroid = fdroid

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

    def login(self, encodedMsg, encodedHash):
        def unpad(s):
            return s[:-ord(s[len(s)-1:])]

        try:
            cipher = base64.b64decode(encodedMsg)
            passwd = base64.b64decode(encodedHash)
            iv = cipher[0:16]
            cipher = cipher[16:32]
            aes = AES.new(passwd, AES.MODE_CBC, iv)
            result = unpad(aes.decrypt(cipher)).split(b'\x00')
            print(result)
            quit()
            email = result[0].decode('utf-8')
            password = result[1].decode('utf-8')
            self.service.login(email,
                               password,
                               None, None)
            self.update_state()
            return 0
        except LoginError as e:
            print('Wrong credentials')
            return 1
        except RequestError as e:
            # probably tokens are invalid, so it is better to
            # invalidate them
            print('Internal error')
            self.invalidate_login()
            return 1

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
        # numItems will be ignored by googleplay-api
        # because needs to be implemented
        try:
            apps = self.service.search(appName, numItems, None)
        except RequestError as e:
            print(e)
            self.invalidate_login()
            sys.exit(1)
        return {
            'result': apps
        }

    def get_bulk_details(self, apksList):
        try:
            apps = self.service.bulkDetails(apksList)
        except RequestError as e:
            print(e)
            self.invalidate_login()
            sys.exit(1)
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
        onlineDetails = self.get_bulk_details([app['docId'] for app in localDetails])
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
                if local['versionCode'] != online['versionCode']:
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
