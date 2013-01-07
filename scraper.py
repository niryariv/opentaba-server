from app import *
from tools.scrapelib import *
import md5


# accepts a gush object, scrapes date from gush URL and saves it into the plans collection
def scrape_gush(gush):

	gush_id = gush['gush_id']
	print "checking gush %s" % gush_id

	# check if the html matches a pre-read html
	html = get_gush_html(gush_id)

	# save in cache
	f = open("filecache/%s.html" % gush_id, "wb")
	f.write(html.encode('utf-8'))
	f.close()

	
	html_hash = md5.new(html.encode('utf-8')).hexdigest()
	print "html_hash: %s" % html_hash

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
