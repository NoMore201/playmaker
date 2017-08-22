# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example1.png)

## Description & features

Playmaker is a python3 apk manager with a web interface. The backend uses the python3 branch of googleplay-api, taken from [gplaycli](https://github.com/matlink/gplaycli)
with a few fixes, together with WebTornado non-blocking web server. Frontend code uses BackboneJS as the JS framework, bootstrap and font-awesome.

Features:
* Download/Update/Delete apks from google play store
* Automatically setup a fdroid repository with the downloaded apks
* Update fdroid and downloads work in background, without blocking UI
* Automatically handle google login tokens using token-dispenser
* Responsive UI

## TODOs

### Backend
- [ ] Auto-update apks
- [ ] System settings (fdroid, auto-update, etc.)
- [x] Switch to an async webserver ( [tornado](http://www.tornadoweb.org/en/stable/) )
- [x] fdroid integration

### Frontend
- [ ] Switch to angular (less code, one page app)
- [ ] Integrate both Apps and Search views in a single page
- [ ] Fdroid repo configuration page
- [ ] Add placeholder when there aren't local apps
- [x] *Check* and *Fdroid update* buttons need some visual feedback while executing
- [x] Add some kind of notification
- [x] Make notifications disappear after some seconds
- [x] gplay.js: populate collection manually (no fetch)

### Dockerfile
- [ ] Try to make image a bit smaller
- [x] Update Android SDK to Android 6.0+

## Usage

### Docker

There is a working Dockerfile (based on the [gplayweb one](https://github.com/matlink/gplayweb/blob/master/Dockerfile)). You can build and run by simply doing:

```
docker build -t playmaker .
docker run -d --restart always --name playmaker -p 5000:5000 -v /srv/fdroid:/data/fdroid playmaker
```
or use the already built image on docker hub:

```
docker run -d --restart always --name playmaker -p 5000:5000 -v /srv/fdroid:/data/fdroid nomore201/playmaker
```
**Notice that** If you need to change the configuration, copy `playmaker.conf` inside `/srv/fdroid` and modify it. The app will look first there for a .conf file, and if it can't find anything, it will check system folders.

### Directly

Otherwise you can run it from the command line.

```
usage: playmaker.py [-h] [-f] [-d]

Apk and fdroid repository manager with a web interface.

optional arguments:
  -h, --help    show this help message and exit
  -f, --fdroid  Enable fdroid integration
  -d, --debug   Enable debug output
```

If you enable the fdroid integration, you need the [fdroidserver](https://gitlab.com/fdroid/fdroidserver) package.
**!! If you use Ubuntu 16.04+** the fdroidserver package in the repositories is a but buggy, so I suggest you to install it through the guardianproject ppa (as explained in their repo).

By default the application uses a token-dispenser server provided by me. However, you can host your own instance of [token-dispenser](https://github.com/yeriomin/token-dispenser) and then change the tokenurl variable in the config file.

For additional informations, check out Dockerfiles for token-dispenser: https://github.com/NoMore201/docker-token-dispenser
