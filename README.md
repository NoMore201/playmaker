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

Playmaker is a python3 apk manager with a web interface. The backend uses an up-to-date version of [googleplay-api](https://github.com/NoMore201/googleplay-api)
 including a lot of improvements, WebTornado for its non-blocking behaviour, while the frontend is built with angularjs and the bootstrap CSS framework.

Features:
* Download apks from google play store to your collection. Update them or delete if they are not needed anymore.
* A fdroid repository is setup on first launch. You can update it manually, as you add/remove apks to your collection.
* Thanks to the non-blocking UI, you can browse the collection or search for an app while the server is updating the fdroid
repository.
* Responsive UI.

<a name="usage"/>

## Usage

###Requirements

Playmaker needs HTTPS to run, since it needs to send base64 encoded google credentials to the server,
to avoid mitm attacks. You can either use you own certs, placing them in a `certs` subfolder

```
# cd /srv/playmaker
# mkdir certs
# cp [cert_dir]/my.crt ./certs/playmaker.crt
# cp [cert_dir]/my.key ./certs/playmaker.key
# pm-server --debug --fdroid
```

or run it behind an https proxy like nginx, disabling playmaker's https support

```
# pm-server --debug --fdroid --no-https
```

On first launch, playmaker will ask your for your google credentials. To avoid problems, or captcha requests
it's recommended to setup app specific password, and securing your account with 2-factor auth.

### Docker image

Since this app requires a lot of heavy dependencies, like Android SDK and fdroidserver, it is recommended to use the docker image. You can use a pre-built image on docker hub:

```
docker run -d --name playmaker -p 5000:5000 -v /srv/fdroid:/data/fdroid nomore201/playmaker
```

or use the available `Dockerfile` if you want to build it by yourself.

### Virtualenv

If you want to run it in a virtualenv rather than using docker, remember that you need to build fdroidserver and setup the android SDK (see the Dockerfile as a reference).

```
usage: pm-server [-h] [-f] [-d]

Apk and fdroid repository manager with a web interface.

optional arguments:
  -h, --help    show this help message and exit
  -f, --fdroid  Enable fdroid integration
  -d, --debug   Enable debug output
  -n, --no-https  Disable HTTPS server
```

<a name="todos"/>

## TODOs

<a name="todos-backend"/>

### Backend

- [ ] Auto-update apks
- [ ] System settings (fdroid, auto-update, etc.)
- [x] Switch to an async webserver
- [x] fdroid integration

<a name="todos-frontend"/>

### Frontend

- [ ] Add more information for apps
- [ ] Better error handling
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
