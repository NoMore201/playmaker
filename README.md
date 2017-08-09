# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example1.png)

## Description

Playmaker is a python3-only apk manager with a web interface. The backend is taken from gplaycli/gplayweb python3 branch, with a few modifications.
On the other hand, the frontend is completely rewritten using Backbonejs web framework.

## Development TODOs

### Backend
- [ ] Switch to an async webserver ( [tornado](http://www.tornadoweb.org/en/stable/) )
- [ ] General python3 code check
- [ ] Fdroid repo configuration
- [x] fdroid integration

### Frontend
- [ ] Fdroid repo configuration page
- [ ] Integrate both Apps and Search views in a single page
- [ ] Add placeholder when there aren't local apps
- [x] *Check* and *Fdroid update* buttons need some visual feedback while executing
- [x] Add some kind of notification
- [x] Make notifications disappear after some seconds
- [x] gplay.js: populate collection manually (no fetch)

### Dockerfile
- [ ] Use updated Android SDK
- [ ] Try to make image a bit smaller

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

Otherwise you can run it directly. Note that in order to run it you need [fdroidserver](https://gitlab.com/fdroid/fdroidserver) app, but you can also comment out the fdroid calls inside `service.py` and start it without.
**!! If you use Ubuntu 16.04+** the fdroidserver package in the repositories is a but buggy, so I suggest you to install it through the guardianproject ppa (as explained in their repo).

```
usage: playmaker.py [-h] [-f] [-d]

Apk and fdroid repository manager with a web interface.

optional arguments:
  -h, --help    show this help message and exit
  -f, --fdroid  Enable fdroid integration
  -d, --debug   Enable debug output
```

By default the application uses a token-dispenser server provided by me. However, you can host your own instance of [token-dispenser](https://github.com/yeriomin/token-dispenser) and then change the tokenurl variable in the config file.

For additional informations, check out Dockerfiles for token-dispenser: https://github.com/NoMore201/docker-token-dispenser
