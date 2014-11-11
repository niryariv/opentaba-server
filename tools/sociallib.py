# -*- coding: utf-8 -*-

import bitly_api
from facepy import GraphAPI
from twitter import *
import logging
import os

log = logging.getLogger(__name__)


def post(plan):
    # generate title and content for posts
    title = plan['location_string']
    # 'not title' is not supposed to happen anymore because every plan currently has a location
    if not title:
        title = plan['number']
        
    # special emphasizing for some statuses
    if plan['status'] in [u'פרסום ההפקדה', u'פרסום בעיתונות להפקדה']:
        status = u'»»%s««' % plan['status']
    else:
        status = plan['status']
    
    content = plan['essence'] + ' [' + status + ', ' + '%02d/%02d/%04d' % (plan['day'], plan['month'], plan['year']) + \
        ', ' + plan['number'] + ']'
    
    # if bitly access token is defined shorten the link
    if 'BITLY_TOKEN' in os.environ.keys():
        try:
            b = bitly_api.Connection(access_token=os.environ['BITLY_TOKEN'])
            shortie = b.shorten(plan['details_link'])
            url = shortie['url']
        except Exception, e:
            log.exception('Could not shorten the link using bit.ly - %s', e)
            url = plan['details_link']
    else:
        url = plan['details_link']
    
    # post to facebook page
    if 'FB_TOKEN' in os.environ.keys() and 'FB_PAGE_ID' in os.environ.keys():
        try:
            graph = GraphAPI(os.environ['FB_TOKEN'])
            graph.post(
                path = 'v2.2/%s/feed' % os.environ['FB_PAGE_ID'],
                message = '%s: %s %s' % (title, content, url),
                retry = 10
            )
        except Exception, e:
            log.exception('Could not post new plan to facebook page - %s', e)
    
    # post to twitter feed
    if 'TW_TOKEN' in os.environ.keys() and 'TW_TOKEN_SECRET' in os.environ.keys() and 'TW_CONSUMER' in os.environ.keys() and 'TW_CONSUMER_SECRET' in os.environ.keys():
        try:
            tweet_content = '%s: %s' % (title, content)
            
            # shorten our content - max size should be 118, not including the link which will be shortened by twitter if bit.ly is not enabled
            if len(tweet_content) > 118:
                tweet = '%s... %s' % (tweet_content[0:114], url)
            else:
                tweet = '%s %s' % (tweet_content, url)
            
            t = Twitter(auth=OAuth(consumer_key=os.environ['TW_CONSUMER'], consumer_secret=os.environ['TW_CONSUMER_SECRET'], token=os.environ['TW_TOKEN'], token_secret=os.environ['TW_TOKEN_SECRET']))
            t.statuses.update(status=tweet)
        except Exception, e:
            log.exception('Could not post new plan to twitter feed - %s', e)
