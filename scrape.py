"""
Main script for scrapping the MMI site
"""

import sys
import logging
from optparse import OptionParser, SUPPRESS_HELP
from rq import Queue
from app import app
from tools.conn import *
from tools.scrapelib import scrape_gush
from worker import redis_conn


def scrape(gush_id, no_queue=False):
    log = logging.getLogger(__name__)
    log.info("Scraping gush: %s", gush_id)

    # find gush/im
    if gush_id == "all":
        """
        this is how we combat the low amount of memory available with the free redis instance -
        sort the gushim by descending last_checked_at timestamps. this is done because
        when redis reaches maxmemory it blocks ALL writes, so rq cannot work anymore
        until someone manually deletes stuff (even dequeueing doesn't work). so current
        solution is setting redis's maxmemory-policy to allkeys-lru, and that way the
        earliest jobs will just be discarded, and since we have the gushim by descending
        last checked order, the later-checked gushim will be discarded one by one so we
        can scrape the gushim that have not been scraped recently.
        """
        gushim = db.gushim.find().sort(u'last_checked_at', -1)
    else:
        gushim = [db.gushim.find_one({"gush_id": gush_id})]
    log.debug("Found gushim: %s", gushim)

    if no_queue:
        log.warn("redis queuing is disabled, this is not recommended")
        for g in gushim:
            log.info("Scraping gush %s", g['gush_id'])
            scrape_gush(g, False, app.config['TESTING'])
    else:
        # enqueue them
        q = Queue(connection=redis_conn)
        for g in gushim:
            log.info("Queuing gush %s for scraping", g['gush_id'])
            q.enqueue(scrape_gush, g, False, app.config['TESTING'])


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-g", dest="gush", help="ID of gush to scrape (-g all to scrape all)")
    # Do not use Redis queuing - for Windows devs. DO NOT USE ON PRODUCTION
    parser.add_option("--no-queue", dest="no_queue", action="store_true", default=False, help=SUPPRESS_HELP)
    parser.add_option("--verbose", dest="verbose", action="store_true", default=False, help="Print verbose debugging information")
    (options, args) = parser.parse_args()

    if not options.gush:
        sys.stderr.write("Error: please specify -g <gush ID>\n")
        sys.exit(1)

    if options.verbose:
        lvl = logging.DEBUG
    else:
        lvl = logging.INFO

    logging.basicConfig(format='%(asctime)-15s %(name)s %(levelname)s %(message)s', level=lvl)
    scrape(options.gush, no_queue=options.no_queue)
