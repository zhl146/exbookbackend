FROM ubuntu:16.04

RUN apt-get install python3 libssl-dev
RUN mkdir -p /tmp/downloads/
RUN cd /tmp/downloads/
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py
RUN pip3 flask peewee werkzeug pymysql
