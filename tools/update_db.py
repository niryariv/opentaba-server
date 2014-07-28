#!/usr/bin/env python2

from conn import *
from gushim import GUSHIM
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--force", dest="force", default=False, action="store_true", help="update gushim in db")

(options, args) = parser.parse_args()

if not options.force:
    print ("This script will update the gushim collection in the actual db. "
           "To make sure this isn't running by mistake, run this with --force")
    exit()

gushim_collection = db.gushim.find()
existing_gushim = []

for g in gushim_collection:
    existing_gushim.append(g['gush_id'])

total_gushim = len(existing_gushim)

for city in GUSHIM.keys():
    for g in GUSHIM[city]['list']
        if g not in existing_gushim:
            print 'Inserting new gush id: ', g
            db.gushim.insert({'gush_id': g,
                              'json_hash': '',
                              'last_checked_at': ''})
            total_gushim += 1
            existing_gushim.append(g)

print 'There are currently %s gushim' % str(total_gushim)
