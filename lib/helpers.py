# -*- coding: utf-8 -*-

"""
Helpers for our web and worker (scraper) instances
"""

from flask import make_response
import json
from bson import json_util
import datetime
import pymongo

from conn import db
from taba_feed import TabaAtomFeed


def _get_plans(count=1000, query={}):
    return list(db.plans.find(query, limit=count).sort(
        [("year", pymongo.DESCENDING), ("month", pymongo.DESCENDING), ("day", pymongo.DESCENDING)]))


def _get_gushim(query={}, fields=None):
    return list(db.gushim.find(query, projection=fields))


def _get_plan_statistics():
    return db.plans.aggregate([
            {"$unwind" : "$gushim" },
            {"$project": {"gush_id": "$gushim", "status": "$status", "_id": 0}},
            {"$group": {"_id": {"gush_id": "$gush_id", "status": "$status"}, "count": {"$sum": 1}}}
        ])


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
    feed = TabaAtomFeed(feed_title, feed_url=request.url, url=request.url_root)

    for p in plans:
        formatted = _format_plan(p, request.url_root)

        feed.add(
            title=formatted['title'],
            content=formatted['content'],
            content_type='html',
            author="OpenTABA.info",
            # id=url + '&status=' + p['status'], 
            # ^^ it seems like the &tblView= value keeps changing in the URL, which causes the ID to change and dlvr.it to republish items.
            id="%s-%s" % (formatted['title'], p['status']),
            # this is a unique ID (not real URL) so adding status to ensure uniqueness in TBA stages
            url=formatted['url'],
            links=formatted['links'],
            updated=formatted['last_update'],
            published=formatted['last_update'],
            tags=formatted['gushim']
        )

    return feed


def _format_plan(plan, server_root=None):
    """
    Take a plan and format it for atom feed and social networks
    """
    formatted_plan = {}
    
    formatted_plan['url'] = plan['details_link']
        
    # special emphasizing for some statuses
    if plan['status'] in [u'פרסום ההפקדה', u'פרסום בעיתונות להפקדה']:
        formatted_plan['status'] = u'»»%s««' % plan['status']
    else:
        formatted_plan['status'] = plan['status']
    
    # the plan's content
    formatted_plan['content'] = plan['essence'] + ' [' + formatted_plan['status'] + ', ' + \
        '%02d/%02d/%04d' % (plan['day'], plan['month'], plan['year']) + ', ' + plan['number'] + ']'
    
    # the title
    formatted_plan['title'] = plan['location_string']
    # 'not title' is not supposed to happen anymore because every plan currently has a location
    if not formatted_plan['title']:
        formatted_plan['title'] = plan['number']
    
    # mavat link - if we have a code and the base url for this server (currently only from the atom feed) we can give a direct link
    # (through our server). otherwise link to the search page with parameters
    if plan['mavat_code'] == '' or server_root is None:
        formatted_plan['links'] = [{'href' : 'http://www.mavat.moin.gov.il/MavatPS/Forms/SV3.aspx?tid=4&tnumb=' + plan['number'], 'rel': 'related', 'title': u'מבא"ת'}]
    else:
        formatted_plan['links'] = [{'href': '%splan/%s/mavat' % (server_root, plan['plan_id']), 'rel': 'related', 'title': u'מבא"ת'}]
    
    # plan last update
    formatted_plan['last_update'] = datetime.date(plan['year'], plan['month'], plan['day'])
    
    # gushim list to be used as tags
    formatted_plan['gushim'] = plan['gushim']
    
    return formatted_plan


"""
A small class to enable json-serializing of datetime.date objects
To use it: json.dumps(json_object, cls=helpers.DateTimeEncoder)
"""
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
       if hasattr(obj, 'isoformat'):
           return obj.isoformat()
       else:
           return json.JSONEncoder.default(self, obj)
