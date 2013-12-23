from optparse import OptionParser, SUPPRESS_HELP

from app import *
from rq import Queue
from worker import conn

from tools.scrapelib import scrape_gush

parser = OptionParser()
parser.add_option("-g", dest="gush", help="ID of gush to scrape (-g all to scrape all)")
# Do not use Redis queuing - for Windows devs. DO NOT USE ON PRODUCTION
parser.add_option("--no-queue", dest="enable_queue", action="store_false", default=True, help=SUPPRESS_HELP)

(options, args) = parser.parse_args()

if not options.gush:
    print ("must include -g <gush ID>")
    exit()

gush_id = options.gush
print(gush_id)

# find gush/im
if gush_id == "all":
    gushim = db.gushim.find()
else:
    gushim = [db.gushim.find_one({"gush_id": gush_id})]

print(gushim)

# enqueue them
for g in gushim:
    if options.enable_queue:
        q = Queue(connection=conn)
        print ("Queue gush %s" % g['gush_id'])
        q.enqueue(scrape_gush, g)
    else:
        print "Scraping gush %s" % g['gush_id']
        scrape_gush(g)
