# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example.png)

## Table of Content

* [Description & Features](#desc)
* [Usage](#usage)
* [Alternatives](#diff)

<a name="desc"/>

## Description & Features

Playmaker is a fdroid repository manager, which lets you download/update apps from the play store using your google account
and configure repository with app you download. After you setup the server, repository will be available at the address `http[s]://<playmaker_host>/fdroid`, and you can start downloading apps from play store.

Features:
* Download apks from google play store to your collection. Update them or delete if they are not needed anymore.
* Manage the fdroid repository. You can update it manually, as you add/remove apks to your collection.
* Non-blocking UI, you can browse the collection or search for an app while the server is updating the fdroid
repository.
* Responsive UI, usable also from a mobile device

<a name="usage"/>

## Usage

### Requirements

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

<a name="diff"/>

## Alternatives

### YalpStore

[YalpStore](https://github.com/yeriomin/YalpStore) is an open source alternative to the play store. It works very well and it requires you to install only the app, but it requires one of the following thing to be able to install/update apks:

- enable **Unknown Sources**
- have **root** privileges

While if you use playmaker and the fdroid [privileged extension](https://gitlab.com/fdroid/privileged-extension), fdroid will be able to install/update app without root privileges or enabling unknown sources.
