from gpapi.googleplay import GooglePlayAPI, LoginError, RequestError, SecurityCheckError
from pyaxmlparser import APK
from subprocess import Popen, PIPE

import base64
import os
import sys
import concurrent.futures
import locale as locale_service
from datetime import datetime as dt

NOT_LOGGED_IN_ERR = 'Not logged in'
WRONG_CREDENTIALS_ERR = 'Wrong credentials'
SESSION_EXPIRED_ERR = 'Session tokens expired, re-login needed'
FDROID_ERR = 'Error while executing fdroidserver tool'


def makeError(message):
    return {'status': 'ERROR',
            'message': message}


def get_details_from_apk(apk, downloadPath, service):
    if apk is not None:
        filepath = os.path.join(downloadPath, apk)
        try:
            a = APK(filepath)
        except Exception as e:
            print(e)
            return None
        print('Fetching details for %s' % a.package)
        try:
            details = service.details(a.package)
            details['filename'] = apk
            details['versionCode'] = int(a.version_code)
        except RequestError as e:
            print('Cannot fetch information for %s' % a.package)
            print('Extracting basic information from package...')
            return {'docid': a.package,
                    'filename': apk,
                    'versionCode': int(a.version_code),
                    'title': a.application}
        print('Added %s to cache' % details['docid'])
    return details


class Play(object):
    def __init__(self, debug=True, fdroid=False):
        self.currentSet = []
        self.totalNumOfApps = 0
        self.debug = debug
        self.fdroid = fdroid
        self.firstRun = True
        self.loggedIn = False
        self._email = None
        self._passwd = None
        self._gsfId = None
        self._token = None
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

        # language settings
        locale = os.environ.get('LANG_LOCALE')
        if locale is None:
            locale = locale_service.getdefaultlocale()[0]
        timezone = os.environ.get('LANG_TIMEZONE')
        if timezone is None:
            timezone = 'Europe/Berlin'
        device = os.environ.get('DEVICE_CODE')
        if device is None:
            self.service = GooglePlayAPI(locale, timezone)
        else:
            self.service = GooglePlayAPI(locale, timezone,
                    device_codename=device)

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
        elif os.path.isfile('config.py'):
            print('Repo already initalized, skipping init')
        else:
            p = Popen([self.fdroid_exe, 'init', '-v'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                sys.stderr.write("error initializing fdroid repository " +
                                 stderr.decode('utf-8'))
                sys.exit(1)
        # backup config.py
        if self.debug:
            print('Checking config.py file')
        with open('config.py', 'r') as config_file:
            content = config_file.readlines()
        with open('config.py', 'w') as config_file:
            # copy all the original content of config.py
            # if the file was not modified with custom values, do it
            modified = False
            for line in content:
                if '# playmaker' in line:
                    modified = True
                config_file.write(line)
            if not modified:
                if self.debug:
                    print('Appending playmaker data to config.py')
                config_file.write('\n# playmaker\nrepo_name = "playmaker"\n'
                                  'repo_description = "repository managed with '
                                  'playmaker https://github.com/NoMore201/playmaker"\n')

        # ensure all folder and files are setup
        p = Popen([self.fdroid_exe, 'update', '--create-key', '-v'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print('Skipping fdroid update')
        else:
            print('Fdroid repo initialized successfully')

    def get_last_fdroid_update(self):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
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
            return {'status': 'PENDING',
                    'total': self.totalNumOfApps,
                    'current': len(self.currentSet)}
        return {'status': 'SUCCESS',
                'message': sorted(self.currentSet, key=lambda k: k['title'])}

    def set_encoded_credentials(self, email, password):
        self._email = base64.b64decode(email).decode('utf-8')
        self._passwd = base64.b64decode(password).decode('utf-8')

    def set_credentials(self, email, password):
        self._email = email
        self._passwd = password

    def set_token_credentials(self, gsfId, token):
        self._gsfId = int(gsfId, 16)
        self._token = token

    def has_credentials(self):
        passwd_credentials = self._email is not None and self._passwd is not None
        token_credentials = self._gsfId is not None and self._token is not None
        return passwd_credentials or token_credentials

    def login(self):
        if self.loggedIn:
            return {'status': 'SUCCESS', 'securityCheck': False, 'message': 'OK'}

        try:
            if not self.has_credentials():
                raise LoginError("missing credentials")
            self.service.login(self._email,
                               self._passwd,
                               self._gsfId,
                               self._token)
            self.loggedIn = True
            return {'status': 'SUCCESS', 'securityCheck': False, 'message': 'OK'}
        except LoginError as e:
            print('LoginError: {0}'.format(e))
            self.loggedIn = False
            return {'status': 'ERROR',
                    'securityCheck': False,
                    'message': 'Wrong credentials'}
        except SecurityCheckError as e:
            print('SecurityCheckError: {0}'.format(e))
            self.loggedIn = False
            return {'status': 'ERROR',
                    'securityCheck': True,
                    'message': 'Need security check'}
        except RequestError as e:
            # probably tokens are invalid, so it is better to
            # invalidate them
            print('RequestError: {0}'.format(e))
            self.loggedIn = False
            return {'status': 'ERROR',
                    'securityCheck': False,
                    'message': 'Request error, probably invalid token'}

    def update_state(self):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}

        print('Updating cache')
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # get application ids from apk files
            apkFiles = [apk for apk in os.listdir(self.download_path)
                        if os.path.splitext(apk)[1] == '.apk']
            self.totalNumOfApps = len(apkFiles)
            if self.totalNumOfApps != 0:
                future_to_app = [executor.submit(get_details_from_apk,
                                                 a,
                                                 self.download_path,
                                                 self.service)
                                 for a in apkFiles]
                for future in concurrent.futures.as_completed(future_to_app):
                    app = future.result()
                    if app is not None:
                        self.currentSet.append(app)
        print('Cache correctly initialized')
        self.firstRun = False

    def insert_app_into_state(self, newApp):
        found = False
        result = list(filter(lambda x: x['docid'] == newApp['docid'],
                             self.currentSet))
        if len(result) > 0:
            found = True
            if self.debug:
                print('%s is already cached, updating..' % newApp['docid'])
                i = self.currentSet.index(result[0])
                self.currentSet[i] = newApp
        if not found:
            if self.debug:
                print('Adding %s into cache..' % newApp['docid'])
            self.currentSet.append(newApp)

    def search(self, appName, numItems=15):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}

        try:
            apps = self.service.search(appName)
        except RequestError as e:
            print(e)
            self.loggedIn = False
            return {'status': 'ERROR',
                    'message': SESSION_EXPIRED_ERR}
        except LoginError as e:
            print(SESSION_EXPIRED_ERR)
            self.loggedIn = False
        except IndexError as e:
            print(SESSION_EXPIRED_ERR)
            self.loggedIn = False

        return {'status': 'SUCCESS',
                'message': apps}

    def details(self, app):
        try:
            details = self.service.details(app)
        except RequestError:
            details = None
        return details

    def get_bulk_details(self, apksList):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        try:
            apps = [self.details(a) for a in apksList]
        except LoginError as e:
            print(e)
            self.loggedIn = False
        return apps

    def download_selection(self, apps):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        success = []
        failed = []
        unavail = []

        for app in apps:
            docid = app.get('docid')
            details = self.details(docid)
            filename = app.get('filename')
            if filename is None:
                filename = details.get('docid') + '.apk'
            if details is None:
                print('Package %s does not exits' % docid)
                unavail.append(docid)
                continue
            print('Downloading %s' % docid)
            try:
                if details.get('offer')[0].get('micros') == 0:
                    data_gen = self.service.download(docid, details.get('details').get('appDetails')['versionCode'])
                else:
                    data_gen = self.service.delivery(docid, details.get('details').get('appDetails')['versionCode'])
                data_gen = data_gen.get('file').get('data')
            except IndexError as exc:
                print(exc)
                print('Package %s does not exists' % docid)
                unavail.append(docid)
            except Exception as exc:
                print(exc)
                print('Failed to download %s' % docid)
                failed.append(docid)
            else:
                filepath = os.path.join(self.download_path, filename)
                try:
                    with open(filepath, 'wb') as apk_file:
                        for chunk in data_gen:
                            apk_file.write(chunk)
                except IOError as exc:
                    print('Error while writing %s: %s' % (filename, exc))
                    failed.append(docid)
                details['filename'] = filename
                success.append(details)
        for x in success:
            self.insert_app_into_state(x)
        return {'status': 'SUCCESS',
                'message': {'success': success,
                            'failed': failed,
                            'unavail': unavail}}

    def check_local_apks(self):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        if len(self.currentSet) == 0:
            print('There is no package')
            return {'status': 'SUCCESS',
                    'message': []}
        else:
            toUpdate = []
            for app in self.currentSet:
                details = self.details(app.get('docid'))
                #print(details)
                if details is None:
                    print('%s not available in Play Store' % app['docid'])
                    continue
                details['filename'] = app.get('filename')
                if self.debug:
                    print('Checking %s' % app['docid'])
                    print('%d == %d ?' % (app.get('details').get('appDetails')['versionCode'], details.get('details').get('appDetails')['versionCode']))
                if app.get('details').get('appDetails')['versionCode'] !=  details.get('details').get('appDetails')['versionCode']:
                    toUpdate.append(details)
        return {'status': 'SUCCESS',
                'message': toUpdate}

    def remove_local_app(self, docid):
        if not self.loggedIn:
            return {'status': 'UNAUTHORIZED'}
        # get app from cache
        app = list(filter(lambda x: x['docid'] == docid, self.currentSet))
        if len(app) < 1:
            return {'status': 'ERROR'}
        apkPath = os.path.join(self.download_path, app[0]['filename'])
        if os.path.isfile(apkPath):
            os.remove(apkPath)
            self.currentSet.remove(app[0])
            return {'status': 'SUCCESS'}
        return {'status': 'ERROR'}
