# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
import lxml
import re


SITE_ENCODING = 'windows-1255'
# Earliest meeting date to filter plans by
FROM_MEETING_DATE_FILTER = '01/01/2010'

# Number of pages regular expression
number_of_pages_pattern = re.compile(ur'דף( \d+ מתוך )(\d+)( דפים)')


def get_mavat_gush_json(gush_id):
    """
    Get JSON data for gush_id from the Ministry of interior's website
    """
    ses = requests.Session()

    # Get the base search page and save the aspx session cookie
    r = ses.get('http://mavat.moin.gov.il/MavatPS/Forms/SV3.aspx?tid=3')
    yum = r.cookies

    # Gather session identifiers
    html = BeautifulSoup(r.text, 'lxml', from_encoding=SITE_ENCODING)
    view_state = html('input', id='__VIEWSTATE')[0]['value']
    view_state_encrypted = html('input', id='__VIEWSTATEENCRYPTED')[0]['value']
    event_validation = html('input', id='__EVENTVALIDATION')[0]['value']
    
    # This is the data we send with the request. From what I saw, removing random fields will make the scraper not work
    # All parameters were actually sent by browser, maybe not all of the are necessary
    request_data = {
            '__EVENTTARGET':'',
            '__EVENTARGUMENT':'',
            '__VIEWSTATE':view_state,
            '__VIEWSTATEENCRYPTED':view_state_encrypted,
            '__EVENTVALIDATION':event_validation,
            'ctl00$ContentPlaceHolder1$txtNumb':'',
            'ctl00$ContentPlaceHolder1$cboEntities':'-1',
            'ctl00$ContentPlaceHolder1$cboSubEntities':'-1',
            'ctl00$ContentPlaceHolder1$txtFromBlock':gush_id,
            'ctl00$ContentPlaceHolder1$txtToBlock':gush_id,
            'ctl00$ContentPlaceHolder1$txtFromParcel':'',
            'ctl00$ContentPlaceHolder1$txtToParcel':'',
            'ctl00$ContentPlaceHolder1$cboFilterDistrict':'-1',
            'ctl00$ContentPlaceHolder1$cboFilterArea':'-1',
            'ctl00$ContentPlaceHolder1$cboFilterJurst':'-1',
            'ctl00$ContentPlaceHolder1$cboFilterCity':'-1',
            'ctl00$ContentPlaceHolder1$cboFilterStreet':'-1',
            'ctl00$ContentPlaceHolder1$txtGoals':'',
            'ctl00$ContentPlaceHolder1$txtFilterFromApprovedDate':'',
            'ctl00$ContentPlaceHolder1$txtFilterToApprovedDate':'',
            'ctl00$ContentPlaceHolder1$txtFromMeetingDate':FROM_MEETING_DATE_FILTER,
            'ctl00$ContentPlaceHolder1$txtToMeetingDate':'',
            'ctl00$ContentPlaceHolder1$btnFilter.x':'49',
            'ctl00$ContentPlaceHolder1$btnFilter.y':'14',
            'ctl00$ContentPlaceHolder1$SubEntityID':'-1',
            'ctl00$ContentPlaceHolder1$SelectedPlanId':'0',
            'ctl00$ContentPlaceHolder1$SelectedPlanNumber':'0',
            'ctl00$ContentPlaceHolder1$StreetID':'-1',
            'ctl00$ContentPlaceHolder1$CityID':'-1',
            'ctl00$ContentPlaceHolder1$JurstID':'-1',
            'ctl00$ContentPlaceHolder1$AreaID':'-1',
            'ctl00$ContentPlaceHolder1$PID':'-1',
            'ctl00$ContentPlaceHolder1$JID':'-1',
            'ctl00$ContentPlaceHolder1$CCID':'-1',
            'ctl00$ContentPlaceHolder1$SLY':'-1',
            'ctl00$ContentPlaceHolder1$ButtonCode':'-1',
            'ctl00$ContentPlaceHolder1$ShowSearchResult':'0'
        }

    plans = []
    curr_page = 1
    
    while True:
        # If we're requesting a page that's not the first one we need to update the request parameters
        if curr_page > 1:
            event_target = 'ctl00$ContentPlaceHolder1$entitiesPaging$pagingForward'
            event_argument = html('input', id='__EVENTARGUMENT')
            if len(event_argument) > 0:
                event_argument = event_argument[0]['value']
            else:
                event_argument = ''
            
            # Update the actual parameters
            request_data.update({'ctl00$ContentPlaceHolder1$entitiesPaging$currentPage':str(curr_page)})
            request_data.update({'__EVENTTARGET':event_target})
            request_data.update({'__EVENTARGUMENT':event_argument})
            request_data.update({'__VIEWSTATE':view_state})
            request_data.update({'__VIEWSTATEENCRYPTED':view_state_encrypted})
            request_data.update({'__EVENTVALIDATION':event_validation})
            request_data.pop('ctl00$ContentPlaceHolder1$btnFilter.x', None)
            request_data.pop('ctl00$ContentPlaceHolder1$btnFilter.y', None)

        # Search plans by gush id
        r = ses.post('http://mavat.moin.gov.il/MavatPS/Forms/SV3.aspx?tid=3', headers={'Content-Type':'application/x-www-form-urlencoded'}, 
            cookies=yum, data=request_data)
        
        # On the first page, get the total number of pages if it exists
        if curr_page == 1:
            number_of_page_str = re.search(number_of_pages_pattern, r.text)
            if number_of_page_str:
                number_of_pages = int(number_of_page_str.groups()[1])
            else:
                number_of_pages = 1
        
        page_plans = []

        # Get the new view state and friends for future requests (following page)
        html = BeautifulSoup(r.text, 'lxml', from_encoding=SITE_ENCODING)
        view_state = html('input', id='__VIEWSTATE')[0]['value']
        view_state_encrypted = html('input', id='__VIEWSTATEENCRYPTED')[0]['value']
        event_validation = html('input', id='__EVENTVALIDATION')[0]['value']
        
        # Parse the table of plans in the result HTML
        for tr in html('tbody')[0].children:
            if type(tr) == Tag:
                # 1 = code, 3 = machoz, 5 = yeshuv/rashut mekomit/merchav tichnun, 7 = yeshut tichnunit, 9 = mispar tochnit, 11 = shem tochnit, 13 = ishur reshumot/itonim
                page_plans.append({'code':tr.contents[1].string,'number':tr.contents[9].string.strip().replace('/ ', '/'),'files':[], 'meetings':[]})

        # Get plan files and meetings for each plan
        for plan in page_plans:
            (plan['files'], plan['meetings']) = get_mavat_plan_docs_meetings_json(ses, yum, plan['code'])
        
        # Add the page's plans to the total plans
        plans += page_plans
        
        # Break if we hit the page number
        if curr_page >= number_of_pages:
            break
        else:
            curr_page += 1

    ses.close()    
    return plans


def get_mavat_plan_docs_meetings_json(session, cookie, plan_code):
    """
    Request plan info page from MAVAT website, parse files and meetings lists and keep the permalinks
    """
    files = []
    meetings = []
    
    # Request the plan's page from MAVAT website
    plan_r = session.post('http://mavat.moin.gov.il/MavatPS/Forms/SV4.aspx?tid=4', headers={'Content-Type':'application/x-www-form-urlencoded'}, 
        cookies=cookie, data={'PL_ID':plan_code})
    
    plan_html = BeautifulSoup(plan_r.text, 'lxml', from_encoding=SITE_ENCODING)
    
    # If we got tblDocs table, parse its content for tasritim
    tbl_docs = plan_html('table', id='tblDocs')
    if len(tbl_docs) > 0:
        for tr in tbl_docs[0]('tbody')[0].children:
            if type(tr) == Tag:
                if any(word in tr.contents[3].string for word in [u'תשריט', u'פרוטוקול']):
                    # Get the file's permalink from the onclick javascript function call
                    file_permalink = _get_permalink_by_opendoc(tr.contents[5].contents[1].get('onclick'))
                
                    # Get the file type from the img
                    file_type = _get_filetype_by_img_src(tr.contents[5].contents[1].get('src'))
                    
                    files.append({'name':tr.contents[3].string.strip(),'type':file_type,'link':file_permalink})
    
    # If we got tblDecisionMeetings, parse its content for meetings
    tbl_protocol = plan_html('table', id='tblDecisionMeetings')
    if len(tbl_protocol) > 0:
        for tr in tbl_protocol[0]('tbody')[0].children:
            if type(tr) == Tag:
                # 1 = mahoz/minhal hatichnun, 3 = mosad tichnun, 5 = mispar yeshiva, 7 = taarich yeshiva, 9 = se'ifei yeshiva, 11 = protocol, 13 = tamlil hayeshiva
                
                # If there's a protocol file link save it, otherwise just make it empty
                if len(tr.contents[11].contents) > 1:
                    # Get the file's permalink from the onclick javascript function call
                    file_permalink = _get_permalink_by_opendoc(tr.contents[11].contents[1].get('onclick'))
                
                    # Get the file type from the img
                    file_type = _get_filetype_by_img_src(tr.contents[11].contents[1].get('src'))
                else:
                    file_permalink = ''
                    file_type = ''
                
                meetings.append({'institute':tr.contents[3].string.strip(),'number':tr.contents[5].string.strip(),
                    'date':tr.contents[7].string.strip(),'p_type':file_type,'p_link':file_permalink})
    
    return (files, meetings)


def _get_filetype_by_img_src(img_src):
    # These are the mavat file icons we know about
    if img_src == '../images/ft/file_PDF.gif':
        return 'pdf'
    elif img_src == '../images/ft/file_ZIP.gif':
        return 'zip'
    elif img_src == '../images/ft/file_DWG.gif':
        return 'dwg'
    elif img_src == '../images/ft/file_XLS.gif':
        return 'xls'
    elif img_src == '../images/ft/file_DOC.gif':
        return 'doc'
    else: # could also be '../images/ft/file.gif', which is basically unknown
        return 'unknown'


def _get_permalink_by_opendoc(opendoc_call):
    # Convert javascript openDoc function call to file permalink
    return 'http://mavat.moin.gov.il/MavatPS/Forms/Attachment.aspx?edid=%s&edn=%s' % (opendoc_call.split('\'')[1], opendoc_call.split('\'')[3])
