# Playmaker

## Description

Playmaker is a python3-only apk manager with a web interface. The backend is taken from gplaycli/gplayweb python3 branch, with a few modifications.
On the other hand, the frontend is completely rewritten using modern web technologies and material design toolkits.

## Development TODOs

### Backend
- [ ] General python3 code check
- [x] Add API for deleting apk
- [x] Add API to get only local apk (for fast startup)
- [ ] Implement configuration methods

### Frontend
- [ ] Implement search page
- [ ] Implement /gplay/check
- [ ] Implement /gplay/download

## Usage

Just clone this repo and start the application

```
python3 playmaker.py
```

it will listen on Flask default port 5000. There is also an experimental Dockerfile, still working on it.
