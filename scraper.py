from app import *
from tools.scrapelib import *
import md5
import os

# accepts a gush object, scrapes date from gush URL and saves it into the plans collection
def scrape_gush(gush):

	gush_id = gush['gush_id']

	print "checking gush %s" % gush_id
	
	if RUNNING_LOCAL:
		local_cache = "filecache/%s.html" % gush_id
		if os.path.exists(local_cache):
			print "reading local file %s" % local_cache
			html = open(local_cache, 'r').read()
			# return html
		else:
			html = get_gush_html(gush_id)
			open(local_cache, 'wb').write(html.encode('utf-8'))

		html_hash = md5.new(html).hexdigest()

	else:
		html = get_gush_html(gush_id)
		html_hash = md5.new(html.encode('utf-8')).hexdigest()

	# check if the html matches a pre-read html
	# html_hash = md5.new(html.encode('utf-8')).hexdigest()
	if gush["html_hash"] == html_hash:
		print "duplicate HTML - returning"
		return True

	print "HTML new, inserting data"
	data = extract_data(html)
	for i in data:	
		i['gush_id']=gush_id
		
		print "Inserting item: %s" % i
		db.plans.insert(i)
		
	print "updating gush html_hash, last_checked_at"
	gush["html_hash"] = html_hash
	gush["last_checked_at"] = datetime.datetime.now()
	db.gushim.save(gush)
