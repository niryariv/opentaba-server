# -*- coding: utf-8 -*-

import logging

import requests
from bs4 import BeautifulSoup
import lxml
import re
import json

from helpers import parse_challenge


SITE_ENCODING = 'windows-1255'
logger = logging.getLogger('challenge')

def get_mmi_gush_json(gush_id):
    """
    Get JSON data for gush_id from the Minhal's website
    """
    ses = requests.Session()

    # Get the base search page and save the aspx session cookie, data source and view state
    r = ses.get('http://mmi.gov.il/IturTabot2/taba1.aspx')
    
    # Solve the challenge if needed
    if 'X-AA-Challenge' in r.text:
        challenge = parse_challenge(r.text)
        logger.warning('Text: %s' % r.text)
        logger.warning('Got challenge: %s' % challenge)
        r = ses.get('http://mmi.gov.il/IturTabot2/taba1.aspx', headers={
            'X-AA-Challenge': challenge['challenge'],
            'X-AA-Challenge-ID': challenge['challenge_id'],
            'X-AA-Challenge-Result': challenge['challenge_result']
        })
        
        logger.warning('Second text: %s' % r.text)
        
        # Yet another request...
        yum = r.cookies
        r = ses.get('http://mmi.gov.il/IturTabot2/taba1.aspx', cookies=yum)
        logger.warning('Third text: %s' % r.text)
    
    yum = r.cookies

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
        '__CALLBACKPARAM': 'Mmi.Tashtiot.UI.AjaxComponent.TableView$#$~$#$GetData$#${"P0":"'+data_source+'","P1":0,"P2":-1,"P3":["mtysvShemYishuv","Link","Status","tbMahut","Takanon","Tasrit","Nispach","Mmg","tbMakom","tbYechidotDiur","mtmrthTirgumMerchav","mtstTargumSugTochnit","svtTargumSugVaadatTichnun","tbTochnitId", "tbMsTochnit"],"P4":"~","P5":"~","P6":true,"P7":true}'
        })
        # Note and warning: other available fields for selction are: "tbMerchav","tbMsTochnitYashan","tbKodIshuv","tbSug","tbTamlilSaruk","tbMmg","mtmhzShemMachoz","tbTabaSruka","mtsttKvutzatStatusim","tbAchrai","tbMetachnen","tbShemMetachnen","mtkyPianuachYeud","tbYalkut","tbTaarichDigitation","tUniqueID"
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
    first_page = get_mmi_gush_json_page(ses, page, yum, view_state, data_source)
    result = result + json.loads(re.findall('\[.*?\]', first_page)[0])

    # Get the number of pages from the first page (every page has this)
    pages = int(re.findall('\$([\-#0-9]*)', re.findall('\](.*?){', first_page)[0])[7])

    # Get the rest of the pages
    while page < pages:
        page = page + 1
        result = result + json.loads('[' + re.findall('\[(.*?)\]', get_mmi_gush_json_page(ses, page, yum, view_state, data_source))[0] + ']')

    ses.close()
    return result


def get_mmi_gush_json_page(requests_session, page_num, cookie, view_state, data_source):
    r = requests_session.post(
        'http://mmi.gov.il/IturTabot2/taba1.aspx', 
        cookies=cookie, 
        data={'scriptManagerId_HiddenField':None,'__EVENTTARGET':None,'__EVENTARGUMENT':None,'__VIEWSTATE':view_state,'cpe_ClientState':None,'txtMsTochnit':None,'cmsStatusim$textBox':None,'txtGush':None,'txtwinCal1$textBox':None,'txtwinCal1$popupWin$time':None,'txtwinCal1$popupWin$mskTime_ClientState':None,'txtFromHelka':None,'txtwinCal2$textBox':None,'txtwinCal2$popupWin$time':None,'txtwinCal2$popupWin$mskTime_ClientState':None,'txtMakom':None,'cmsMerchaveiTichnun$textBox':None,'cmsYeudRashi$textBox':None,'txtMatara':None,'cmsYeshuvim$textBox':None,'cmsKodAchrai$textBox':None,'cmsTakanon$textBox':None,'txtAchrai':None,'cmsSug$textBox':None,'cmsMmg$textBox':None,'cmsKodMetachnen$textBox':None,'cmsTasrit$textBox':None,'txtMetachnen':None,'__CALLBACKID':'scriptManagerId',
            '__CALLBACKPARAM':'Mmi.Tashtiot.UI.AjaxComponent.TableView$#$~$#$GetData$#${"P0":"'+data_source+'","P1":'+str(page_num)+',"P2":-1,"P3":["mtysvShemYishuv","Link","Status","tbMahut","Takanon","Tasrit","Nispach","Mmg","tbMakom","tbYechidotDiur","mtmrthTirgumMerchav","mtstTargumSugTochnit","svtTargumSugVaadatTichnun","tbTochnitId", "tbMsTochnit"],"P4":"~","P5":"~","P6":true,"P7":true}'
        })
    
    return r.text
