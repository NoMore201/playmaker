FROM python:3-buster

RUN apt-get update && \
    apt-get install -y git \
    lib32stdc++6 \
    lib32gcc1 \
    lib32z1 \
    lib32ncurses6 \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libxml2-dev \
    libxslt1-dev \
    openjdk-11-jdk-headless \
    virtualenv \
    wget \
    unzip \
    zlib1g-dev \
    less \
    mc \
    nano \
    android-sdk-platform-tools \
    android-sdk-build-tools && \
    rm -rf /var/lib/apt/lists

#RUN wget https://dl.google.com/android/repository/commandlinetools-linux-6200805_latest.zip \
#    && echo "F10F9D5BCA53CC27E2D210BE2CBC7C0F1EE906AD9B868748D74D62E10F2C8275 commandlinetools-linux-6200805_latest.zip" | sha256sum -c \
#    && unzip commandlinetools-linux-6200805_latest.zip \
#    && rm commandlinetools-linux-6200805_latest.zip

#RUN mkdir /opt/android-sdk-linux \
#    && mv tools /opt/android-sdk-linux/tools

#ENV ANDROID_HOME=/opt/android-sdk-linux
#ENV PATH=$PATH:$ANDROID_HOME/tools

#RUN echo 'y' | /opt/android-sdk-linux/tools/bin/sdkmanager --sdk_root=/opt/android-sdk-linux --verbose --install "platforms;android-28" "build-tools;28.0.3"

#RUN echo 'y' | rm -rf tools

RUN mkdir -p /data/fdroid/repo && \
    mkdir -p /opt/playmaker

COPY README.md setup.py pm-server /opt/playmaker/
COPY playmaker /opt/playmaker/playmaker

WORKDIR /opt/playmaker
RUN pip3 install . && \
    cd /opt && rm -rf playmaker

#RUN pip3 install fdroidserver
RUN pip3 install Cython && \
	pip3 install fdroidserver && \
    pip3 install . && \
    cd /opt && rm -rf playmaker && \
    sed -i 's/\"sdk_version\"/#\"sdk_version\"/g' /usr/local/lib/python3.8/site-packages/gpapi/config.py

RUN groupadd -g 999 pmuser && \
    useradd -m -u 999 -g pmuser pmuser
RUN chown -R pmuser:pmuser /data/fdroid && \
    chown -R pmuser:pmuser /opt/playmaker
USER pmuser

VOLUME /data/fdroid
WORKDIR /data/fdroid

EXPOSE 5000
ENTRYPOINT python3 -u /usr/local/bin/pm-server --fdroid --debug