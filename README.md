# Playmaker

![screenshot](https://github.com/NoMore201/playmaker/raw/master/example.png)

## Description & Features

Playmaker is a fdroid repository manager, which lets you download/update apps from the play store using your google account
and configure repository with app you download. After you setup the server, repository will be available at the address 
`http[s]://<playmaker_host>/fdroid`, and you can start downloading apps from play store.

Server uses [googleplay-api](https://github.com/NoMore201/googleplay-api) library, which is the python equivalent of the Java [play-store-api](https://github.com/yeriomin/play-store-api) library used by YalpStore.

Features:
* Download apks from google play store to your collection
* Generate a fdroid repository serving apks downloaded, directly from `<pm_url>/fdroid`
* Configure automatic updates of app+repo through a Crontab string
* Non-blocking UI, you can browse the collection or search for an app while the server is updating the fdroid
repository.
* Responsive UI, usable also from a mobile device

## Configuration

### Authentication

To avoid authentication problems, like captcha requests, it's recommended to setup app specific password, and securing your account with 2-factor auth. There are two ways to login to Play Store:

- Providing credentials in a configuration file
- Through a login page.

The default behaviour is to ask credentials with a login page, when accessing playmaker on first launch. In order to skip login page, it is possible to provide google credentials through a configuration file. Just put `credentials.conf` inside the playmaker directory, with this structure:

```
[google]
email = myemail@gmail.com
password = mypassword
```

To restrict access to that file, ensure it is readable only by user running playmaker.

### HTTPS

It's recommended to configure playmaker with HTTPS, especially with the login page authentication, since playmaker needs to send to the server credentials in plaintext. You can setup it in conjunction with a proxy like nginx, or provide certificate directly to playmaker.

## Running

Since this app requires a lot of heavy dependencies, like Android SDK and fdroidserver, it is recommended to use the docker image.
You can use a pre-built image on [docker hub](https://hub.docker.com/r/nomore201/playmaker/builds/) or build by yourself using provided `Dockerfile`.
There are some environment variables you'll want to use:

- `HTTPS_CERTFILE`: path of the https certificate file
- `HTTPS_KEYFILE`: path of the https key file
- `LANG_LOCALE`: set a specific locale. Defaults to the system one if not set
- `LANG_TIMEZONE`: set a specific timezone. Defaults to `Europe/Berlin` if not set
- `CRONTAB_STRING`: crontab string to configure automatic updates. Defaults to every night at 2AM (`0 2 * * *`)
- `DEVICE_CODE`: specify a device to be used by playmaker, defaults to `bacon` (OnePlus One) if not specified. For
a list of supported devices see [this file](https://raw.githubusercontent.com/NoMore201/googleplay-api/master/gpapi/device.properties)

To enable HTTPS through playmaker, without an external tool, just define `HTTPS_CERTFILE`
and `HTTPS_KEYFILE` with paths to those file. If these variables are not set, tornado will default to http.

If you want to browse apps for a specific country, you need to specify the variables `LANG_LOCALE` and `LANG_TIMEZONE`.
Before creating an issue "cannot find app X", make sure the app is available it that country.

The docker run command will look like this:
```
docker run -d --name playmaker \
    -p 5000:5000 \
    -v /srv/fdroid:/data/fdroid \
    -e HTTPS_CERTFILE="/srv/https.crt" \
    -e HTTPS_KEYFILE="/srv/https.key" \
    -e LANG_LOCALE="de_DE" \
    -e LANG_TIMEZONE="Europe/Berlin" \
    -e DEVICE_CODE="hammerhead" \
    fellek/playmaker:fellek
```

If you want to run it in a virtualenv rather than using docker, remember that you need to install fdroidserver,
android SDK and define the ANDROID\_HOME env variable (see the Dockerfile as a reference).
Instruction on how to install fdroidserver [here](https://f-droid.org/docs/Installing_the_Server_and_Repo_Tools/)

## Alternatives

### YalpStore

[YalpStore](https://github.com/yeriomin/YalpStore) is an open source alternative to the play store.
It works very well and it requires you to install only the app, but it requires one of the
following thing to be able to install/update apks:

- enable **Unknown Sources**
- have **root** privileges

If you use playmaker and the fdroid [privileged extension](https://gitlab.com/fdroid/privileged-extension),
fdroid will be able to install/update app without root privileges or enabling unknown sources.
