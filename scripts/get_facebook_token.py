# -*- coding: utf-8 -*-

"""
Adapted from: http://stackoverflow.com/a/16743363
This script will run a small web server, redirect you to authorize the Taba Publisher facebook
app to manage_pages permission, extend the access token and print out your page tokens
"""

import web
from facepy import GraphAPI, utils
from urlparse import parse_qs

url = ('/', 'index')
    
app_id = '?'
app_secret = '?'
post_login_url = 'http://0.0.0.0:8080/'

class index:
    def GET(self):
        user_data = web.input(code=None)
        
        if not user_data.code:
            dialog_url = ('http://www.facebook.com/dialog/oauth?' +
                'client_id=' + app_id +
                '&redirect_uri=' + post_login_url +
                '&scope=manage_pages')

            return '<script>top.location.href="' + dialog_url + '"</script>'
        else:
            try:
                graph = GraphAPI()
                response = graph.get(
                    path='oauth/access_token',
                    client_id=app_id,
                    client_secret=app_secret,
                    redirect_uri=post_login_url,
                    code=user_data.code
                )
                data = parse_qs(response)
                
                extended_token = utils.get_extended_access_token(data['access_token'][0], app_id, app_secret)
                graph = GraphAPI(extended_token[0])
                accounts = graph.get(path = 'me/accounts')
                result = u'<!DOCTYPE html><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>'
                result += u'<body><table width="100%"><thead><td><b>Name</b></td><td><b>Id</b></td><td><b>Access Token</b></td></thead>'
                
                for entry in accounts['data']:
                    result += u'<tr><td>' + unicode(entry['name']) + u'</td><td>'
                    result += unicode(entry['id']) + u'</td><td>' + unicode(entry['access_token']) + u'</td></tr>'
                
                result += '</table></body></html>'
                return result
            except Exception, e:
                return 'Error: %s' % e
            

if __name__ == '__main__':
    print 'Please browse to this address to authorize Taba Publisher:'
    
    app = web.application(url, globals())
    app.run()
