"""
fab file for managing opentaba-client-dummy forks
"""

from fabric.api import *
from github import Repository
from bs4 import BeautifulSoup
import os
import codecs

from common import _github_connect
from client_fabfile import update_gushim_client


@runs_once
def _get_repo_name(muni_name):
    return 'opentaba-client-dummy-%s' % muni_name


@task
def create_dummy(muni_name, display_name):
    """Create a new opentaba-client-dummy fork for a new municipality"""
    
    g = _github_connect()
    repo_name = _get_repo_name(muni_name)
    
    # create a new repo for the new dummy site
    try:
        repo = g.create_repo(repo_name, has_issues=False, has_wiki=False, has_downloads=False, auto_init=False)
    except:
        abort('Failed to create new github repository...')
    
    # update the index.js file
    update_gushim_client(muni_name, display_name)
    
    with lcd('..'):
        local('git clone %s tmp-%s' % (repo.ssh_url, repo_name))
        
        with lcd('tmp-%s' % repo_name):
            local('git remote add upstream https://github.com/opentaba/opentaba-client-dummy')
            local('git fetch upstream master:gh-pages')
            local('git checkout gh-pages')
            
            # add CNAME
            local('echo %s.opentaba.info > CNAME' % muni_name)
            
            # edit index.html metadata
            with open(os.path.join('..', 'tmp-%s' % repo_name, 'index.html')) as index_file:
                index_data = index_file.read()
            
            bs = BeautifulSoup(index_data, 'lxml')
            bs('meta')[2]['content'] = bs('meta')[2]['content'] + display_name.decode('utf-8')
            bs('link')[0]['href'] = '%s.opentaba.info' % muni_name
            
            out = codecs.open(os.path.join('..', 'tmp-%s' % repo_name, 'index.html'), 'w', 'utf-8')
            out.write(bs.prettify())
            out.flush()
            os.fsync(out.fileno())
            out.close()
    
            # add, commit, push new CNAME
            local('git add CNAME')
            local('git add index.html')
            local('git commit -m "personalized for %s"' % muni_name)
            local('git push origin gh-pages')
            
            # delete the remote master branch as we don't need it
            #local('git push origin --delete master')
    
        # delete new repo's local folder
        local('rm -rf tmp-%s' % repo_name)
    
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
    print 'Now you need to manually add the new hostname (subdomain)'
    print 'to point to %s.opentaba.info' % muni_name
    print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'


@task
def delete_dummy(muni_name, ignore_errors=False):
    """Delete a dummy fork repository"""
    
    g = _github_connect()
    repo_name = _get_repo_name(muni_name)
    
    try:
        repo = g.get_repo(repo_name)
        repo.delete()
    except:
        if not ignore_errors:
            abort('Failed to delete github repository...')
