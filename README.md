# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example2.png)

## Description

Playmaker is a python3-only apk manager with a web interface. The backend is taken from gplaycli/gplayweb python3 branch, with a few modifications.
On the other hand, the frontend is completely rewritten using modern web technologies and material design toolkits.

## Development TODOs

### Backend
- [ ] General python3 code check
- [x] Add API for deleting apk
- [x] Save local apps in application state (for fast retrieving)
- [ ] Implement configuration API (mainly for resetting/updating tokens)
- [ ] Add fdroid integration

### Frontend
- [x] Implement search page
- [ ] Implement /gplay/check
- [x] Implement /gplay/download
- [ ] Add placeholder when there aren't local apps
- [ ] Merge both AppViews in the same file (need to investigate)
- [ ] Add some kind of notifications ([toasts](https://fezvrasta.github.io/snackbarjs/))

## Usage

Install dependencies, then start the application

```
pip install -r requirements.txt  # consider using a virtualenv
python3 playmaker.py
```

it will listen on Flask default port 5000. By default the application uses [Matlink token-dispenser service](https://github.com/matlink/gplaycli#changelog). However, in order to avoid [problems](https://github.com/matlink/gplaycli/issues/80) I suggest you to host your own instance of [token-dispenser](https://github.com/yeriomin/token-dispenser).

For additional informations on how to do this, consider checking the Docker images for token-dispenser: https://github.com/NoMore201/docker-token-dispenser

After correctly setting up the server, change the `tokenurl` variable inside `playmaker.conf`.
