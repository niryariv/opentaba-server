"""
The data from the MMI site includes a number of plans (around 220 as of Jan 2013) which appear in hundreds of blocks
("gushim"). This is clearly a bug on MMI's side, so we need to filter them out of the search results.
For this we keep a blacklist, which is a Mongo collection with one document consisting of an array of blacklisted plan
numbers. This script creates that blacklist.
"""

from app import *  # for DB stuff


# so, we used to do it all-mongo JS and then eval() that.
# But MongoHQ doesn't allow eval() on sandbox accts anymore, so re-implemented in Python and commenting the part below

# js = '''
# 	BLACKLIST_THRESHOLD = 99;
#
# 	t = db.plans.group({
# 		key: {'number' : true}, 
# 		initial: {gushim : []}, 
# 		reduce: function(doc, prev) { prev.gushim.push(doc.gush_id)},
# 		finalize: function(doc) { doc.total = doc.gushim.length }
# 	});
#
# 	var blacklist = new Array();
# 	t.forEach(
# 		function(d) { if (d.total > BLACKLIST_THRESHOLD) blacklist.push(d.number); }
# 	);
#
# 	db.blacklist.remove();
# 	db.blacklist.insert({blacklist : blacklist});
#
# '''
# print db.eval(js)

# Python version of the above

from bson.code import Code

blacklist = []
BLACKLIST_THRESHOLD = 99

reducer = Code(" function(doc, prev){ prev.gushim.push(doc.gush_id)	}")
finalizer = Code(" function(doc){	doc.total = doc.gushim.length }")

results = db.plans.group(key={"number": True}, initial={"gushim": []}, reduce=reducer, finalize=finalizer, condition={})

for r in results:
    if r['total'] > BLACKLIST_THRESHOLD:
        blacklist.append(r['number'])

db.blacklist.remove()
db.blacklist.insert({'blacklist': blacklist})
