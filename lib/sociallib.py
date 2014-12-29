# -*- coding: utf-8 -*-

import requests
import logging
import os
from json import dumps

import helpers as helpers

log = logging.getLogger(__name__)


def post(plan):
    if all(param in os.environ.keys() for param in ['POSTER_SERVICE_URL', 'POSTER_ID']):
        # generate a formatted plan and the post data
        formatted_plan = helpers._format_plan(plan)
        post_data = {'poster_id': os.environ['POSTER_ID'], 'title': formatted_plan['title'], 'content': formatted_plan['content'], 'url': formatted_plan['url']}
        
        # send data to social poster service. we just get an ok and continue, it's up to the service to take care of errors and such
        requests.post(os.environ['POSTER_SERVICE_URL'], data=post_data)
