FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y python3-dev python3-pip git && \
    cd /opt && git clone https://github.com/NoMore201/playmaker

WORKDIR /opt/playmaker

RUN pip3 install -r requirements.txt
ENTRYPOINT /opt/playmaker/playmaker
