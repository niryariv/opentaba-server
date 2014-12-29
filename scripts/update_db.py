#!/usr/bin/env python2

# allow ourselves to import from the parent and current directory
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '.')

from conn import *
from gushim import GUSHIM
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--force", dest="force", default=False, action="store_true", help="update gushim in db")
parser.add_option("-m", dest="municipality", help="name of the municipality this server should serve ('all' to serve all of them)")

(options, args) = parser.parse_args()

if not options.force:
    print ("This script will update the gushim collection in the actual db. "
           "To make sure this isn't running by mistake, run this with --force")
    exit()

if not options.municipality:
    print ("Parameter \"-m <specific-municipality | all>\" must be specified")
    exit()

if options.municipality != "all" and options.municipality not in GUSHIM.keys():
    print ("Municipality %s does not exist" % options.municipality)
    exit()

gushim_collection = db.gushim.find()
existing_gushim = []

for g in gushim_collection:
    existing_gushim.append(g['gush_id'])

total_gushim = len(existing_gushim)

for city in GUSHIM.keys():
    if options.municipality == 'all' or city == options.municipality:
        for g in GUSHIM[city]['list']:
            if g not in existing_gushim:
                print 'Inserting new gush id: ', g
                db.gushim.insert({'gush_id': g,
                                  'json_hash': '',
                                  'last_checked_at': ''})
                total_gushim += 1
                existing_gushim.append(g)

print 'There are currently %s gushim' % str(total_gushim)
