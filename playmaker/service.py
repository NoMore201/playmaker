from gpapi.googleplay import GooglePlayAPI, LoginError, RequestError
from pyaxmlparser import APK
from subprocess import Popen, PIPE
from Crypto.Cipher import AES

import concurrent.futures
import base64
import os
import sys

NOT_LOGGED_IN_ERR = 'Not logged in'
WRONG_CREDENTIALS_ERR = 'Wrong credentials'
SESSION_EXPIRED_ERR = 'Session tokens expired, re-login needed'
FDROID_ERR = 'Error while executing fdroidserver tool'

def makeError(message):
    return { 'status': 'ERROR',
             'message': message }

class Play(object):
    def __init__(self, debug=True, fdroid=False):
        self.currentSet = []
        self.debug = debug
        self.fdroid = fdroid
        self.loggedIn = False
        self.firstRun = True

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
        elif os.path.isfile('./config.py'):
            print('Repo already initalized, skipping')
        else:
            p = Popen([self.fdroid_exe, 'init'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                sys.stderr.write("error initializing fdroid repository " +
                                 stderr.decode('utf-8'))
                sys.exit(1)
        # ensure all folder and files are setup
        p = Popen([self.fdroid_exe, 'update', '--create-key'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            sys.stderr.write("error initializing fdroid repository " +
                             stderr.decode('utf-8'))
        else:
            print('Fdroid repo initialized successfully')

    def fdroid_update(self):
        if not self.loggedIn:
            return makeError(NOT_LOGGED_IN_ERR)
        if self.fdroid:
            try:
                p = Popen([self.fdroid_exe, 'update', '-c', '--clean'],
                          stdout=PIPE, stderr=PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    sys.stderr.write("error updating fdroid repository " +
                                     stderr.decode('utf-8'))
                    return makeError(FDROID_ERR)
                else:
                    print('Fdroid repo updated successfully')
                    return { 'status': 'SUCCESS' }
            except:
                return makeError(FDROID_ERR)
        else:
            return { 'status': 'SUCCESS' }

    def get_apps(self):
        if self.firstRun:
            return { 'status': 'PENDING' }
        return { 'status': 'SUCCESS',
                 'message': sorted(self.currentSet, key=lambda k: k['title']) }

    def login(self, ciphertext, hashToB64):
        def unpad(s):
            return s[:-ord(s[len(s)-1:])]

        try:
            cipher = base64.b64decode(ciphertext)
            passwd = base64.b64decode(hashToB64)
            # first 16 bytes corresponds to the init vector
            iv = cipher[0:16]
            cipher = cipher[16:]
            aes = AES.new(passwd, AES.MODE_CBC, iv)
            result = unpad(aes.decrypt(cipher)).split(b'\x00')
            email = result[0].decode('utf-8')
            password = result[1].decode('utf-8')
            self.service.login(email,
                               password,
                               None, None)
            self.loggedIn = True
            return { 'status': 'SUCCESS', 'message': 'OK' }
        except LoginError as e:
            print('Wrong credentials')
            self.loggedIn = False
            return { 'status': 'ERROR',
                     'message': 'Wrong credentials' }
        except RequestError as e:
            # probably tokens are invalid, so it is better to
            # invalidate them
            print('Request error, probably invalid token')
            self.loggedIn = False
            return { 'status': 'ERROR',
                     'message': 'Request error, probably invalid token' }

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
        self.firstRun = False

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
        if not self.loggedIn:
            return { 'status': 'ERROR',
                     'message': NOT_LOGGED_IN_ERR }

        try:
            apps = self.service.search(appName, numItems, None)
        except RequestError as e:
            print(SESSION_EXPIRED_ERR)
            self.loggedIn = False
            return { 'status': 'ERROR',
                     'message': SESSION_EXPIRED_ERR }
        except IndexError as e:
            print(SESSION_EXPIRED_ERR)
            self.loggedIn = False
            return { 'status': 'ERROR',
                     'message': SESSION_EXPIRED_ERR }

        return { 'status': 'SUCCESS',
                 'message': apps }

    def get_bulk_details(self, apksList):
        if not self.loggedIn:
            return { 'status': 'ERROR',
                     'message': NOT_LOGGED_IN_ERR }
        try:
            apps = self.service.bulkDetails(apksList)
        except RequestError as e:
            print(SESSION_EXPIRED_ERR)
            self.loggedIn = False
            return { 'status': 'ERROR',
                     'message': SESSION_EXPIRED_ERR }
        return apps

    def download_selection(self, appNames):
        if not self.loggedIn:
            return { 'status': 'ERROR',
                     'error': NOT_LOGGED_IN_ERR }

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
                if appdetails['offer'][0]['formattedAmount'] == 'Free':
                    data = self.service.download(appname, appdetails['versionCode'])
                else:
                    data = self.service.delivery(appname, appdetails['versionCode'])
                success.append(appdetails)
                print('Done!')
            except IndexError as exc:
                print(exc)
                print('Package %s does not exists' % appname)
                unavail.append(appname)
            except Exception as exc:
                print(exc)
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
        return { 'status': 'SUCCESS',
                 'message': { 'success': success,
                              'failed': failed,
                              'unavail': unavail } }

    def check_local_apks(self):
        if not self.loggedIn:
            return { 'status': 'ERROR',
                     'error': NOT_LOGGED_IN_ERR }

        localDetails = self.currentSet
        onlineDetails = self.get_bulk_details([app['docId'] for app in localDetails])
        if len(localDetails) == 0 or len(onlineDetails) == 0:
            print('There is no package locally')
            return { 'status': 'SUCCESS',
                     'message': [] }
        else:
            toUpdate = []
            for local, online in zip(localDetails, onlineDetails):
                if self.debug:
                    print('Checking %s' % local['docId'])
                    print('%d == %d ?' % (local['versionCode'], online['versionCode']))
                if local['versionCode'] != online['versionCode']:
                    toUpdate.append(online['docId'])
        return { 'status': 'SUCCESS',
                 'message': toUpdate }

    def remove_local_app(self, appName):
        apkName = appName + '.apk'
        apkPath = os.path.join(self.download_path, apkName)
        if os.path.isfile(apkPath):
            os.remove(apkPath)
            for pos, app in enumerate(self.currentSet):
                if app['docId'] == appName:
                    del self.currentSet[pos]
            return { 'status': 'SUCCESS' }
        return { 'status': 'ERROR' }
