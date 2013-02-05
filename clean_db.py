# The data from the MMI site includes a number of plans (around 220 as of Jan 2013) which appear in hundreds of blocks ("gushim").
# This is clearly a bug on MMI's side, so we need to filter them out of the search results
# For this we keep a blacklist, which is a Mongo collection with one document consisting of an array of blacklisted plan numbers
# This script creates that blacklist.

from app import * # for DB stuff

js = '''
	BLACKLIST_THRESHOLD = 99;

	t = db.plans.group({
		key: {'number' : true}, 
		initial: {gushim : []}, 
		reduce: function(doc, prev) { prev.gushim.push(doc.gush_id)},
		finalize: function(doc) { doc.total = doc.gushim.length }
	});

	var blacklist = new Array();
	t.forEach(
		function(d) { if (d.total > BLACKLIST_THRESHOLD) blacklist.push(d.number); }
	);

	db.blacklist.remove();
	db.blacklist.insert({blacklist : blacklist});

'''

print db.eval(js)