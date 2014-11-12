# -*- coding: utf-8 -*-

"""
Build using code from: https://code.google.com/p/python-twitter/source/browse/get_access_token.py
Copyright 2007 The Python-Twitter Developers , licensed under the Apache License, Version 2.0

This script will run a small web server, redirect you to authorize the Taba Publisher twitter
app to your account and print out your access token and secret
"""

import os
from urlparse import parse_qsl
import oauth2 as oauth
import web
from facepy import GraphAPI, utils
from urlparse import parse_qs

consumer_key    = ''
consumer_secret = ''


class index:
    def GET(self):
        user_data = web.input(oauth_token=None, oauth_verifier=None)
        
        if not user_data.oauth_token:
            oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
            oauth_client = oauth.Client(oauth_consumer)
            resp, content = oauth_client.request('https://api.twitter.com/oauth/request_token', 'GET')
            
            if resp['status'] != '200':
                return 'Invalid respond from Twitter requesting temp token: %s' % resp['status']
            else:
                request_token = dict(parse_qsl(content))
                
                auth_url = ('https://api.twitter.com/oauth/authorize?' +
                    'oauth_token=' + request_token['oauth_token'] +
                    '&oauth_callback=http://0.0.0.0:8080/')

                return '<script>top.location.href="' + auth_url + '"</script>'
        else:
            token = oauth.Token(user_data.oauth_token, '')
            token.set_verifier(user_data.oauth_verifier)
            
            oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
            oauth_client  = oauth.Client(oauth_consumer, token)
            resp, content = oauth_client.request('https://api.twitter.com/oauth/access_token', method='POST', body='oauth_callback=oob&oauth_verifier=%s' % user_data.oauth_verifier)
            access_token  = dict(parse_qsl(content))

            if resp['status'] != '200':
                return 'The request for a Token did not succeed: %s' % resp['status']
            else:
                result = u'<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>'
                result += u'<body><b>Access Token: </b>' + access_token['oauth_token']
                result += u'<br><b>Access Token Secret: </b>' + access_token['oauth_token_secret']
                result += u'</body></html>'
                return result


if __name__ == '__main__':
    if consumer_key == '' or consumer_secret == '':
        print 'Variables consumer_key and consumer_secret must be set to your Twitter app\'s values'
        print 'Also, "http://0.0.0.0:8080" has to be set as a valid callback URL in your app\'s settings'
    else:
        print 'Please browse to this address to authorize Taba Publisher:'
        app = web.application(('/', 'index'), globals())
        app.run()
