from googleplay_api.service import Play
import sys

apps = ['org.mozilla.firefox', 'com.whatsapp', 'com.appthatdoesntexits', 'it.atm.appmobile']

service = Play()

downloaded = service.download_selection(apps)
if len(downloaded['unavail']) == 0:
    print('Results "unavail" list is empty. It should not')
    sys.exit(1)
if downloaded['unavail'][0] != apps[2]:
    print('Wrong result in download_selection()')
    sys.exit(1)
local_apks = service.get_local_apks()
service.check_local_apks()
local = service.get_local_apps()
