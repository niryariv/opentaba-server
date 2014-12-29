# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import lxml
import re
import logging
import json
import datetime
import os
from hashlib import md5
from copy import deepcopy
from multiprocessing.pool import ThreadPool

from conn import db, RUNNING_LOCAL
from mmi_scrape import get_mmi_gush_json
from mavat_scrape import get_mavat_gush_json
import sociallib

date_pattern = re.compile(r'(\d+/\d+/\d+)')
mmi_bad_plan_number_no_slash_pattern = re.compile(ur'^(.*[0-9]+)([א-ת])$')
mmi_bad_plan_number_leading_zero_pattern = re.compile(r'^(0+)([0-9]+)$')

log = logging.getLogger(__name__)


def get_gush_json(gush_id):
    log.debug("About to download Gush JSON for %s", gush_id)
    
    try:
        # Use different threads to get data from mmi and mavat
        scrape_pool = ThreadPool(processes=1)
        async_mmi_scrape = scrape_pool.apply_async(get_mmi_gush_json, (gush_id,))
        async_mavat_scrape = scrape_pool.apply_async(get_mavat_gush_json, (gush_id,))
        
        mmi_json = async_mmi_scrape.get()
        mavat_json = async_mavat_scrape.get()
    except Exception, e:
        log.exception("ERROR: %s", e)
        exit(1)
    
    # We need to try to match mmi plans to mavat plans, which is not very easy because they don't seem to follow the same rules
    # eg. there are lots of extra spaces in mavat, and dashes that don't exist in the mmi numbers
    for mmi_plan in mmi_json:
        # Get the plan number from the mmi plan and put it in a list so we can compare to it AND the fixed values if it will be needed
        bs = BeautifulSoup(mmi_plan['Link'], 'lxml')
        mmi_number = [ bs('a')[0].contents[0] ]
        
        # Check if the mmi plan number is missing a slash
        bad_mmi_number = re.search(mmi_bad_plan_number_no_slash_pattern, mmi_number[0])
        if bad_mmi_number:
            mmi_number.append(''.join(bad_mmi_number.group(0)[0:-1]) + '/' + bad_mmi_number.group(0)[-1])
        else:
            # Check if the mmi plan number starts with a zero (eg. "0856")
            bad_mmi_number = re.search(mmi_bad_plan_number_leading_zero_pattern, mmi_number[0])
            if bad_mmi_number:
                mmi_number.append(''.join(bad_mmi_number.group(0)[1:]))
        
        # Now just try to match mavat plan numbers with any of the mmi possible plan numbers' list
        for mavat_plan in mavat_json:
            if mavat_plan['number'] in mmi_number:
                mmi_plan['mavat_code'] = unicode(mavat_plan['code'])
                mmi_plan['mavat_files'] = mavat_plan['files']
                mmi_plan['mavat_meetings'] = mavat_plan['meetings']
                break
    
    return mmi_json


def extract_data(gush_json):
    data = []
    
    for plan in gush_json:
        rec = {'plan_id': 0,
               'area': '',
               'number': '',
               'details_link': '',
               'status': '',
               # 'date': '',
               'day': None, 'month': None, 'year': None,
               'essence': '',
               'takanon_link': [],
               'tasrit_link': [],
               'nispahim_link': [],
               'files_link': [],
               'govmap_link': [],
               'location_string': '',
               'housing_units': 0,
               'region': '',
               'plan_type': '',
               'committee_type' : '',
               'mavat_code': '',
               'mavat_files': [],
               'mavat_meetings': []}
        
        rec['plan_id'] = plan['tbTochnitId']
        rec['area'] = plan['mtysvShemYishuv'].strip()
        
        bs = BeautifulSoup(plan['Link'], 'lxml')
        rec['details_link'] = bs('a')[0].get('href').replace("javascript:openDetailesPage('", 'http://mmi.gov.il/IturTabot2/').replace("','", '', 1).replace("','", '&tbMsTochnit=').replace("')", '')
        rec['number'] = bs('a')[0].contents[0]

        rec['status'] = plan['Status'].strip()

        matchdate = re.search(date_pattern, rec['status'])
        if matchdate:
            d = matchdate.group(1)
            # rec["date"] = datetime.datetime.strptime(d, "%d/%m/%Y")
            # switched to this instead of datetime - seems to be much faster to query with mongo
            rec['day'], rec['month'], rec['year'] = [int(i) for i in d.split('/')]
            # silly hack to get the years to look good, because 06 turns to 6. should look into python date parsers...
            if rec['year'] < 30:
                rec['year'] = rec['year'] + 2000
            elif rec['year'] < 100:
                rec['year'] = rec['year'] + 1900
            
            rec['status'] = rec['status'].replace(d, '').strip()

        rec['essence'] = plan['tbMahut'].strip()

        if plan['Takanon'] is not None:
            bs = BeautifulSoup(plan['Takanon'], 'lxml')
            for i in bs('a'):
                rec['takanon_link'].append('http://mmi.gov.il' + i.get('href'))

        bs = BeautifulSoup(plan['Tasrit'], 'lxml')
        for i in bs('a'):
            rec['tasrit_link'].append('http://mmi.gov.il' + i.get('href'))

        bs = BeautifulSoup(plan['Nispach'], 'lxml')
        for i in bs('a'):
            rec['nispahim_link'].append('http://mmi.gov.il' + i.get('href'))

        if plan['Mmg'] is not None:
            bs = BeautifulSoup(plan['Mmg'], 'lxml')
            for i in bs('a'):
                url = i.get('href')
                if url.endswith('.zip'):
                    rec['files_link'].append(url)
                elif 'PopUpMmg' in url:
                    rec['govmap_link'].append(url)

        rec['location_string'] = plan['tbMakom'].strip()
        rec['housing_units'] = plan['tbYechidotDiur']
        rec['region'] = plan['mtmrthTirgumMerchav']
        rec['plan_type'] = plan['mtstTargumSugTochnit']
        rec['committee_type'] = plan['svtTargumSugVaadatTichnun']
        
        # check if we managed to pair the mmi data for this plan with its mavat data
        if 'mavat_code' in plan.keys():
            rec['mavat_code'] = plan['mavat_code']
            rec['mavat_files'] = plan['mavat_files']
            rec['mavat_meetings'] = plan['mavat_meetings']
        
        data.append(rec)
    
    return data


def hash_gush_json(gush_json):
    """
    Returns MD5 hash of the gush's plans json without the Link field, because it contains 
    a parameter which changes with every request, and it is only the link to the plan's 
    details on the MMI website so we can keep using an old value
    """
    
    for plan in gush_json: 
        del plan['Link']

    return md5(json.dumps(gush_json, sort_keys=True)).hexdigest()


def scrape_gush(gush, RUN_FOLDER=False, TESTING=False):
    """
    Accepts a gush object, scrapes data from gush URL and saves it into the plans collection

    RUN_FOLDER is for testing
    TESTING is because we don't have access to the flask app from here anymore
    """

    gush_id = gush['gush_id']
    log.info("Checking gush #%s", gush_id)

    if RUNNING_LOCAL:
        local_cache = "filecache/%s.json" % gush_id
        if RUN_FOLDER:
            local_cache = os.path.join(RUN_FOLDER, local_cache)
        log.info("Running locally, cache file is %s", local_cache)

        if os.path.exists(local_cache):
            log.debug("Reading existing cache file %s", local_cache)
            gush_json = json.loads(open(local_cache, 'r').read())
        else:
            gush_json = get_gush_json(gush_id)
            open(local_cache, 'wb').write(json.dumps(gush_json))

    else:
        gush_json = get_gush_json(gush_id)

    """
    first check if the gush results have changed. no point in checking each plan's data
    if the entire plan-set hasn't changed at all
    """
    json_hash = hash_gush_json(deepcopy(gush_json))
    if gush["json_hash"] == json_hash:
        log.debug("gush plans' data hasn't changed, returning")
        """
        need to update last_checked_at even if the plan data hasn't changed, so the gush's 
        scraping priority on the next scrape would be less than earlier-checked gushim
        """
        gush["last_checked_at"] = datetime.datetime.now()
        db.gushim.save(gush)
        return True

    plans_data = extract_data(gush_json)

    # Testing, just return the plans json
    if TESTING:
        return plans_data
    
    # select all existing plans in one db transaction
    plan_ids = []
    for plan in plans_data:
        plan_ids.append(plan['plan_id'])
    existing_plans = list(db.plans.find({'plan_id' : { '$in' : plan_ids } }))
    
    for plan in plans_data:
        # try to find the plan if it already exists
        existing_plan = None
        for e in existing_plans:
            if e['plan_id'] == plan['plan_id']:
                existing_plan = e
                break
		
        if existing_plan is None:
            # the plan is new, just insert it to the db
            plan['gushim'] = [ gush_id ]
            log.debug("Inserting new plan data: %s", plan)
            db.plans.insert(plan)
            
            # post plan to social networks
            sociallib.post(plan)
        else:
            # since the plan exists get it's _id and gushim values
            plan['_id'] = existing_plan['_id']
            plan['gushim'] = existing_plan['gushim']
            
            if not gush_id in existing_plan['gushim']:
                # the current gush does not exist yet in this plan's gushim list
                plan['gushim'].append(gush_id)
                # since we are sending an _id value the document will be updated
                log.debug("Updating modified plan data: %s", plan)
                db.plans.save(plan)
                
                # post plan to social networks
                sociallib.post(plan)
            else:
                # compare the values. maybe the plan wasn't modified at all
                plan_copy = deepcopy(plan)
                existing_plan_copy = deepcopy(existing_plan)
                del plan_copy['details_link']
                del existing_plan_copy['details_link']
                if not plan_copy == existing_plan_copy:
                    # since we are sending an _id value the document will be updated
                    log.debug("Updating modified plan data: %s", plan)
                    db.plans.save(plan)
                    
                    # post plan to social networks
                    sociallib.post(plan)
            
                # just make sure these are deleted because we will probably have quite a few iterations here
                del plan_copy
                del existing_plan_copy
    
    # update the gush data
    log.debug("updating gush json_hash, last_checked_at")
    gush["json_hash"] = json_hash
    gush["last_checked_at"] = datetime.datetime.now()
    db.gushim.save(gush)
