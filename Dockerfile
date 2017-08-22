FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y python3-dev python3-pip git \
    lib32stdc++6 \
    lib32gcc1 \
    lib32z1 \
    lib32ncurses5 \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    openjdk-8-jdk \
    virtualenv \
    wget \
    unzip \
    zlib1g-dev \
    software-properties-common

# Using guardian project ppa because the version in
# ubuntu repositories is a bit buggy
RUN add-apt-repository ppa:guardianproject/ppa && \
    apt-get update && \
    apt-get install -y fdroidserver

WORKDIR /opt
RUN git clone https://github.com/NoMore201/playmaker

RUN wget https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip \
    && echo "444e22ce8ca0f67353bda4b85175ed3731cae3ffa695ca18119cbacef1c1bea0  sdk-tools-linux-3859397.zip" | sha256sum -c \
    && unzip sdk-tools-linux-3859397.zip \
    && rm sdk-tools-linux-3859397.zip

RUN mkdir /opt/android-sdk-linux
ENV ANDROID_HOME=/opt/android-sdk-linux
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
RUN echo 'y' | tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "platforms;android-26" \
    && tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "build-tools;26.0.1" \
    && tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "platform-tools" \
    && tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "tools"

RUN mkdir -p /data/fdroid/repo

WORKDIR /opt/playmaker
RUN pip3 install -r requirements.txt

VOLUME /data/fdroid
WORKDIR /data/fdroid

RUN cp /opt/playmaker/playmaker.conf /etc

EXPOSE 5000
ENTRYPOINT /usr/bin/env python3 -u /opt/playmaker/playmaker.py --fdroid --debug
