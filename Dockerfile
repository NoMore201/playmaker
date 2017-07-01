FROM ubuntu:16.04

RUN apt-get update && \
    apt-get -y upgrade && \
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
    zlib1g-dev \
    software-properties-common

RUN add-apt-repository ppa:guardianproject/ppa && \
    apt-get update && \
    apt-get install fdroidserver

WORKDIR /opt
RUN git clone https://github.com/NoMore201/playmaker

RUN wget https://dl.google.com/android/android-sdk_r24.3.4-linux.tgz \
    && echo "fb293d7bca42e05580be56b1adc22055d46603dd  android-sdk_r24.3.4-linux.tgz" | sha1sum -c \
    && tar xzf android-sdk_r24.3.4-linux.tgz \
    && rm android-sdk_r24.3.4-linux.tgz

ENV ANDROID_HOME=/opt/android-sdk-linux
ENV PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
RUN echo 'y' | android update sdk --no-ui -a --filter platform-tools,build-tools-22.0.1,android-22

RUN mkdir -p /data/fdroid/repo

WORKDIR /opt/playmaker
RUN pip3 install -r requirements.txt

VOLUME /data/fdroid
WORKDIR /data/fdroid

RUN cp /opt/playmaker/playmaker.conf /data/fdroid

EXPOSE 5000
ENTRYPOINT /opt/playmaker/playmaker.py
