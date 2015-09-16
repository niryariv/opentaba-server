"""
This is the code to make a connection to our mongodb instance
"""

import os
import pymongo
from pymongo.errors import ConnectionFailure
from urlparse import urlparse

# support legacy munis that were installed with MongoHQ before it canceled the sandbox plan
MONGO_URL = os.environ.get('MONGOLAB_URI') or os.environ.get('MONGOHQ_URL')


if MONGO_URL:  # on Heroku, get a connection
    m_conn = pymongo.MongoClient(MONGO_URL)
    db = m_conn[urlparse(MONGO_URL).path[1:]]
    RUNNING_LOCAL = False
else:  # work locally
    try:
        m_conn = pymongo.MongoClient('localhost', 27017)
    except ConnectionFailure:
        print('You should have mongodb running')

    db = m_conn['citymap']
    RUNNING_LOCAL = True
