"""
fab file for managing opentaba-server heroku apps
"""

from github import Github, Repository
from fabric.api import *
from getpass import getpass
from json import loads, dumps
import os
from copy import deepcopy

from common import _download_gush_map


@runs_once
def _github_connect():
    #  connect to github only once per run
    username = prompt('Github user: ')
    password = getpass('Github password: ')
    
    try:
        u = Github(username, password).get_user()
        
        # this is just so PyGithub tries to authorize now and not when someone actually wants
        # to do something like create or delete a repo
        i = u.id
    except:
        abort('Could not gain Github authorization')
    
    return u


@runs_once
def _get_repo_name(client_name):
    return 'opentaba-client-%s' % client_name


def _get_clients():
    # get the defined remotes' names, without 'origin' or 'all_sites'
    clients = ''.join(local('git remote', capture=True)).split('\n')
    if 'origin' in clients:
        clients.remove('origin')
    if 'all_sites' in clients:
        clients.remove('all_sites')
    if 'PhantomCSS' in clients:
        clients.remove('PhantomCSS')
    
    return clients


def _add_cname(client_name, client_git):
    # clone new repo in another directory
    with lcd('..'):
        local('git clone %s -b gh-pages tmp-%s' % (client_git, client_name))
        
        with lcd('tmp-%s' % client_name):
            # add CNAME
            local('echo %s.opentaba.info > CNAME' % client_name)
    
            # add, commit, push new CNAME
            local('git add CNAME')
            local('git commit -m "added CNAME - %s.opentaba.info"' % client_name)
            local('git push')
    
        # delete new repo folder
        local('rm -rf tmp-%s' % client_name)


def _get_muni_center(features):
    """
    Get the center point for the municipality - average longtitude and latitude values
    """
    
    sum_x = 0
    sum_y = 0
    count = 0
    
    for f in features:
        for cgroup in f['geometry']['coordinates']:
            for coord in cgroup:
                sum_x += coord[0]
                sum_y += coord[1]
                count += 1

    return [eval('{:.6f}'.format(sum_y / count)), eval('{:.6f}'.format(sum_x / count))]


@task
def create_client(client_name, display_name):
    """Create a new sub-site for a new municipality"""
    
    with lcd(os.path.join('..', 'opentaba-client')):
        g = _github_connect()
        repo_name = _get_repo_name(client_name)
        
        # start by adding the gushim to index.js
        update_gushim_client(client_name, display_name)
        
        # create a new repo for the new site
        try:
            repo = g.create_repo(repo_name, has_issues=False, has_wiki=False, has_downloads=False, auto_init=False)
        except:
            abort('Failed to create new github repository...')

        # add new repo as remote with the gh-pages branch as destination
        local('git remote add %s %s' % (client_name, repo.clone_url))
    
        # add new repo to all_sites remote
        with settings(warn_only=True):
            if local('git remote set-url --add all_sites %s' % repo.clone_url).failed:
                # in case just adding the the remote fails it probably doesn't exist yet, so try to add it
                if local('git remote add all_sites %s' % repo.clone_url).failed:
                    delete_client(client_name, ignore_errors=True)
                    abort('Could not add new remote to all_sites')
    
        # push to new remote
        deploy_client(client_name, repo.clone_url)
    
        print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
        print 'Now you need to manually add the new hostname (subdomain)'
        print 'to point to %s.opentaba.info' % client_name
        print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'


@task
def delete_client(client_name, ignore_errors=False):
    """Delete a sub-site"""
    
    with lcd(os.path.join('..', 'opentaba-client')):
        g = _github_connect()
        repo_name = _get_repo_name(client_name)
    
        with settings(warn_only=True):
            # try to find the site's git url if it is a remote here
            client_git = None
            remotes = ''.join(local('git remote -v', capture=True)).split('\n')
            for r in remotes:
                if r.startswith(client_name):
                    client_git = r.split('\t')[1].split(' ')[0]
                    break
        
            # delete the remotes for target site
            if client_git:
                local('git remote set-url --delete all_sites %s' % client_git, capture=ignore_errors)
        
            local('git remote remove %s' % client_name, capture=ignore_errors)
        
            # delete the github repository
            try:
                repo = g.get_repo(repo_name)
                repo.delete()
            except:
                if not ignore_errors:
                    abort('Failed to delete github repository...')


@task
def update_gushim_client(muni_name, display_name=''):
    """Add an entry for a new municipality or update an existing one to the data/index.js file with the required data"""
    
    with lcd(os.path.join('..', 'opentaba-client')):
        # download the online gush map
        geojson_gush_map = _download_gush_map(muni_name)
    
        # load the current municipalities' index dictionary
        with open(os.path.join('..', 'opentaba-client', 'data', 'index.js')) as index_data:
            original_index_json = loads(index_data.read().replace('var municipalities = ', '').rstrip('\n').rstrip(';'))
        
        new_index_json = deepcopy(original_index_json)
    
        # add a new entry if needed
        if muni_name not in new_index_json.keys():
            if display_name == '':
                abort('For new municipalities display name must be provided')
        
            new_index_json[muni_name] = {'display':'', 'center':[]}
    
        # update the display name and center of the municipality's entry
        new_index_json[muni_name]['display'] = display_name
        new_index_json[muni_name]['center'] = _get_muni_center(geojson_gush_map['features'])
        
        # don't try to add, commit etc. if no changes were made
        if dumps(new_index_json) != dumps(original_index_json):
            warn('No new data was found in the downloaded gush map. No changes were made to data/index.js')
        else:
            # write back the index.js file
            out = open(os.path.join('..', 'opentaba-client', 'data', 'index.js'), 'w')
            out.write('var municipalities = ' + dumps(new_index_json, sort_keys=True, indent=4, separators=(',', ': ')) + ';')
            out.flush()
            os.fsync(out.fileno())
            out.close()
    
            # commit and push to origin
            local('git add %s' % os.path.join('data', 'index.js'))
            local('git commit -m "added %s to index.js"' % muni_name)
            local('git push origin master')
            
            print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
            print 'The new/updated municipality data was added to data/index.js, and its topojson '
            print 'gushim map will be loaded from the israel_gushim repository, and changes were '
            print 'committed and pushed to origin. If more data needs to be in index.js, you can do '
            print 'it now and push again. If modified after app was created you will need to deploy '
            print 'the app again (explanation of valid fields in the index.js file can be found in '
            print 'the repository\'s DEPLOYMENT.md).'
            print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'


@task
def deploy_client(client_name, client_git=''):
    """Deploy changes to a certain sub-site"""
    
    with lcd(os.path.join('..', 'opentaba-client')):
        # this will in fact run over all current content of the remote and 
        # replace it with the active repo's master tree (--force), because 
        # otherwise the local CNAME of the remote will stop the push
        local('git push %s master:gh-pages --force' % client_name)
    
        if client_git == '':
            client_git = ''.join(local('git remote -v | grep ^%s | grep \(push\)$ | awk \'{print $2}\'' % client_name, capture=True))
    
        # re-add the CNAME file to the site
        _add_cname(client_name, client_git)


@task
def deploy_client_all():
    """Deploy changes to all sub-sites"""
    
    with lcd(os.path.join('..', 'opentaba-client')):
        # go over the remotes and deploy them, thus making sure to update the CNAME after destroying their data
        for client in _get_clients():
            deploy_client(client)
