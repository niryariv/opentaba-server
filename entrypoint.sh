#!/usr/bin/bash

set -e

sed -i 's/daemonize no/daemonize yes/g' /etc/redis.conf
redis-server /etc/redis.conf
mongod --fork --logpath /tmp/mongo.log

cd /opt/opentaba-server
first_run=$(mongo --quiet --eval "db.getSiblingDB('citymap').plans.count()")
if [[ "$first_run" -eq "0" ]];
then
    echo "First Run, will create the databases now...."
    python scripts/create_db.py --force -m all
fi

if [[ "$RUN_SERVER" -eq "1" ]];
then
    python app.py
else
    exec /bin/bash "$@"
fi
