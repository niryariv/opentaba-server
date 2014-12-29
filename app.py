# -*- coding: utf-8 -*-
#!/usr/bin/python

import os
import datetime
import json
from bson import json_util

from werkzeug.contrib.atom import AtomFeed
from werkzeug.urls import url_encode

from flask import Flask
from flask import abort, make_response, request

from tools.conn import *
from tools.gushim import GUSHIM
from tools.cache import cached, _setup_cache

app = Flask(__name__)
app.debug = RUNNING_LOCAL # if we're local, keep debug on


#### Helpers ####

def _get_plans(count=1000, query={}):
    return list(db.plans.find(query, limit=count).sort(
        [("year", pymongo.DESCENDING), ("month", pymongo.DESCENDING), ("day", pymongo.DESCENDING)]))


def _get_gushim(query={}, fields=None):
    return list(db.gushim.find(query, fields=fields))


def _create_response_json(data):
    """
    Convert dictionary to JSON. json_util.default adds automatic mongoDB result support
    """
    r = make_response(json.dumps(data, ensure_ascii=False, default=json_util.default))
    r.headers['Access-Control-Allow-Origin'] = "*"
    r.headers['Content-Type'] = "application/json; charset=utf-8"
    return r


def _create_response_atom_feed(request, plans, feed_title=''):
    """
    Create an atom feed of plans fetched from the DB based on an optional query
    """
    feed = AtomFeed(feed_title, feed_url=request.url, url=request.url_root)

    for p in plans:
        url = p['details_link']
        
        # special emphasizing for some statuses
        if p['status'] in [u'פרסום ההפקדה', u'פרסום בעיתונות להפקדה']:
            status = u'»»%s««' % p['status']
        else:
            status = p['status']
        
        content = p['essence'] + ' [' + status + ', ' + '%02d/%02d/%04d' % (p['day'], p['month'], p['year']) + \
            ', ' + p['number'] + ']'
        title = p['location_string']
        # 'not title' is not supposed to happen anymore because every plan currently has a location
        if not title:
            title = p['number']
        
        if p['mavat_code'] == '':
            links = [{'href' : 'http://www.mavat.moin.gov.il/MavatPS/Forms/SV3.aspx?tid=4&tnumb=' + p['number'], 'rel': 'related', 'title': u'מבא"ת'}]
        else:
            links = [{'href': '%splan/%s/mavat' % (request.url_root, p['plan_id']), 'rel': 'related', 'title': u'מבא"ת'}]

        feed.add(
            title=title,
            content=content,
            content_type='html',
            author="OpenTABA.info",
            # id=url + '&status=' + p['status'], 
            # ^^ it seems like the &tblView= value keeps changing in the URL, which causes the ID to change and dlvr.it to republish items.
            id="%s-%s" % (title, p['status']),
            # this is a unique ID (not real URL) so adding status to ensure uniqueness in TBA stages
            url=url,
            links=links,
            updated=datetime.date(p['year'], p['month'], p['day'])
        )

    return feed


#### Cache Helper ####

@app.before_first_request
def setup_cache():
    """
    We initialize the cache here for the first time because __main__ is not run when we launch
    within a WSGI container.
    """
    _setup_cache(app)


#### ROUTES ####

@app.route('/gushim.json')
@cached(app, timeout=3600)
def get_gushim():
    """
    get gush_id metadata
    """
    detailed = request.args.get('detailed', '') == 'true'
    gushim = _get_gushim(fields={'gush_id': True, 'last_checked_at': True, '_id': False})
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

    return _create_response_json(gushim)


@app.route('/gush/<gush_id>.json')
@cached(app, timeout=3600)
def get_gush(gush_id):
    """
    get gush_id metadata
    """
    gush = _get_gushim(query={"gush_id": gush_id})
    if gush is None or len(gush) == 0:
        abort(404)
    return _create_response_json(gush[0])


@app.route('/gush/<gushim>/plans.json')
@cached(app, timeout=3600)
def get_plans(gushim):
    """
    Get JSON plan data for one or more gush IDs.
    The URL format for multiple gushim is something like /gush/12340,12350,12360/plans.json
    """
    gushim = gushim.split(',')
    if len(gushim) > 1:
        gushim_query = {'gushim': {'$in': gushim}}
    else:
        gushim_query = {'gushim': gushim[0]}

    return _create_response_json(_get_plans(query=gushim_query))


@app.route('/recent.json')
@cached(app, timeout=3600)
def get_recent_plans():
    """
    Get the 10 most recent plans to show on the site's home page
    """
    return _create_response_json(_get_plans(count=10))


@app.route('/plans.atom')
@cached(app, timeout=3600)
def atom_feed():
    if 'MUNICIPALITY_NAME' in os.environ.keys():
        title = u'תב"ע פתוחה - %s' % os.environ['MUNICIPALITY_NAME'].decode('utf-8')
    else:
        title = u'תב"ע פתוחה'
    
    return _create_response_atom_feed(request, _get_plans(count=20), feed_title=title).get_response()


@app.route('/gush/<gushim>/plans.atom')
@cached(app, timeout=3600)
def atom_feed_gush(gushim):
    """
    Create a feed for one or more gush IDs.
    The URL format for multiple gushim is something like /gush/12340,12350,12360/plans.atom
    """
    gushim = gushim.split(',')
    if len(gushim) > 1:
        gushim_query = {'gushim': {'$in': gushim}}
    else:
        gushim_query = {'gushim': gushim[0]}
    
    return _create_response_atom_feed(request, _get_plans(query=gushim_query), feed_title=u'תב״ע פתוחה - גוש %s' % ', '.join(gushim)).get_response()


@app.route('/plans/search/<path:plan_name>')
@cached(app, timeout=3600)
def find_plan(plan_name):
    """
    Find plans that contain the search query and return a json array of their plan and gush ids
    """
    return _create_response_json(_get_plans(count=3, query={'number': {'$regex': '.*%s.*' % plan_name}}))


@app.route('/plan/<plan_id>/mavat')
@cached(app, timeout=3600)
def redirect_to_mavat(plan_id):
    """
    If we have a mavat code for the given plan redirect the client to the plan's page on the
    mavat website using an auto-sending form
    """
    try: 
        plans = _get_plans(count=1, query={'plan_id': int(plan_id)})
    except ValueError: # plan_id is not an int
        abort(400)
    except: # DB error
        abort(500)
    
    if plans is None or len(plans) == 0 or plans[0]['mavat_code'] == '':
        abort(404)
    
    return ('<html><body>'
            '<form action="http://mavat.moin.gov.il/MavatPS/Forms/SV4.aspx?tid=4" method="post" name="redirect_form">'
            '<input type="hidden" name="PL_ID" value="' + plans[0]['mavat_code'] + '">'
            '</form><script language="javascript">document.redirect_form.submit();</script></body></html>')


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
    return _create_response_json({'morning': 'good'})


#### MAIN ####

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
