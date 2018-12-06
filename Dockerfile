FROM python:3-stretch

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
    openjdk-8-jdk-headless \
    virtualenv \
    wget \
    unzip \
    fdroidserver \
    zlib1g-dev

RUN wget https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip \
    && echo "444e22ce8ca0f67353bda4b85175ed3731cae3ffa695ca18119cbacef1c1bea0  sdk-tools-linux-3859397.zip" | sha256sum -c \
    && unzip sdk-tools-linux-3859397.zip \
    && rm sdk-tools-linux-3859397.zip

RUN mkdir /opt/android-sdk-linux
ENV ANDROID_HOME=/opt/android-sdk-linux
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
RUN echo 'y' | tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "platforms;android-26" \
    && tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose "build-tools;26.0.1" \
    && rm -rf tools

RUN mkdir -p /data/fdroid/repo && \
    mkdir -p /opt/playmaker

COPY README.md setup.py pm-server /opt/playmaker/
ADD playmaker /opt/playmaker/playmaker

WORKDIR /opt/playmaker
RUN pip3 install . && \
    cd /opt && rm -rf playmaker

RUN groupadd -g 999 pmuser && \
    useradd -m -u 999 -g pmuser pmuser
RUN chown -R pmuser:pmuser /data/fdroid && \
    chown -R pmuser:pmuser /opt/playmaker
USER pmuser

VOLUME /data/fdroid
WORKDIR /data/fdroid

EXPOSE 5000
ENTRYPOINT python3 -u /usr/local/bin/pm-server --fdroid --debug
