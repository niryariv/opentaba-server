FROM ubuntu:14.04

RUN apt-get update
RUN apt-get -y install mongodb-server redis-server python-pip \
                       gcc-4.8-base python-dev libmemcached-dev memcached \
                       zlib1g-dev libxml2-dev libxslt1-dev mongodb
RUN mkdir -p /opt/opentaba-server && mkdir -p /opt/opentaba-server/filecache && mkdir -p /data/db
COPY . /opt/opentaba-server
RUN pip install -r /opt/opentaba-server/requirements.txt
RUN chmod +x /opt/opentaba-server/entrypoint.sh
ENV RUN_SERVER=1
ENTRYPOINT "/opt/opentaba-server/entrypoint.sh"
