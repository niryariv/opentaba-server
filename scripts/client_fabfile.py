"""
fab file for managing opentaba-server heroku apps
"""

from fabric.api import *
from json import loads, dumps
import os
from copy import deepcopy
from github import Repository

from common import _download_gush_map, _github_connect


@runs_once
def _get_repo_name(client_name):
    return 'opentaba-client-%s' % client_name


def _is_repo_name(name):
    return name.startswith('opentaba-client-%s')


def _get_muni_from_repo_name(repo_name):
    return repo_name[16:]


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


def _get_muni_bounds(features):
    """
    Get the bounds for the municipality - south-west point and north-east point
    """
    
    min_x = 180
    max_x = -180
    min_y = 180
    max_y = -180
    
    for f in features:
        for cgroup in f['geometry']['coordinates']:
            for coord in cgroup:
                if coord[0] < min_x:
                    min_x = coord[0]
                if coord[0] > max_x:
                    max_x = coord[0]
                
                if coord[1] < min_y:
                    min_y = coord[1]
                if coord[1] > max_y:
                    max_y = coord[1]

    return [[eval('{:.6f}'.format(min_y)), eval('{:.6f}'.format(min_x))], [eval('{:.6f}'.format(max_y)), eval('{:.6f}'.format(max_x))]]


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
        
        # make sure we're using the master branch
        local('git checkout master')
    
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
        new_index_json[muni_name]['bounds'] = _get_muni_bounds(geojson_gush_map['features'])
        
        # don't try to add, commit etc. if no changes were made
        if dumps(new_index_json, sort_keys=True) == dumps(original_index_json, sort_keys=True):
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
            print 'The new/updated municipality data was added to data/index.js, its topojson '
            print 'gushim map will be loaded from the israel_gushim repository, and changes were '
            print 'committed and pushed to origin. If more data needs to be in index.js, you can '
            print 'do it now and push again. If using full copy methodology (not dummy) and '
            print 'modifying the file after app was created you will need to deploy the app again '
            print '(explanation of valid fields in the index.js file can be found in the client '
            print 'repository\'s DEPLOYMENT.md'
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


@task
def create_client_pull(muni_name, display_name):
    """Create a new opentaba-client copy, to be updated using a local copy and pull"""
    
    # first time running the pull task - create the 'municipalities' directory
    if not os.path.exists(os.path.join('..', 'municipalities')):
        os.makedirs(os.path.join('..', 'municipalities'))
    
    repo_name = _get_repo_name(muni_name)
    
    # make sure a local repository of the municipality doesn't exist yet
    # if it does the user did something weird and should review stuff and fix
    if os.path.exists(os.path.join('..', 'municipalities', repo_name)):
        abort('%s seems to already exist... (at least locally)' % repo_name)
    else:
        with lcd(os.path.join('..', 'municipalities')):
            g = _github_connect()
            
            # start by adding the gushim to index.js
            update_gushim_client(muni_name, display_name)
            
            # create a new repository for the new municipality
            try:
                repo = g.create_repo(repo_name, has_issues=False, has_wiki=False, has_downloads=False, auto_init=False)
            except:
                abort('Failed to create new github repository...')
            
            # clone the new repository
            local('git clone %s' % repo.ssh_url)
            
            with lcd(repo_name):
                # add core as remote and fetch from master to gh-pages
                local('git remote add upstream https://github.com/niryariv/opentaba-client.git')
                local('git fetch upstream master:gh-pages')
                local('git checkout gh-pages')
                
                # add CNAME
                local('echo %s.opentaba.info > CNAME' % muni_name)
                
                # add, commit, push new CNAME
                local('git add CNAME')
                local('git add index.html')
                local('git commit -m "personalized for %s"' % muni_name)
                local('git push origin gh-pages')
            
        print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
        print 'Now you need to manually add the new hostname (subdomain)'
        print 'to point to %s.opentaba.info' % muni_name
        print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'


@task
def delete_client_pull(muni_name, ignore_errors=False):
    """Delete a municipality's client repository"""
    
    g = _github_connect()
    repo_name = _get_repo_name(muni_name)
    
    with settings(warn_only=True):
        # delete the github repository
        try:
            repo = g.get_repo(repo_name)
            repo.delete()
        except:
            if not ignore_errors:
                abort('Failed to delete github repository...')
        
        # delete the local repository if it exists
        if os.path.exists(os.path.join('..', 'municipalities', repo_name)):
            local('rm -rf %s', os.path.join('..', 'municipalities', repo_name))


@task
def deploy_client_pull(muni_name):
    """Deploy updates to specific municipality's opentaba-client copy"""
    
    repo_name = _get_repo_name(muni_name)
    
    # if the local repo doesn't exist create it
    if not os.path.exists(os.path.join('..', 'municipalities', repo_name)):
        _get_client_pull_repo(muni_name)
    
    # perform fetch-merge-push
    with lcd(os.path.join('..', 'municipalities', repo_name)):
        local('git fetch upstream master')
        local('git merge upstream/master --no-edit')
        local('git push origin gh-pages')


@task
def deploy_client_pull_all():
    """Deploy updates to all opentaba-client municipality copies"""
    
    g = _github_connect()
    
    # go over the organization's repositories, and the ones that match a 
    # a client fork syntax should be deployed to
    for r in g.get_repos():
        if _is_repo_name(r.name):
            deploy_client_pull(_get_muni_from_repo_name(r.name));


def _get_client_pull_repo(muni_name):
    repo_name = _get_repo_name(muni_name)
    g = _github_connect()
    
    # try to find the repository on github
    try:
        repo = g.get_repo(repo_name)
    except:
        abort('The municipality does not have a repository on Github')
    
    # delete the local repository if it exists
    if os.path.exists(os.path.join('..', 'municipalities', repo_name)):
        local('rm -rf %s', os.path.join('..', 'municipalities', repo_name))
    
    # clone the repository from github and add an upstream remote
    with lcd(os.path.join('..', 'municipalities')):
        local('git clone %s' % repo_name)
        with lcd(repo_name):
            local('git remote add upstream https://github.com/niryariv/opentaba-client.git')
