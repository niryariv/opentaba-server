#!/usr/bin/python

from app import *
from tools.gushim import GUSHIM
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

db.gushim.create_index([('gush_id', 1)], unique=True)

for g in GUSHIM:
    db.gushim.insert({'gush_id': g,
                      'html_hash': '',
                      'last_checked_at': ''})

db.plans.create_index([('gush_id', pymongo.ASCENDING),
                       ('year', pymongo.DESCENDING),
                       ('month', pymongo.DESCENDING),
                       ('day', pymongo.DESCENDING),
                       ('number', pymongo.ASCENDING),
                       ('essence', pymongo.ASCENDING)],
                      unique=True)  # , drop_dups = True)

db.blacklist.insert({'blacklist': []})
