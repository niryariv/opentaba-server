"""
This is the code to make a connection to our mongodb instance
"""

import os
import pymongo
from pymongo.errors import ConnectionFailure
from urlparse import urlparse

MONGO_URL = os.environ.get('MONGOHQ_URL')

if MONGO_URL:  # on Heroku, get a connection
    m_conn = pymongo.Connection(MONGO_URL)
    db = m_conn[urlparse(MONGO_URL).path[1:]]
    RUNNING_LOCAL = False
else:  # work locally
    try:
        m_conn = pymongo.Connection('localhost', 27017)
    except ConnectionFailure:
        print('You should have mongodb running')

    db = m_conn['citymap']
    RUNNING_LOCAL = True
