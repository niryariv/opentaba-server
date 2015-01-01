#!/usr/bin/python

# allow ourselves to import from the parent and current directory
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '.')

import os
import datetime
from optparse import OptionParser
from time import sleep
import requests

from lib.conn import *
import lib.helpers as helpers
from lib.sociallib import post

# can't communicate with poster service without these
if not all(param in os.environ.keys() for param in ['POSTER_SERVICE_URL', 'POSTER_ID']):
    print 'Environment variables POSTER_SERVICE_URL and POSTER_ID must both be set!'
    exit(1)

parser = OptionParser()
parser.add_option('-m', dest='min_date', help='minimum date for plans to be sent to poster service. if not supplied, ALL plans will be sent. format: 1/1/2015')
parser.add_option('-q', dest='quiet', default=False, action='store_true', help='quiet, don\'t prompt for user approval')
parser.add_option('-d', dest='dont_wait', default=False, action='store_true', help='don\'t wait for poster service to post everything')

(options, args) = parser.parse_args()

if options.min_date:
    # make sure the min_date parses fine
    try:
        min_date = datetime.datetime.strptime(options.min_date, '%d/%m/%Y')
    except:
        print 'Invalid minimum date. Format is 1/1/2015'
        exit(1)
    
    # build min_date query
    plans_query = {'$or': [ {'year': {'$gt': min_date.year}}, {'year': min_date.year, 'month': {'$gt': min_date.month}}, {'year': min_date.year, 'month': min_date.month, 'day': {'$gte': min_date.day}} ]}
else:
    # no query
    plans_query = {}

# get valid plans
plans = helpers._get_plans(query=plans_query)

# if not quiet, make sure the user is ok with this
if not options.quiet:
    while 1:
        if not options.min_date:
            sys.stdout.write('No minimum date was supplied.\nAre you sure you want ALL %s plans to be synced? [y/N] ' % len(plans))
        else:
            sys.stdout.write('Are you sure you want %s plans to be synced? [y/N] ' % len(plans))
        
        choice = raw_input().lower()
        if choice == 'n' or choice == 'no':
            exit()
        elif choice == 'y' or choice == 'yes':
            break

print 'Posting plans... (may take up to a few minutes, depending on how many are sent)'

# reverse the list so that we send the service the earlier plans first (service's queue is fifo)
for plan in reversed(plans):
    post(plan)

if not options.dont_wait:
    status = 10
    
    while status > 1:
        print 'Poking poster service for status...'
        
        r = requests.get('%s/status' % os.environ['POSTER_SERVICE_URL'].rstrip('/'))
        for s in r.text.split():
            if s.isdigit():
                status = int(s)
        
        print 'Approxiamtely %s posts remaining...' % status
        
        # wait for 30 seconds then poke again
        sleep(30)
    
    print 'Poster done!'
