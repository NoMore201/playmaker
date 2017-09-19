# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example1.png)

## Table of Content

* [Description & Features](#desc)
* [Usage](#usage)
* [TODOs](#todos)
  * [Backend](#todos-backend)
  * [Frontend](#todos-frontend)
  * [Dockerfile](#todos-docker)

<a name="desc"/>

## Description & Features

Playmaker is a python3 apk manager with a web interface. The backend uses the python3 branch of googleplay-api, taken from [gplaycli](https://github.com/matlink/gplaycli)
with a few fixes, together with WebTornado non-blocking web server. Frontend code uses BackboneJS as the JS framework, bootstrap and font-awesome.

Features:
* Download/Update/Delete apks from google play store
* Automatically setup a fdroid repository with the downloaded apks
* Update fdroid and downloads work in background, without blocking UI
* Automatically handle google login tokens using token-dispenser
* Responsive UI

<a name="usage"/>

## Usage

There is a working Dockerfile. You can build and run it, or use a pre-built image on docker hub:

```
docker run -d --restart always --name playmaker -p 5000:5000 -v /srv/fdroid:/data/fdroid nomore201/playmaker
```

**REQUIRED** **You need to insert you google credentials in the configuration file!!**. Copy `playmaker.conf` inside `/srv/fdroid` and modify it. Credentials have this structure:

```
# parts inside square brackets are not mandatory
email = <google_user>[@gmail.com]
password = <google_passowrd> | <app specific_password>
```

Otherwise you can run it from the command line, but this is not recommended since you need to setup the android sdk and the fdroidserver tools

```
usage: playmaker.py [-h] [-f] [-d]

Apk and fdroid repository manager with a web interface.

optional arguments:
  -h, --help    show this help message and exit
  -f, --fdroid  Enable fdroid integration
  -d, --debug   Enable debug output
```

<a name="todos"/>

## TODOs

<a name="todos-backend"/>

### Backend

- [ ] Auto-update apks
- [ ] System settings (fdroid, auto-update, etc.)
- [x] Switch to an async webserver ( [tornado](http://www.tornadoweb.org/en/stable/) )
- [x] fdroid integration

<a name="todos-frontend"/>

### Frontend

- [ ] Fdroid repo configuration page
- [ ] Add placeholder when there aren't local apps
- [x] Switch to angular (less code, one page app)
- [x] Integrate both Apps and Search views in a single page
- [x] *Check* and *Fdroid update* buttons need some visual feedback while executing
- [x] Add some kind of notification
- [x] Make notifications disappear after some seconds
- [x] gplay.js: populate collection manually (no fetch)

<a name="todos-docker"/>

### Dockerfile

- [ ] Try to make image a bit smaller
- [x] Update Android SDK to Android 6.0+
