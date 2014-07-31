#!/usr/bin/python

from conn import *
from gushim import GUSHIM
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--force", dest="force", default=False, action="store_true", help="delete existing dbs")

(options, args) = parser.parse_args()

if not options.force:
    print ("This script will delete the gushim and plans collection. "
           "To make sure this isn't running by mistake, run this with --force")
    exit()

# print "Deleting db.gushim and db.plans"
db.gushim.drop()
db.plans.drop()
# delete blacklist in case it still exists. we don't use it anymore
db.blacklist.drop()

db.gushim.create_index([('gush_id', 1)], unique=True)

"""
exisiting_gushim protects against gush numbers that can be part of more than one municipality. this is 
fine in the gushim.py file as it is used to filter the per-city atom feeds, but in our db we only want 
one instance of each gush number
"""
existing_gushim = []

for city in GUSHIM.keys():
    for g in GUSHIM[city]['list']:
        if g not in existing_gushim:
            db.gushim.insert({'gush_id': g,
                              'json_hash': '',
                              'last_checked_at': ''})
            existing_gushim.append(g)

db.plans.create_index([('plan_id', pymongo.DESCENDING)], unique=True)
db.plans.create_index([('gushim', pymongo.ASCENDING),
                       ('year', pymongo.DESCENDING),
                       ('month', pymongo.DESCENDING),
                       ('day', pymongo.DESCENDING),
                       ('number', pymongo.ASCENDING),
                       ('essence', pymongo.ASCENDING)],
                      unique=True)  # , drop_dups = True)

