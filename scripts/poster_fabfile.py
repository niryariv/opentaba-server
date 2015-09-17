"""
fab file for managing opentaba-poster heroku apps
"""

from urlparse import urlparse, parse_qs
import webbrowser
import socket
import md5

from fabric.api import *
from facepy import GraphAPI, utils
import oauth2 as oauth
import pymongo


def _authorize_get_response(url):
    """
    This is a one-request http server so we can synchronously wait and grab the response
    from Facebook \ Twitter after the user authorizes using a normal browser (user
    interaction is required)
    """
    
    # gonna use a simple socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # reuse if possible, and bind the socket to 0.0.0.0:8080
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 8080))
    except socket.error, msg:
        abort('Bind failed. Error Code : %s, Message : %s' % (str(msg[0]), msg[1]))
    
    # start listening, only 1 connection at at time (and at all)
    s.listen(1)
    s.settimeout(30)
    
    # open the authorization page so the user can interact and authorize the app if needed
    print 'About to open a new browser window or tab for authorization'
    print 'Please switch to it and authorize the permission request...'
    webbrowser.open_new(url)
    
    try:
        # wait for a connection, grab the data and send back a predefined response
        conn, addr = s.accept()
        data = conn.recv(4096)
        conn.sendall('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 47\r\nConnection: close\r\n\r\n<h1>Done with this window, please close it</h1>')
        conn.close()
    except socket.timeout:
        abort('No user authorization detected after 30 seconds')
    finally:
        # make sure the socket is closed
        s.close()
    
    # return a parsed query string from the request we got after authorization was successful
    return parse_qs(urlparse(data.split()[1]).query)


def _get_facebook_token(fb_app_id, fb_app_secret):
    # try to authenticate
    fb_auth = _authorize_get_response('http://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=http://0.0.0.0:8080/&scope=manage_pages' % fb_app_id)
    
    if 'code' not in fb_auth.keys():
        abort('Did not receive a token from Facebook! Did you decline authorization?')
    
    # get a short-term access token
    graph = GraphAPI()
    response = graph.get(
        path='oauth/access_token',
        client_id=fb_app_id,
        client_secret=fb_app_secret,
        redirect_uri='http://0.0.0.0:8080/',
        code=fb_auth['code'][0]
    )
    data = parse_qs(response)
    
    # extend the token
    extended_token = utils.get_extended_access_token(data['access_token'][0], fb_app_id, fb_app_secret)
    graph = GraphAPI(extended_token[0])
    
    # get the accounts associated with the token (list of pages managed by the user)
    pages = []
    accounts = graph.get(path = 'me/accounts')
    for entry in accounts['data']:
        pages.append({'value': {'page_id': unicode(entry['id']), 'token': unicode(entry['access_token'])}, 'display': '%s - %s' % (unicode(entry['id']), unicode(entry['name']))})
    
    # get the user's selected page
    selected_page = _get_user_choice('Select a page from your authorized ones: ', pages)
    if selected_page:
        return (selected_page['token'], selected_page['page_id'])
    else:
        return (None, None)


def _get_twitter_token(tw_con_id, tw_con_secret):
    # get a temp token
    oauth_consumer = oauth.Consumer(key=tw_con_id, secret=tw_con_secret)
    oauth_client = oauth.Client(oauth_consumer)
    resp, content = oauth_client.request('https://api.twitter.com/oauth/request_token', 'GET')
    
    if resp['status'] != '200':
        abort('Invalid response from Twitter requesting temp token: %s' % resp['status'])
    
    # have the user authorize our app
    request_token = parse_qs(content)
    tw_auth = _authorize_get_response('https://api.twitter.com/oauth/authorize?oauth_token=%s&oauth_callback=http://0.0.0.0:8080/' % request_token['oauth_token'][0])
    
    if 'oauth_token' not in tw_auth.keys():
        abort('Did not receive a token from Twitter! Did you decline authorization?')
    
    token = oauth.Token(tw_auth['oauth_token'][0], '')
    token.set_verifier(tw_auth['oauth_verifier'][0])
    
    # get the access token for posting tweets by the user
    oauth_consumer = oauth.Consumer(key=tw_con_id, secret=tw_con_secret)
    oauth_client = oauth.Client(oauth_consumer, token)
    resp, content = oauth_client.request('https://api.twitter.com/oauth/access_token', method='POST', body='oauth_callback=oob&oauth_verifier=%s' % tw_auth['oauth_verifier'][0])
    
    if resp['status'] != '200':
        abort('The request for a Twitter token did not succeed: %s' % resp['status'])
    
    access_token = parse_qs(content)
    return (access_token['oauth_token'][0], access_token['oauth_token_secret'][0])


def _get_user_choice(title, values):
    """Print a list of values and get the user's choice"""
    
    print title
    
    # print the value list
    for i in range(0, len(values)):
        print '%s: %s' % (i, values[i]['display'])
    
    # add an option to chose none of the values
    print '%s: None' % len(values)
    
    # get the user's choice
    choice = -1
    while choice not in range(0, len(values) + 1):
        try:
            choice = int(raw_input('Enter choice: '))
        except ValueError:
            print 'Please only enter integers from the given list!'
    
    # return it
    if choice == len(values):
        return None
    else:
        return values[choice]['value']


def _get_heroku_connection_string(app_name):
    """Get the connection string from environment variables on opentaba-poster app"""
    # this will either just show the user if connected or prompt for a connection
    # if a connection is not made it will error out and the fab process will stop
    local('heroku auth:whoami')
    
    # try mongolab first
    conn = local('heroku config:get MONGOHQ_URL --app %s' % app_name, capture=True)
    
    # if no mongolab, try mongohq
    if len(conn) == 0:
        conn = local('heroku config:get MONGOLAB_URI --app %s' % app_name, capture=True)
    
    return conn


@task
def add_new_poster(poster_app_name, poster_desc='', fb_app_id=None, fb_app_secret=None, tw_con_id=None, tw_con_secret=None):
    """Adds a new poster to the given app's db and returns its new id so it can be set on opentaba-server instances"""
    
    fb_token = None
    fb_page_id = None
    tw_token = None
    tw_secret = None
    
    # Facebook tokens
    if not (fb_app_id and fb_app_secret):
        print 'Warning: No Facebook page will be set, since app id and secret were not both provided'
    else:
        fb_token, fb_page_id = _get_facebook_token(fb_app_id, fb_app_secret)
        
    # Twitter tokens
    if not (tw_con_id and tw_con_secret):
        print 'Warning: No Twitter account will be set, since consumer id and secret were not both provided'
    else:
        tw_token, tw_secret = _get_twitter_token(tw_con_id, tw_con_secret)
    
    if not fb_token and not tw_token:
        print 'No social credentials provided or selected. Cancelling...'
        return None
    else:
        # get connection string and connect to poster's db
        db_connection_string = _get_heroku_connection_string(poster_app_name)
        conn = pymongo.MongoClient(db_connection_string)
        db = conn[urlparse(db_connection_string).path[1:]]
        
        # generate an md5 string of the first token available for id
        m = md5.new()
        
        if len(fb_token) > 0:
            m.update(fb_token)
        else:
            m.update(tw_token)
        
        poster_id = m.hexdigest()
        
        # make sure the id is unique. if it isn't, create an md5 string of itself and try again
        while db.posters.find_one({'id': poster_id}):
            m = md5.new()
            m.update(poster_id)
            poster_id = m.hexdigest()
        
        # build the new poster's document and insert it into the db
        new_poster = {'id': poster_id, 'desc': poster_desc}
        if fb_token and len(fb_token) > 0:
            new_poster['fb_tok'] = fb_token
            new_poster['fb_page'] = fb_page_id
        if tw_token and len(tw_token) > 0:
            new_poster['tw_tok'] = tw_token
            new_poster['tw_tsec'] = tw_secret
            new_poster['tw_con'] = tw_con_id
            new_poster['tw_csec'] = tw_con_secret
        db.posters.insert(new_poster)
        
        # close db connection
        conn.close()
        
        print 'Added new poster with id %s successfuly!' % poster_id
        return poster_id
