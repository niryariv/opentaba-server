"""
Helper functions for both fabfiles
"""

from requests import get
from json import loads


def _download_gush_map(muni_name, topojson=False):
    r = get('https://raw.githubusercontent.com/niryariv/israel_gushim/master/%s.%s' % (muni_name, 'topojson' if topojson else 'geojson'))
    if r.status_code != 200:
        abort('Failed to download gushim map')
    
    try:
        res = loads(r.text)
    except:
        abort('Gushim map is an invalid JSON file')
    
    return res
