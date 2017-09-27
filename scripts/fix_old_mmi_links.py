#!/usr/bin/env python2

# allow ourselves to import from the parent and current directory
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '.')

from lib.conn import *

existing_plans = db.plans.find()
fixed_count = 0

for p in existing_plans:
    update_needed = False
    
    # fix tasrit links
    tasrit_link = []
    for l in p['tasrit_link']:
        if l.startswith('/') or 'mmi.gov.il' in l:
            tasrit_link.append('http://apps.land.gov.il%s' % l.split('mmi.gov.il')[-1])
            update_needed = True
        else:
            tasrit_link.append(l)
    
    # fix takanon links
    takanon_link = []
    for l in p['takanon_link']:
        if l.startswith('/') or 'mmi.gov.il' in l:
            takanon_link.append('http://apps.land.gov.il%s' % l.split('mmi.gov.il')[-1])
            update_needed = True
        else:
            takanon_link.append(l)
    
    # fix nispachim links
    nispahim_link = []
    for l in p['nispahim_link']:
        if l.startswith('/') or 'mmi.gov.il' in l:
            nispahim_link.append('http://apps.land.gov.il%s' % l.split('mmi.gov.il')[-1])
            update_needed = True
        else:
            nispahim_link.append(l)
    
    # fix file links
    files_link = []
    for l in p['files_link']:
        if l.startswith('/') or 'mmi.gov.il' in l:
            files_link.append('http://apps.land.gov.il%s' % l.split('mmi.gov.il')[-1])
            update_needed = True
        else:
            files_link.append(l)
    
    # fix details link
    details_link = p['details_link']
    if details_link.startswith('/') or 'mmi.gov.il' in details_link:
        details_link = 'http://apps.land.gov.il%s' % details_link.split('mmi.gov.il')[-1]
        update_needed = True
    
    if update_needed:
        db.plans.update({'_id': p['_id']}, {
            '$set': {
                'tasrit_link': tasrit_link,
                'takanon_link': takanon_link,
                'nispahim_link': nispahim_link,
                'files_link': files_link,
                'details_link': details_link
            }
        }, upsert=False)
        fixed_count += 1

print 'Finished fixing %s plans' % fixed_count
