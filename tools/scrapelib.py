from bs4 import BeautifulSoup

import requests
import datetime
import re

# import pymongo
# from pymongo import MongoClient
# connection = MongoClient()
# db = connection.citymap
# gushim_col = db.gushim


SITE_ENCODING = 'windows-1255'

def url_for_gush(gush_id):
	return "http://mmi.gov.il/IturTabot/taba2.asp?Gush=%s&fromTaba1=true" % gush_id

# get HTML page for gush_id from the Minhal's website
def get_gush_html(gush_id):

	download_url = url_for_gush(gush_id)
	print download_url

	try:
		r = requests.get(download_url)
		if r.status_code != 200:
			raise Exception("Status code: %s" % r.status_code)
	except Exception, e:
		print "ERROR: %s" % e
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

	COLUMNS = {	
		"area" 	: '',
		"number" : '',
		"details_link" : '',
		"status": '',
		"date" 	: '',
		"essence" : '',
		"takanon_link" 	: [],
		"tasrit_link" 	: [],
		"nispahim_link" : [],
		"files_link" 	: [],
		"govmap_link" 	: []
	}

	s = BeautifulSoup(html, "lxml", from_encoding = SITE_ENCODING)

	table = s("table", "highLines")[0]

	for tr in table("tr", valign="top"):
		rec = COLUMNS.copy()
		# rec["gush"]		= gush
		rec["area"] 	= tr("td", width="80")[0].get_text(strip=True).encode('utf-8')
		rec["number"]	= tr("td", width="120")[0].get_text(strip=True).encode('utf-8')
		rec["details_link"] 	= tr("td", width="120")[0].a.get("href")
		
		rec["status"] 	= tr("td", width="210")[0].get_text(strip=True).encode('utf-8')
		
		matchdate=re.search(r'(\d+/\d+/\d+)', rec["status"])
		if matchdate:
			d = matchdate.group(1)
			rec["date"] = datetime.datetime.strptime(d, "%d/%m/%Y")
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
