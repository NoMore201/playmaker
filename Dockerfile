FROM python:3-alpine

# use all available cores when using make
ARG MAKEFLAGS="-j $(nproc)"
# location of android SDK
ARG ANDROID_HOME=/opt/android-sdk-linux
# URL to get android SDK from
ARG ANDROID_SDK_URL=https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip
# name of downloaded android SDK archive
ARG ANDROID_SDK_ARCHIVE="sdk.zip"
# checksum of the android SDK file
ARG ANDROID_SDK_CHECKSUM="444e22ce8ca0f67353bda4b85175ed3731cae3ffa695ca18119cbacef1c1bea0"

# location of android SDK (from build argument)
ENV ANDROID_HOME=${ANDROID_HOME}
# add android SDK to path
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Install android SDK
RUN echo "${ANDROID_SDK_CHECKSUM} ${ANDROID_SDK_ARCHIVE}"  && apk add --no-cache --virtual install-deps wget unzip \
# fetch and extract android SDK archive
    && wget -O ${ANDROID_SDK_ARCHIVE} --quiet ${ANDROID_SDK_URL} \
    && echo -n "${ANDROID_SDK_CHECKSUM} *${ANDROID_SDK_ARCHIVE}" | sha256sum -c - \
    && unzip ${ANDROID_SDK_ARCHIVE} \
    && rm ${ANDROID_SDK_ARCHIVE} \
    && mkdir ${ANDROID_HOME} \
# install JDK
    && apk add --no-cache openjdk8 \
# install android SDK
    && echo 'y' | tools/bin/sdkmanager --sdk_root=${ANDROID_HOME} --verbose "platforms;android-26" \
    && tools/bin/sdkmanager --sdk_root=${ANDROID_HOME} --verbose "build-tools;26.0.1" \
# remove Android SDK tools
    && rm -rf tools \
# remove SDK install dependencies
    && apk del install-deps

# copy installation files
COPY README.md setup.py pm-server /opt/playmaker/
# copy source files
COPY playmaker /opt/playmaker/playmaker

WORKDIR /opt/playmaker
RUN apk add --no-cache --virtual build-deps \
# install build dependencies
    git \
    alpine-sdk \
    libffi-dev \
    openssl-dev \
    libxml2-dev \
    libxml2 \
    zlib-dev \
    freetype-dev \
    libjpeg-turbo-dev \
    libpng \
# install run time dependencies
    && apk add --no-cache libxslt-dev \
# pip install with cache disabled to reduce image size
    && pip3 install . --no-cache-dir \
# pip install fdroidserver
    && pip3 install fdroidserver --no-cache-dir \
# remove source files
    && rm -rf playmaker \
# remove build dependencies
    && apk del build-deps \
# create directories and set permissions
    && addgroup -S pmuser && adduser -S pmuser -G pmuser \
    && mkdir -p /data/fdroid/repo \
    && chown -R pmuser /data/fdroid \
    && chown -R pmuser /opt/playmaker

# switch to non root user
USER pmuser

VOLUME /data/fdroid
WORKDIR /data/fdroid

EXPOSE 5000
ENTRYPOINT ["python3", "-u", "/usr/local/bin/pm-server", "--fdroid", "--debug"]
