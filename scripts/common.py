"""
Helper functions for both fabfiles
"""

from fabric.api import runs_once, prompt, abort
from getpass import getpass
from requests import get
from json import loads
from github import Github, Repository


def _download_gush_map(muni_name, topojson=False):
    r = get('https://raw.githubusercontent.com/niryariv/israel_gushim/master/%s.%s' % (muni_name, 'topojson' if topojson else 'geojson'))
    if r.status_code != 200:
        abort('Failed to download gushim map')
    
    try:
        res = loads(r.text)
    except:
        abort('Gushim map is an invalid JSON file')
    
    return res


@runs_once
def _github_connect():
    # connect to github only once per run
    username = prompt('Github user: ')
    password = getpass('Github password: ')
    
    try:
        u = Github(username, password).get_user()
        
        # find the opentaba organization
        for org in u.get_orgs():
            if org.login == 'opentaba':
                return org
        
        abort('You are not a member of \'opentaba\' organization')
    except:
        abort('Could not gain Github authorization')
