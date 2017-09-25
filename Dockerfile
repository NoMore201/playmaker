FROM python:stretch

RUN apt-get update && \
    apt-get install -y git \
    lib32stdc++6 \
    lib32gcc1 \
    lib32z1 \
    lib32ncurses5 \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libxml2-dev \
    libxslt1-dev \
    openjdk-8-jdk \
    virtualenv \
    wget \
    unzip \
    zlib1g-dev

# python deps setup
RUN pip3 install pyaxmlparser pyasn1 tornado pycrypto requests

RUN cd /opt && git clone https://gitlab.com/fdroid/fdroidserver.git && \
    cd fdroidserver && python3 setup.py install

RUN wget https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip \
    && echo "444e22ce8ca0f67353bda4b85175ed3731cae3ffa695ca18119cbacef1c1bea0  sdk-tools-linux-3859397.zip" | sha256sum -c \
    && unzip sdk-tools-linux-3859397.zip \
    && rm sdk-tools-linux-3859397.zip

RUN mkdir /opt/android-sdk-linux
ENV ANDROID_HOME=/opt/android-sdk-linux
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
RUN echo 'y' | tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "platforms;android-26" \
    && tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "build-tools;26.0.1" \
    && tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "platform-tools"

RUN mkdir -p /data/fdroid/repo

WORKDIR /opt
RUN git clone https://github.com/NoMore201/playmaker && \
    git clone https://github.com/NoMore201/googleplay-api

WORKDIR /opt/googleplay-api
RUN python3 setup.py install && cd /opt && rm -rf googleplay-api

WORKDIR /opt/playmaker
RUN python3 setup.py install

VOLUME /data/fdroid
WORKDIR /data/fdroid

RUN cp /opt/playmaker/playmaker.conf /data/fdroid

EXPOSE 5000
ENTRYPOINT python3 -u /usr/local/bin/pm-server --fdroid --debug
