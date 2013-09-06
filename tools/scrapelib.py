from bs4 import BeautifulSoup

import requests
import datetime
import re
#import md5
from hashlib import md5

from app import *

date_pattern = re.compile(r'(\d+/\d+/\d+)')
SITE_ENCODING = 'windows-1255'

def url_for_gush(gush_id):
	return "http://mmi.gov.il/IturTabot/taba2.asp?Gush=%s&fromTaba1=true" % gush_id

# get HTML page for gush_id from the Minhal's website
def get_gush_html(gush_id):

	download_url = url_for_gush(gush_id)
	print (download_url)

	try:
		r = requests.get(download_url)
		if r.status_code != 200:
			raise Exception("Status code: %s" % r.status_code)
	except Exception, e:
		print ("ERROR: %s" % e)
		exit()

	r.encoding = SITE_ENCODING
	html = r.text
	
	return html



# helper functions to clean up some hrefs
def _extract_popoutpdf(js):
	return "http://mmi.gov.il/%s" % js.replace("javascript:PopOutPdf('", "").replace("');", "")

def _extract_popoutmmg(js):
	return js.replace("javascript:PopOutMmg('", "").replace("');", "")

def extract_data(html):
	data = []

	s = BeautifulSoup(html, "lxml", from_encoding = SITE_ENCODING)

	table = s("table", "highLines")[0]
	for tr in table("tr", valign="top"):

		rec = {	
			"area" 	: '',
			"number" : '',
			"details_link" : '',
			"status": '',
			# "date" 	: '',
			"day" : None, "month" : None, "year" : None,
			"essence" : '',
			"takanon_link" 	: [],
			"tasrit_link" 	: [],
			"nispahim_link" : [],
			"files_link" 	: [],
			"govmap_link" 	: []
		}		

		rec["area"] = tr("td", width="80")[0].get_text(strip=True).encode('utf-8')
		rec["number"] = tr("td", width="120")[0].get_text(strip=True).encode('utf-8')
		rec["details_link"] = tr("td", width="120")[0].a.get("href")
		
		rec["status"] = tr("td", width="210")[0].get_text(strip=True).encode('utf-8')
		
		matchdate = re.search(date_pattern, rec["status"])
		if matchdate:
			d = matchdate.group(1)
			# rec["date"] = datetime.datetime.strptime(d, "%d/%m/%Y")
			# switched to this instead of datetime - seems to be much faster to query with mongo
			rec["day"], rec["month"], rec["year"] = [int(i) for i in d.split('/')]
			rec["status"] = rec["status"].replace(d, '').strip()
		
		rec["essence"] = tr("td", width="235")[0].get_text(strip=True).encode('utf-8')

		if tr("td", width="40")[0].a:
			for i in tr("td", width="40")[0].find_all("a"):
				rec["takanon_link"].append(_extract_popoutpdf(i.get("href")))

		if tr("td", width="40")[1].a:
			for i in tr("td", width="40")[1].find_all("a"):
				rec["tasrit_link"].append(_extract_popoutpdf(i.get("href")))

		if tr("td", width="55")[0].a:
			for i in tr("td", width="55")[0].find_all("a"):
				rec["nispahim_link"].append(_extract_popoutpdf(i.get("href")))

		if tr("td", width="40")[2].a:
			for i in tr("td", width="40")[2].find_all("a"):
				url = i.get("href")
				if url.endswith(".zip"):
					rec["files_link"].append(url)
				elif "PopUpMmg" in url:
					rec["govmap_link"].append(_extract_popupmmg(url))

		data.append(rec)

	return data


# accepts a gush object, scrapes date from gush URL and saves it into the plans collection
def scrape_gush(gush):

	gush_id = gush['gush_id']

	print ("checking gush %s" % gush_id)
	
	if RUNNING_LOCAL:
		local_cache = "filecache/%s.html" % gush_id
		if os.path.exists(local_cache):
			print ("reading local file %s" % local_cache)
			html = open(local_cache, 'r').read()
		else:
			html = get_gush_html(gush_id)
			open(local_cache, 'wb').write(html.encode('utf-8'))

	else:
		html = get_gush_html(gush_id)
	
	
	if isinstance(html, unicode):
		html = html.encode('utf-8')
	html_hash = md5.new(html).hexdigest()

	# check if the html matches a pre-read html
	# html_hash = md5.new(html.encode('utf-8')).hexdigest()
	if gush["html_hash"] == html_hash:
		print ("duplicate HTML - returning")
		return True

	print ("HTML new, inserting data")
	data = extract_data(html)
	for i in data:	
		i['gush_id']=gush_id
		
		print ("Inserting item: %s" % i)
		db.plans.insert(i)
		
	print ("updating gush html_hash, last_checked_at")
	gush["html_hash"] = html_hash
	gush["last_checked_at"] = datetime.datetime.now()
	db.gushim.save(gush)
