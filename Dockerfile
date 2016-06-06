FROM fedora:22

RUN dnf -y install mongodb-server.x86_64 redis.x86_64 python-pip.noarch \
                    gcc.x86_64 python-devel.x86_64 libmemcached-devel.x86_64 memcached.x86_64 \
                    zlib-devel.x86_64 libxml2-devel.x86_64 libxslt-devel.x86_64 mongodb.x86_64
RUN mkdir -p /opt/opentaba-server && mkdir -p /opt/opentaba-server/filecache && mkdir -p /data/db
COPY . /opt/opentaba-server
RUN pip install -r /opt/opentaba-server/requirements.txt
RUN chmod +x /opt/opentaba-server/entrypoint.sh
ENV RUN_SERVER=1
ENTRYPOINT "/opt/opentaba-server/entrypoint.sh"