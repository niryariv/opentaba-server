"""
fab file for managing opentaba-server heroku apps
"""

from fabric.api import *
from json import loads, dumps
import re
import os

from common import _download_gush_map


@runs_once
def _heroku_connect():
    # this will either just show the user if connected or prompt for a connection
    # if a connection is not made it will error out and the fab process will stop
    local('heroku auth:whoami')


def _get_server_full_name(muni_name):
    return 'opentaba-server-%s' % muni_name


def _is_server_full_name(name):
    return name.startswith('opentaba-server-')


def _get_muni_name(server_full_name):
    if _is_server_full_name(server_full_name):
        return server_full_name[16:]
    
    return ''


def _get_servers():
    _heroku_connect()
    
    # get all current user's heroku apps, and return a list of the ones who match a server's name
    apps = ''.join(local('heroku list', capture=True)).split('\n')
    
    # filter out the not-servers
    apps = [app for app in apps if _is_server_full_name(app)]
    
    return apps


@task
def create_server(muni_name, display_name):
    """Create a new heroku app for a new municipality"""
    
    _heroku_connect()
    full_name = _get_server_full_name(muni_name)
    
    # start by adding the gushim to gushim.py
    update_gushim_server(muni_name)
    
    # create a new heroku app with the needed addons
    local('heroku apps:create %s --addons scheduler:standard,memcachedcloud:30,mongolab:sandbox,rediscloud:30' % full_name)
    
    # set the server's display name
    local('heroku config:set MUNICIPALITY_NAME="%s" --app %s' % (display_name, full_name))
    
    # push code to the new app and create db and scrape for the first time
    deploy_server(muni_name)
    renew_db(muni_name)
    
    # add scheduled job - can't be done automatically
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
    print 'You must add a new scheduled job now to scrape data during every night'
    print 'This cannot be done automatically, but it\'s not hard. Just click "Add Job..."'
    print 'Command is: '
    print '     python scrape.py -g all ; python worker.py'
    print '1X dyno, daily frequency, next run 04:00'
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
    local('heroku addons:open scheduler --app %s' % full_name)
    
    # wait for user to finish
    raw_input('Press enter for next step...')
    
    # set rediscloud's data eviction policy to "allkeys lru"
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
    print 'You must now change RedisCloud\'s configuration for our jobs to be queued'
    print 'and flushed properly. Click on the Redis instance (the top one), then hit the'
    print '"Edit" button on the bottom of the page. Change the data eviction policy to'
    print '"allkeys lru", and finally hit "Update".'
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
    local('heroku addons:open rediscloud --app %s' % full_name)


@task
def delete_server(muni_name, ignore_errors=False):
    """Delete a heroku app"""
    
    _heroku_connect()
    full_name = _get_server_full_name(muni_name)
    
    with settings(warn_only=True):
        # delete heroku app
        local('heroku apps:destroy --app %s --confirm %s' % (full_name, full_name), capture=ignore_errors)


@task
def update_gushim_server(muni_name):
    """Add the gush ids from an existing online gush map to the lib/gushim.py file"""
    
    # download the online gush map
    gush_map = _download_gush_map(muni_name)
    gush_ids = []
    
    # make a list of all gush ids in the file
    for geometry in gush_map['features']:
        gush_ids.append(geometry['properties']['Name'])
    
    # make sure we're using the master branch
    local('git checkout master')
    
    # open and load the existing gushim dictionary from lib/gushim.py
    with open(os.path.join('lib', 'gushim.py')) as gushim_data:
        existing_gushim = loads(gushim_data.read().replace('GUSHIM = ', ''))
    
    # if the municipality already exists replace it's list, otherwise create a new one
    existing_gushim[muni_name] = {'list': gush_ids}
    
    # write the dictionary back to lib/gushim.py
    out = open(os.path.join('lib', 'gushim.py'), 'w')
    out.write('GUSHIM = ' + dumps(existing_gushim, sort_keys=True, indent=4, separators=(',', ': ')))
    out.flush()
    os.fsync(out.fileno())
    out.close()
    
    # update the automated test to test for the new total number of gushim
    total = []
    for key in existing_gushim.keys():
        for g in existing_gushim[key]['list']:
            if g not in total:
                total.append(g)
    
    with open(os.path.join('Tests', 'functional_tests', 'test_return_json.py')) as test_data:
        test_code = test_data.read()
        gush_count_line_re = re.compile('(eq_\(len\(j\), )[0-9]+(\))')
        test_code = gush_count_line_re.sub('eq_(len(j), %s)' % len(total), test_code, count=1)
    
    out = open(os.path.join('Tests', 'functional_tests', 'test_return_json.py'), 'w')
    out.write(test_code)
    out.flush()
    os.fsync(out.fileno())
    out.close()
    
    # commit and push to origin
    local('git add %s' % os.path.join('lib', 'gushim.py'))
    local('git add %s' % os.path.join('Tests', 'functional_tests', 'test_return_json.py'))
    local('git commit -m "added gushim and updated tests for %s"' % muni_name)
    local('git push origin master')
    
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
    print 'The new/updated gushim data was added to lib/gushim.py and the test file '
    print 'Tests/functional_tests/test_return_json.py was updated.'
    print 'Both files were successfuly comitted and pushed to origin.'
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'


@task
def deploy_server(muni_name):
    """Deploy changes to a certain heroku app"""
    
    print 'Deploying app: %s' % _get_server_full_name(muni_name)
    local('git push git@heroku.com:%s.git master' % _get_server_full_name(muni_name))


@task
def deploy_server_all():
    """Deploy changes to all heroku apps"""
    
    for server in _get_servers():
        print 'Deploying app: %s...' % server
        local('git push git@heroku.com:%s.git master' % server)


@task
def create_db(muni_name):
    """Run the create_db script file on a certain heroku app"""
    
    _heroku_connect()
    
    local('heroku run "python scripts/create_db.py --force -m %s" --app %s' % (muni_name, _get_server_full_name(muni_name)))


@task
def update_db(muni_name):
    """Run the update_db script file on a certain heroku app"""
    
    _heroku_connect()
    
    local('heroku run "python scripts/update_db.py --force -m %s" --app %s' % (muni_name, _get_server_full_name(muni_name)))


@task
def scrape(muni_name, show_output=False):
    """Scrape all gushim on a certain heroku app"""
    
    _heroku_connect()
    full_name = _get_server_full_name(muni_name)
    
    if show_output:
        local('heroku run "python scrape.py -g all; python worker.py" --app %s' % full_name)
    else:
        local('heroku run:detached "python scrape.py -g all; python worker.py" --app %s' % full_name)


@task
def renew_db(muni_name):
    """Run the create_db script file and scrape all gushim on a certain heroku app"""
    
    create_db(muni_name)
    scrape(muni_name)


@task
def renew_db_all():
    """Run the create_db script file and scrape all gushim on all heroku apps"""
    
    for server in _get_servers():
        renew_db(_get_muni_name(server))


@task
def refresh_db(muni_name):
    """Run the update_db script file and scrape all gushim on a certain heroku app"""
    
    update_db(muni_name)
    scrape(muni_name)


@task
def refresh_db_all():
    """Run the update_db script file and scrape all gushim on all heroku apps"""
    
    for server in _get_servers():
        refresh_db(_get_muni_name(server))

@task
def set_poster(muni_name, poster_base_url, poster_id):
    """
    Set the necessary environment variables on the app so it can communicate with
    an opentaba-poster instance for social posting
    """
    
    _heroku_connect()
    full_name = _get_server_full_name(muni_name)
    
    local('heroku config:set POSTER_SERVICE_URL="%s" --app %s' % (poster_base_url, full_name))
    local('heroku config:set POSTER_ID="%s" --app %s' % (poster_id, full_name))

@task
def sync_poster(muni_name, min_date):
    """Run the sync_poster script file on a certain heroku app"""
    
    _heroku_connect()
    
    local('heroku run "python scripts/sync_date.py -m %s -q" --app %s' % (min_date, _get_server_full_name(muni_name)))
