# -*- coding: utf-8 -*-

import requests
import logging
import os
from json import dumps

import helpers as helpers

log = logging.getLogger(__name__)


def post(plan):
    if 'SOCIAL_SERVICE_URL' in os.environ.keys():
        # generate a formatted plan
        post_data = {'plan': dumps(helpers._format_plan(plan), cls=helpers.DateTimeEncoder)}
        
        # if we have facebook posting settings, add them
        if 'FB_TOKEN' in os.environ.keys() and 'FB_PAGE_ID' in os.environ.keys():
            post_data['fb_tok'] = os.environ['FB_TOKEN']
            post_data['fb_page'] = os.environ['FB_PAGE_ID']
        
        # same for twitter settings
        if 'TW_TOKEN' in os.environ.keys() and 'TW_TOKEN_SECRET' in os.environ.keys() and 'TW_CONSUMER' in os.environ.keys() and 'TW_CONSUMER_SECRET' in os.environ.keys():
            post_data['tw_tok'] = os.environ['TW_TOKEN']
            post_data['tw_tsec'] = os.environ['TW_TOKEN_SECRET']
            post_data['tw_con'] = os.environ['TW_CONSUMER']
            post_data['tw_csec'] = os.environ['TW_CONSUMER_SECRET']
        
        # send data to social poster service. we just get an ok and continue, it's up to the service to take care of errors and such
        requests.post(os.environ['SOCIAL_SERVICE_URL'], data=post_data)
