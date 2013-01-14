from optparse import OptionParser

from app import *
from rq import Queue
from worker import conn

from tools.scrapelib import scrape_gush

parser = OptionParser()
parser.add_option("-g", dest="gush", help="ID of gush to scrape (-g all to scrape all)")

(options, args) = parser.parse_args()

if not options.gush:
	print "must include -g <gush ID>"
	exit()

gush_id = options.gush

q = Queue(connection=conn)


# find gush/im
if gush_id=="all":
	gushim = db.gushim.find()
else:
	gushim = [db.gushim.find_one({"gush_id" : gush_id})]


# enqueue them
for g in gushim:
	print "Queue gush %s" % g['gush_id']
	q.enqueue(scrape_gush, g)