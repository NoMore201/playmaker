from gpapi.googleplay import GooglePlayAPI, LoginError, RequestError
from pyaxmlparser import APK
from subprocess import Popen, PIPE

import base64
import os
import sys
from datetime import datetime as dt

NOT_LOGGED_IN_ERR = 'Not logged in'
WRONG_CREDENTIALS_ERR = 'Wrong credentials'
SESSION_EXPIRED_ERR = 'Session tokens expired, re-login needed'
FDROID_ERR = 'Error while executing fdroidserver tool'


def makeError(message):
    return {'status': 'ERROR',
            'message': message}


class Play(object):
    def __init__(self, debug=True, fdroid=False):
        self.currentSet = []
        self.debug = debug
        self.fdroid = fdroid
        self.firstRun = True
        self.loggedIn = False
        self._email = None
        self._passwd = None
        self._last_fdroid_update = None

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
        for path in os.environ['PATH'].split(':'):
            exe = os.path.join(path, self.fdroid_exe)
            if os.path.isfile(exe):
                found = True
                break
        if not found:
            print('Please install fdroid')
            sys.exit(1)
        elif os.path.isfile('./config.py'):
            print('Repo already initalized, skipping')
        else:
            p = Popen([self.fdroid_exe, 'init', '-v'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                sys.stderr.write("error initializing fdroid repository " +
                                 stderr.decode('utf-8'))
                sys.exit(1)
        # ensure all folder and files are setup
        p = Popen([self.fdroid_exe, 'update', '--create-key', '-v'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            sys.stderr.write("error initializing fdroid repository " +
                             stderr.decode('utf-8'))
        else:
            print('Fdroid repo initialized successfully')

    def get_last_fdroid_update(self):
        return {'status': 'SUCCESS',
                'message': str(self._last_fdroid_update)}

    def fdroid_update(self):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
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
                    self._last_fdroid_update = dt.today().replace(microsecond=0)
                    return {'status': 'SUCCESS'}
            except Exception as e:
                return makeError(FDROID_ERR)
        else:
            return {'status': 'SUCCESS'}

    def get_apps(self):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        if self.firstRun:
            return {'status': 'PENDING'}
        return {'status': 'SUCCESS',
                'message': sorted(self.currentSet, key=lambda k: k['title'])}

    def login(self, email=None, password=None):
        def unpad(s):
            return s[:-ord(s[len(s)-1:])]

        try:
            if email is not None and password is not None:
                self._email = base64.b64decode(email).decode('utf-8')
                self._passwd = base64.b64decode(password).decode('utf-8')
                self.service.login(self._email,
                                   self._passwd,
                                   None, None)
                self.loggedIn = True
            else:
                # otherwise we need only to refresh auth token
                encrypted = self.service.encrypt_password(self._email,
                                                          self._passwd).decode('utf-8')
                self.service.getAuthSubToken(self._email,
                                             encrypted)
                self.loggedIn = True
            return {'status': 'SUCCESS', 'message': 'OK'}
        except LoginError as e:
            print('Wrong credentials: {0}'.format(e))
            return {'status': 'ERROR',
                    'message': 'Wrong credentials'}
        except RequestError as e:
            # probably tokens are invalid, so it is better to
            # invalidate them
            print(e)
            return {'status': 'ERROR',
                    'message': 'Request error, probably invalid token'}

    def _get_details_from_apk(self, details):
        filepath = os.path.join(self.download_path,
                                details['docId'] + '.apk')
        a = APK(filepath)
        details['versionCode'] = int(a.version_code)
        return details

    def _fetch_details_for_local_apps(self):
        # get application ids from apk files
        appList = [os.path.splitext(apk)[0]
                   for apk in os.listdir(self.download_path)
                   if os.path.splitext(apk)[1] == '.apk']
        toReturn = []
        if len(appList) > 0:
            details = self.get_bulk_details(appList)
            for app in details:
                local_app = self._get_details_from_apk(app)
                toReturn.append(local_app)
                if self.debug:
                    print('Added %s to cache' % app['docId'])
        return toReturn

    def update_state(self):
        print('Updating cache')
        self.currentSet = self._fetch_details_for_local_apps()
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
            return {'status': 'UNAUTHORIZED'}
        try:
            apps = self.service.search(appName, numItems, None)
        except RequestError as e:
            print(e)
            self.loggedIn = False
            return {'status': 'ERROR',
                    'message': SESSION_EXPIRED_ERR}
        except LoginError as e:
            print(SESSION_EXPIRED_ERR)
            self.login()
            return self.search(appName, numItems)
        except IndexError as e:
            print(SESSION_EXPIRED_ERR)
            self.login()
            return self.search(appName, numItems)

        return {'status': 'SUCCESS',
                'message': apps}

    def get_bulk_details(self, apksList):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        try:
            apps = self.service.bulkDetails(apksList)
            if any([a['versionCode'] == 0 for a in apps]):
                self.login()
                apps = self.service.bulkDetails(apksList)
        except RequestError as e:
            print(e)
            return {'status': 'ERROR',
                    'message': SESSION_EXPIRED_ERR}
        return apps

    def download_selection(self, appNames):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
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
                    open(filepath, 'wb').write(data['data'])
                except IOError as exc:
                    print('Error while writing %s: %s' % (filename, exc))
                    failed.append(appname)
                success.append(appdetails)
        for x in success:
            self.insert_app_into_state(x)
        return {'status': 'SUCCESS',
                'message': {'success': success,
                            'failed': failed,
                            'unavail': unavail}}

    def check_local_apks(self):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        localDetails = self.currentSet
        onlineDetails = self.get_bulk_details([app['docId'] for app in localDetails])
        if len(localDetails) == 0 or len(onlineDetails) == 0:
            print('There is no package locally')
            return {'status': 'SUCCESS',
                    'message': []}
        else:
            toUpdate = []
            for local, online in zip(localDetails, onlineDetails):
                if self.debug:
                    print('Checking %s' % local['docId'])
                    print('%d == %d ?' % (local['versionCode'], online['versionCode']))
                if local['versionCode'] != online['versionCode']:
                    toUpdate.append(online['docId'])
        return {'status': 'SUCCESS',
                'message': toUpdate}

    def remove_local_app(self, appName):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        apkName = appName + '.apk'
        apkPath = os.path.join(self.download_path, apkName)
        if os.path.isfile(apkPath):
            os.remove(apkPath)
            for pos, app in enumerate(self.currentSet):
                if app['docId'] == appName:
                    del self.currentSet[pos]
            return {'status': 'SUCCESS'}
        return {'status': 'ERROR'}
