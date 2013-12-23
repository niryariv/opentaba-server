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


#### ROUTES ####

@app.route('/gushim.json')
def get_gushim():
    """
    get gush_id metadata
    """
    gushim = db.gushim.find(fields={'gush_id': True, '_id': False})
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

    plans = db.plans.find({"gush_id": gush_id}).sort(
        [("year", pymongo.DESCENDING), ("month", pymongo.DESCENDING), ("day", pymongo.DESCENDING)])

    # eliminate plans which appear in >99 blocks - cover for MMI's database bugs
    blacklist = db.blacklist.find_one()['blacklist']

    plans_clean = [p for p in list(plans) if p['number'] not in blacklist]

    return _resp(plans_clean)


@app.route('/feed.atom')
def atom_feed():
    feed = AtomFeed("OpenTABA", feed_url=request.url, url=request.url_root)

    plans = db.plans.find(limit=2000).sort(
        [("year", pymongo.DESCENDING), ("month", pymongo.DESCENDING), ("day", pymongo.DESCENDING)])

    blacklist = db.blacklist.find_one()['blacklist']
    plans_clean = [p for p in list(plans) if p['number'] not in blacklist]

    for p in plans_clean:
        url = 'http://mmi.gov.il/IturTabot/taba4.asp?' + url_encode({'kod': 3000, 'MsTochnit': p['number']},
                                                                    charset='windows-1255')

        content = p['status'] + p['number']
        title = p['essence']
        if not title:
            title = content
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

    return feed.get_response()


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
    wake up heroku dyno from idle. perhaps can if >1 dynos
    used as endpoint for a "wakeup" request when the client inits
    """
    return _resp({'morning': 'good'})


#### MAIN ####

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



