"""
fab file for managing opentaba-server heroku apps
"""

from fabric.api import *
from json import loads, dumps
import os
from copy import deepcopy

from common import _download_gush_map


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
def add_muni(muni_name, display_name=''):
    """Add an entry for a new municipality or update an existing one to the munis.js file with the required data"""
    
    with lcd(os.path.join('..', 'opentaba-client')):
        # download the online gush map
        geojson_gush_map = _download_gush_map(muni_name)
        
        # make sure we're using the master branch
        local('git checkout master')
    
        # load the current municipalities' index dictionary
        with open(os.path.join('..', 'opentaba-client', 'munis.js')) as index_data:
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
            warn('No new data was found in the downloaded gush map. No changes were made to munis.js')
        else:
            # write back the munis.js file
            out = open(os.path.join('..', 'opentaba-client', 'munis.js'), 'w')
            out.write('var municipalities = ' + dumps(new_index_json, sort_keys=True, indent=4, separators=(',', ': ')) + ';')
            out.flush()
            os.fsync(out.fileno())
            out.close()
    
            # commit and push to origin
            local('git add munis.js')
            local('git commit -m "added %s to munis.js"' % muni_name)
            local('git push origin master')
            
            # merge into gh-pages branch
            local('git checkout gh-pages')
            local('git merge master --no-edit')
            local('git push origin gh-pages')
            
            # back to master for work
            local('git checkout master')
            
            print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
            print 'The new/updated municipality data was added to munis.js, its topojson '
            print 'gushim map will be loaded from the israel_gushim repository, and changes were '
            print 'committed and pushed to origin. If more data needs to be in munis.js, you can '
            print 'do it now and push again. The municipality\'s site is now live at:'
            print 'http://%s.opentaba.info/' % muni_name
            print '*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*X*'
