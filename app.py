# -*- coding: utf-8 -*-
#!/usr/bin/python

import os
import datetime
import json
from bson import json_util
from urlparse import urlparse
from functools import wraps
import email.utils
from time import time

from werkzeug.contrib.atom import AtomFeed
from werkzeug.contrib.cache import MemcachedCache, NullCache
from werkzeug.urls import url_encode

from flask import Flask
from flask import abort, make_response, request

from pylibmc import Client

from tools.conn import *
from tools.gushim import GUSHIM

app = Flask(__name__)
app.debug = RUNNING_LOCAL # if we're local, keep debug on

# cache connection retry data
MAX_CACHE_RETRIES = 3
app.cache_retry = 0


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
        
        # special emphasizing for some statuses
        if p['status'] in [u'פרסום ההפקדה', u'פרסום בעיתונות להפקדה']:
            status = u'»»%s««' % p['status']
        else:
            status = p['status']
        
        content = p['essence'] + ' [' + status + ', ' + '%02d/%02d/%04d' % (p['day'], p['month'], p['year']) + \
            ', ' + p['number'] + '] (http://www.mavat.moin.gov.il/MavatPS/Forms/SV3.aspx?tid=4&tnumb=' + p['number'] + ')'
        title = p['location_string']
        # 'not title' is not supposed to happen anymore because every plan currently has a location
        if not title:
            title = p['number']
        
        links = [{'href' : 'http://www.mavat.moin.gov.il/MavatPS/Forms/SV3.aspx?tid=4&tnumb=' + p['number'], 'rel': 'related', 'title': u'מבא"ת'}]

        feed.add(
            title=title,
            content=content,
            content_type='html',
            author="OpenTABA.info",
            id=url + '&status=' + p['status'],
            # this is a unique ID (not real URL) so adding status to ensure uniqueness in TBA stages
            url=url,
            links=links,
            updated=datetime.date(p['year'], p['month'], p['day'])
        )

    return feed


#### Cache ####

@app.before_first_request
def setup_cache():
    """
    We initialize the cache here for the first time because __main__ is not run when we launch
    within a WSGI container.
    """
    _setup_cache()


def _setup_cache():
    """
    If a test is being run or we don't want cache, NullCache will be initialized just as a dummy.
    If running locally without the 'DISABLE_CACHE' env variable and without a memcached instance running,
    MemcachedCache and it's underlying pylibmc will give no warning on connection, but will throw
    exceptions when trying to work with the cache. A few connection retires will be made in that
    scenario, and eventually the cache will be replaced with a NullCache. Binary communications must
    be used for SASL.
    """
    # Setup cache
    if app.config['TESTING'] or os.environ.get('DISABLE_CACHE', None) is not None:
        app.cache = NullCache()
        app.logger.debug('Cache initialized as NullCache')
    else:
        MEMCACHED_SERVERS = os.environ.get('MEMCACHEDCLOUD_SERVERS', '127.0.0.1:11211')
        
        try:
            memcached_client = Client(servers=MEMCACHED_SERVERS.split(','),
                                      username=os.environ.get('MEMCACHEDCLOUD_USERNAME'),
                                      password=os.environ.get('MEMCACHEDCLOUD_PASSWORD'),
                                      binary=True)
            app.cache = MemcachedCache(memcached_client)
            app.logger.debug('Cache initialized as MemcachedCache with servers: %s', MEMCACHED_SERVERS)
        except Exception as e:
            # very unlikely to have an exception here. pylibmc mostly throws when trying to communicate, not connect
            app.logger.error('Error initializing MemcachedCache: %s', e);
            app.logger.error('Initializing cache as NullCache. Fix ASAP!');
            app.cache = NullCache()


def cached(timeout=3600, cache_key=None, set_expires=True):
    """
    Caching decorator for Flask routes

    Provides both caching and setting of relevant "Expires" header if appropriate.
    Adapted from http://flask.pocoo.org/docs/patterns/viewdecorators/
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if cache_key is None:
                ck = 'view:%s?%s' % (request.path, request.query_string)
            else:
                ck = cache_key
            ek = '%s.expires' % ck
            response = None
            expires = None
            
            # pylibmc will throw an error when trying to communicate with memcached, not upon a bad connection
            try:
                cached = app.cache.get_many(ck, ek)
                if cached[0] is not None:
                    response = cached[0]
                    app.logger.debug('Cache hit for %s, returning cached content, expires=%d', ck, cached[1])
                    if cached[1] is not None and set_expires:
                        expires = cached[1]
                else:
                    response = f(*args, **kwargs)
                    expires = int(time() + timeout)
                    app.cache.set_many({ck: response, ek: expires}, timeout=timeout)
                    app.logger.debug('Cache miss for %s, refreshed content and saved in cache, expires=%d', ck, expires)

                if set_expires and expires is not None:
                    response.headers['Expires'] = email.utils.formatdate(expires)
            except Exception as e:
                app.logger.error('Cache error, returning miss: %s', e)
                if response is None:
                    response = f(*args, **kwargs)
                
                if (type(app.cache) is not NullCache):
                    if (app.cache_retry < MAX_CACHE_RETRIES):
                        app.cache_retry += 1
                        app.logger.error('Attempting to restore cache')
                        _setup_cache()
                    else:
                        app.logger.error('Exhausted retry attempts. Converting cache to NullCache. Fix ASAP!')
                        app.cache = NullCache()

            return response

        return decorated_function

    return decorator


#### ROUTES ####

@app.route('/gushim.json')
@cached(timeout=3600)
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
@cached(timeout=3600)
def get_gush(gush_id):
    """
    get gush_id metadata
    """
    gush = db.gushim.find_one({"gush_id": gush_id})
    if gush is None:
        abort(404)
    return _resp(gush)


@app.route('/gush/<gush_id>/plans.json')
@cached(timeout=3600)
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
@cached(timeout=3600)
def atom_feed():
    return _plans_query_to_atom_feed(request, limit=20, feed_title=u'תב״ע פתוחה').get_response()


@app.route('/<city>/plans.atom')
def atom_feed_city(city):
    if city not in GUSHIM.keys():
        abort(404)
    
    if len(GUSHIM[city]['list']) > 1:
        query = {'gushim': {'$in': GUSHIM[city]['list']}}
    else:
        query = {'gushim': GUSHIM[city]['list'][0]}
    return _plans_query_to_atom_feed(request, query, limit=20, feed_title=u'תב״ע פתוחה - ' + GUSHIM[city]['display'].decode('unicode-escape')).get_response()


@app.route('/gush/<gushim>/plans.atom')
@cached(timeout=3600)
def atom_feed_gush(gushim):
    """
    Create a feed for one or more gush IDs.
    The URL format for multiple gushim is something like /gush/12340,12350,12360/plans.atom
    """
    gushim = gushim.split(',')
    if len(gushim) > 1:
        query = {'gushim': {'$in': gushim}}
    else:
        query = {'gushim': gushim[0]}
    return _plans_query_to_atom_feed(request, query, feed_title=u'תב״ע פתוחה - גוש %s' % ', '.join(gushim)).get_response()


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
