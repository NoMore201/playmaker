# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example.png)

## Table of Content

* [Description & Features](#desc)
* [Usage](#usage)
* [Alternatives](#diff)

<a name="desc"/>

## Description & Features

Playmaker is a fdroid repository manager, which lets you download/update apps from the play store using your google account
and configure repository with app you download. After you setup the server, repository will be available at the address 
`http[s]://<playmaker_host>/fdroid`, and you can start downloading apps from play store.

Server uses [googleplay-api](https://github.com/NoMore201/googleplay-api) library, which is the python equivalent of the Java [play-store-api](https://github.com/yeriomin/play-store-api) library used by YalpStore.

Features:
* Download apks from google play store to your collection. Update them or delete if they are not needed anymore.
* Manage the fdroid repository. You can update it manually, as you add/remove apks to your collection.
* Non-blocking UI, you can browse the collection or search for an app while the server is updating the fdroid
repository.
* Responsive UI, usable also from a mobile device

<a name="usage"/>

## Usage

### Requirements

Playmaker requires HTTPS to avoid mitm attacks, since it needs to send base64 encoded google credentials to the server. You can use you own certs, placing them in a `certs` subfolder in the current working directory (or in the mounted volume if you are using docker image)

```
# cd /srv/playmaker
# mkdir certs
# cp [cert_dir]/my.crt ./certs/playmaker.crt
# cp [cert_dir]/my.key ./certs/playmaker.key
```

If you are running playmaker behind an already configured HTTPS proxy like nginx, or if you want to locally start it without HTTPS, you need to disable built-in https support (docker image has disabled HTTPS support by default)

```
# pm-server --debug --fdroid --no-https
```

On first launch, playmaker will ask your for your google credentials. To avoid authentication problems, like captcha requests,
it's recommended to setup app specific password, and securing your account with 2-factor auth.

### Docker image

Since this app requires a lot of heavy dependencies, like Android SDK and fdroidserver, it is recommended to use the docker image. You can use a pre-built image on docker hub:

```
docker run -d --name playmaker -p 5000:5000 -v /srv/fdroid:/data/fdroid nomore201/playmaker
```

or use the available `Dockerfile` if you want to build it by yourself. Notice that the docker image is built by default with HTTPS support disabled, so if you need it change `Dockerfile` accordingly and place your certificate in the mounted volume like described above

### Virtualenv

If you want to run it in a virtualenv rather than using docker, remember that you need to install fdroidserver,
android SDK and define the ANDROID_HOME env variable (see the Dockerfile as a reference).
Instruction on how to install fdroidserver [here](https://f-droid.org/docs/Installing_the_Server_and_Repo_Tools/)

<a name="diff"/>

## Alternatives

### YalpStore

[YalpStore](https://github.com/yeriomin/YalpStore) is an open source alternative to the play store. It works very well and it requires you to install only the app, but it requires one of the following thing to be able to install/update apks:

- enable **Unknown Sources**
- have **root** privileges

While if you use playmaker and the fdroid [privileged extension](https://gitlab.com/fdroid/privileged-extension), fdroid will be able to install/update app without root privileges or enabling unknown sources.
