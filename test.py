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
local_apks = service.currentSet
print(str(local_apks))
service.download_selection(['com.backdrops.wallpapers'])
local_apks = service.currentSet
print(str(local_apks))
