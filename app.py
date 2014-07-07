# -*- coding: utf-8 -*-
#!/usr/bin/python

import os
import datetime
import json
import pymongo
from pymongo.errors import ConnectionFailure
from bson import json_util
from urlparse import urlparse

from werkzeug.contrib.atom import AtomFeed
from werkzeug.urls import url_encode

from flask import Flask
from flask import abort, redirect, url_for, make_response, request

app = Flask(__name__)

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
    app.debug = True  # since we're local, keep debug on

#### Helpers ####


def _to_json(mongo_obj):
    """
    convert dictionary to JSON. json_util.default adds automatic mongoDB result support
    """
    return json.dumps(mongo_obj, ensure_ascii=False, default=json_util.default)


def _resp(data):
    r = make_response(_to_json(data))
    r.headers['Access-Control-Allow-Origin'] = "*"
    r.headers['Content-Type'] = "application/json; charset=utf-8"
    return r


def _plans_query_to_atom_feed(request, query={}, limit=0, feed_title=''):
    """
    Create an atom feed of plans fetched from the DB based on an optional query
    """
    plans = db.plans.find(query, limit=1000).sort(
        [("year", pymongo.DESCENDING), ("month", pymongo.DESCENDING), ("day", pymongo.DESCENDING)])
    
    # remove duplicate plans (ie when a plan is in >1 gush)
    seen = set()
    plans = [p for p in plans if p['number'] not in seen and not seen.add(p['number'])]

    # of the remains, take the latest N
    if limit > 0:
        plans = plans[:limit]

    feed = AtomFeed(feed_title, feed_url=request.url, url=request.url_root)

    for p in plans:
        url = p['details_link']
        content = p['essence'] + ' [' + p['status'] + ', ' + '%02d/%02d/%04d' % (p['day'], p['month'], p['year']) + ', ' + p['number'] + ']'
        title = p['location_string']
        # 'not title' is not supposed to happen anymore because every plan currently has a location
        if not title:
            title = p['number']

        feed.add(
            title=title,
            content=content,
            content_type='html',
            author="OpenTABA.info",
            id=url + '&status=' + p['status'],
            # this is a unique ID (not real URL) so adding status to ensure uniqueness in TBA stages
            url=url,
            updated=datetime.date(p['year'], p['month'], p['day'])
        )

    return feed


#### ROUTES ####

@app.route('/gushim.json')
def get_gushim():
    """
    get gush_id metadata
    """
    detailed = request.args.get('detailed', '') == 'true'
    gushim = db.gushim.find(fields={'gush_id': True, 'last_checked_at': True, '_id': False})
    if detailed:
        # Flatten list of gushim into a dict
        g_flat = dict((g['gush_id'], {"gush_id": g['gush_id'],
                                      "last_checked_at": g['last_checked_at'],
                                      "plan_stats": {}}) for g in gushim)
        # Get plan statistics from DB
        stats = db.plans.aggregate([
            {"$unwind" : "$gushim" },
            {"$project": {"gush_id": "$gushim", "status": "$status", "_id": 0}},
            {"$group": {"_id": {"gush_id": "$gush_id", "status": "$status"}, "count": {"$sum": 1}}}
        ])

        # Merge stats into gushim dict
        for g in stats['result']:
            try:
                gush_id = g['_id']['gush_id']
                status = g['_id']['status']
                g_flat[gush_id]['plan_stats'][status] = g['count']
            except KeyError, e:
                # Gush has plans but is missing from list of gushim?
                app.logger.warn("Gush #%d has plans but is not listed in the Gushim list", gush_id)
                app.log_exception(e)

        # De-flatten our dict
        gushim = g_flat.values()

    return _resp(list(gushim))


@app.route('/gush/<gush_id>.json')
def get_gush(gush_id):
    """
    get gush_id metadata
    """
    gush = db.gushim.find_one({"gush_id": gush_id})
    if gush is None:
        abort(404)
    return _resp(gush)


@app.route('/gush/<gush_id>/plans.json')
def get_plans(gush_id):
    """
    get plans from gush_id
    """
    if db.gushim.find_one({"gush_id": gush_id}) is None:
        abort(404)

    plans = db.plans.find({"gushim": gush_id}).sort(
        [("year", pymongo.DESCENDING), ("month", pymongo.DESCENDING), ("day", pymongo.DESCENDING)])

    return _resp(list(plans))


@app.route('/plans.atom')
def atom_feed():
    return _plans_query_to_atom_feed(request, limit=20, feed_title=u'תב״ע פתוחה - ירושלים').get_response()


@app.route('/gush/<gushim>/plans.atom')
def atom_feed_gush(gushim):
    """
    Create a feed for one or more gush IDs.
    The URL format for multiple gushim is something like /gush/12340,12350,12360/plans.atom
    """
    gushim = gushim.split(',')
    if len(gushim) > 1:
        query = {"gush_id": {"$in": gushim}}
    else:
        query = {"gush_id": gushim[0]}
    return _plans_query_to_atom_feed(request, query, feed_title=u'תב״ע פתוחה - ירושלים - גוש %s' % ', '.join(gushim)).get_response()


# TODO add some text on the project
@app.route('/')
def hello():
    return ('<html><body style="font-size: 3em; margin: 100px; text-align:center">'
            '<p>Hi. You\'ve reached the server side of <a href="http://opentaba.info">opentaba.info</a></p>'
            '<p><a href="https://github.com/niryariv/opentaba-server">Source</a></p>'
            '</body></html>')


@app.route('/wakeup')
def wakeup():
    """
    wake up Heroku dyno from idle. perhaps can if >1 dynos
    used as endpoint for a "wakeup" request when the client inits
    """
    return _resp({'morning': 'good'})


#### MAIN ####

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



