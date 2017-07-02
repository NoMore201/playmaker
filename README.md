# Playmaker

## Description

Playmaker is a python3-only apk manager with a web interface. The backend is taken from gplaycli/gplayweb python3 branch, with a few modifications.
On the other hand, the frontend is completely rewritten using modern web technologies and material design toolkits.

## Development TODOs

### Backend
- [ ] Switch to an async webserver ( [tornado](http://www.tornadoweb.org/en/stable/), [kyoukai](https://github.com/SunDwarf/Kyoukai) )
- [ ] General python3 code check
- [x] API for deleting apk
- [x] Save local apps in application state (for fast retrieving)
- [ ] configuration API (mainly for resetting/updating tokens)
- [x] fdroid integration

### Frontend
- [x] Implement search page
- [x] Implement /gplay/check
- [x] Implement /gplay/download
- [ ] Add placeholder when there aren't local apps
- [ ] Merge both AppViews in the same file (need to investigate)
- [ ] Add some kind of notifications ([toasts](https://fezvrasta.github.io/snackbarjs/))

## Usage

### Docker

There is a working Dockerfile (based on the [gplayweb one](https://github.com/matlink/gplayweb/blob/master/Dockerfile)). You can build and run by simply doing:

```
docker build -t playmaker .
docker run -d --restart always --name playmaker -p 5000:5000 -v /srv/fdroid:/data/fdroid playmaker
```
If you need to change the configuration, copy `playmaker.conf` inside `/srv/fdroid` and modify it. The app will look first there for a .conf file, and if it can't find anything, it will check system folders.
### Directly

Otherwise you can run it directly. Note that in order to run it you need [fdroidserver](https://gitlab.com/fdroid/fdroidserver) app, but you can also comment out the fdroid calls inside `service.py` and start it without.
**!! If you use Ubuntu 16.04+** the fdroidserver package in the repositories is a but buggy, so I suggest you to install it through the guardianproject ppa (as explained in their repo).

```
pip install -r requirements.txt  # consider using a virtualenv
python3 playmaker.py
```

it will listen on Flask default port 5000. By default the application uses [Matlink token-dispenser service](https://github.com/matlink/gplaycli#changelog). However, in order to avoid [problems](https://github.com/matlink/gplaycli/issues/80) I suggest you to host your own instance of [token-dispenser](https://github.com/yeriomin/token-dispenser).

For additional informations on how to do this, consider checking the Docker images for token-dispenser: https://github.com/NoMore201/docker-token-dispenser

After correctly setting up the server, change the `tokenurl` variable inside `playmaker.conf`.
