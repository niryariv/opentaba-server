from bs4 import BeautifulSoup
import lxml
import requests
import re
import logging
import json
from hashlib import md5
from copy import deepcopy

from app import *

date_pattern = re.compile(r'(\d+/\d+/\d+)')
SITE_ENCODING = 'windows-1255'

log = logging.getLogger(__name__)


def get_gush_json_page(requests_session, page_num, cookie, view_state, data_source):
    r = requests_session.post(
        'http://mmi.gov.il/IturTabot2/taba1.aspx', 
        cookies=cookie, 
        data={'scriptManagerId_HiddenField':None,'__EVENTTARGET':None,'__EVENTARGUMENT':None,'__VIEWSTATE':view_state,'cpe_ClientState':None,'txtMsTochnit':None,'cmsStatusim$textBox':None,'txtGush':None,'txtwinCal1$textBox':None,'txtwinCal1$popupWin$time':None,'txtwinCal1$popupWin$mskTime_ClientState':None,'txtFromHelka':None,'txtwinCal2$textBox':None,'txtwinCal2$popupWin$time':None,'txtwinCal2$popupWin$mskTime_ClientState':None,'txtMakom':None,'cmsMerchaveiTichnun$textBox':None,'cmsYeudRashi$textBox':None,'txtMatara':None,'cmsYeshuvim$textBox':None,'cmsKodAchrai$textBox':None,'cmsTakanon$textBox':None,'txtAchrai':None,'cmsSug$textBox':None,'cmsMmg$textBox':None,'cmsKodMetachnen$textBox':None,'cmsTasrit$textBox':None,'txtMetachnen':None,'__CALLBACKID':'scriptManagerId',
            '__CALLBACKPARAM':'Mmi.Tashtiot.UI.AjaxComponent.TableView$#$~$#$GetData$#${"P0":"'+data_source+'","P1":'+str(page_num)+',"P2":-1,"P3":["mtysvShemYishuv","Link","Status","tbMahut","Takanon","Tasrit","Nispach","Mmg","tbMakom","tbYechidotDiur","mtmrthTirgumMerchav","mtstTargumSugTochnit","svtTargumSugVaadatTichnun","tbTochnitId"],"P4":"~","P5":"~","P6":true,"P7":true}'
        })
    
    return r.text


def get_gush_json(gush_id):
    """
    Get JSON data for gush_id from the Minhal's website
    """
    log.debug("About to download Gush JSON for %s", gush_id)
    
    try:
        ses = requests.Session()
        
        # Get the base search page and save the aspx session cookie, data source and view state
        r = ses.get('http://mmi.gov.il/IturTabot2/taba1.aspx')
        yum = r.cookies
        # print 'GET http://mmi.gov.il/IturTabot2/taba1.aspx', r.text

        data_source = re.findall(r'tblView_[A-Za-z0-9]+', r.text)[-1]

        html = BeautifulSoup(r.text, 'lxml', from_encoding=SITE_ENCODING)
        view_state = html('input', id='__VIEWSTATE')[0]['value']

        # Tell the server which fields we are displaying
        r = ses.post('http://mmi.gov.il/IturTabot2/taba1.aspx', cookies=yum, data={
            'scriptManagerId_HiddenField':None,
            '__EVENTTARGET':None,
            '__EVENTARGUMENT':None,
            '__VIEWSTATE':view_state,
            'cpe_ClientState':None,
            'txtMsTochnit':None,
            'cmsStatusim$textBox':None,
            'txtGush':None,
            'txtwinCal1$textBox':None,
            'txtwinCal1$popupWin$time':None,
            'txtwinCal1$popupWin$mskTime_ClientState':None,
            'txtFromHelka':None,
            'txtwinCal2$textBox':None,
            'txtwinCal2$popupWin$time':None,
            'txtwinCal2$popupWin$mskTime_ClientState':None,
            'txtMakom':None,
            'cmsMerchaveiTichnun$textBox':None,
            'cmsYeudRashi$textBox':None,
            'txtMatara':None,
            'cmsYeshuvim$textBox':None,
            'cmsKodAchrai$textBox':None,
            'cmsTakanon$textBox':None,
            'txtAchrai':None,
            'cmsSug$textBox':None,
            'cmsMmg$textBox':None,
            'cmsKodMetachnen$textBox':None,
            'cmsTasrit$textBox':None,
            'txtMetachnen':None,
            '__CALLBACKID':'scriptManagerId',
            '__CALLBACKPARAM': 'Mmi.Tashtiot.UI.AjaxComponent.TableView$#$~$#$GetData$#${"P0":"'+data_source+'","P1":0,"P2":-1,"P3":["mtysvShemYishuv","Link","Status","tbMahut","Takanon","Tasrit","Nispach","Mmg","tbMakom","tbYechidotDiur","mtmrthTirgumMerchav","mtstTargumSugTochnit","svtTargumSugVaadatTichnun","tbTochnitId"],"P4":"~","P5":"~","P6":true,"P7":true}'
            })
            # Note and warning: other available fields for selction are: "tbMerchav","tbMsTochnit","tbMsTochnitYashan","tbKodIshuv","tbSug","tbTamlilSaruk","tbMmg","mtmhzShemMachoz","tbTabaSruka","mtsttKvutzatStatusim","tbAchrai","tbMetachnen","tbShemMetachnen","mtkyPianuachYeud","tbYalkut","tbTaarichDigitation","tUniqueID"
            # DO NOT, however, select the field "tbMatara", as it reduces the amount of results in jerusalem from ~15000 to ~1500 (true for June 18th 2014)
            # and, if fields are added here they should be added above as well in the get_gush_json_page function

        # Send a parameterized request to the server (just search for the gush)
        r = ses.post(
            'http://mmi.gov.il/IturTabot2/taba1.aspx/getNetuneiTochniotByAllParames', 
            headers={'Content-Type':'application/json'}, 
            cookies=yum, 
            data=json.dumps({
                'IsOneRow': False,'SourceName': data_source,'bBProjects': False,'conMachoz': 0,'iFromHelka': "-1",'iGush': gush_id,'iMaamadMoncipali': "-1",'iMachoz': "-1",'iNumOfRows': 300,'iToHelka': "-1",'rtncol': 2,'sAchrai': "~",'sFromTaarichStatus': "~",'sKodAchrai': "~",'sKodIshuv': "~",'sKodMetachnen': "~",'sKvutzatStatusim': "~",'sMakom': "~",'sMatara': "~",'sMerchav': "~",'sMetachnen': "~",'sMisTochnit': "~",'sMmg': "~",'sSug': "~",'sTabaSruka': "~",'sTakanon': "~",'sTasrit': "~",'sTik': "~",'sToTaarichStatus': "~",'sVaada': "~",'sYeudRashi': "~"
          })
        )

        result = []
        page = 0

        # Get the first page of results and extra data
        first_page = get_gush_json_page(ses, page, yum, view_state, data_source)
        result = result + json.loads(re.findall('\[.*?\]', first_page)[0])

        # Get the number of pages from the first page (every page has this)
        pages = int(re.findall('\$([\-#0-9]*)', re.findall('\](.*?){', first_page)[0])[7])

        # Get the rest of the pages
        while page < pages:
            page = page + 1
            result = result + json.loads('[' + re.findall('\[(.*?)\]', get_gush_json_page(ses, page, yum, view_state, data_source))[0] + ']')

        ses.close()
            
    except Exception, e:
        log.exception("ERROR: %s", e)
        exit(1)

    return result


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
               'committee_type' : ''}
        
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


def scrape_gush(gush, RUN_FOLDER=False):
    """
    Accepts a gush object, scrapes data from gush URL and saves it into the plans collection

    RUN_FOLDER is for testing
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
        return True

    plans_data = extract_data(gush_json)

    # Testing, just return the plans json
    if app.config['TESTING']:
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
            
                # just make sure these are deleted because we will probably have quite a few iterations here
                del plan_copy
                del existing_plan_copy
    
    # update the gush data
    log.debug("updating gush json_hash, last_checked_at")
    gush["json_hash"] = json_hash
    gush["last_checked_at"] = datetime.datetime.now()
    db.gushim.save(gush)
