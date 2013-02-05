from app import * # for DB stuff

# Remove the "total_gushim" field
#  db.plans.update( { total_gushim: { $exists: true } }, {$unset: { total_gushim : 1 } }, false, true) 

# DEPRECATED : other methods for handling blacklisting, proved to be less scalable than the one below.
# 	// Add plans appearing in > BLACKLIST_THRESHOLD gushim to blacklist
# 	t.forEach(
# 		function(d) { if (d.total > BLACKLIST_THRESHOLD) db.blacklist.update({number : d.number}, { $set : { total_gushim : d.total }}, { upsert : true }); }
# 	);
# 	// OR update the DB with total_gushim for plans > BLACKLIST_THRESHOLD 
# 	t.forEach(
# 		function(d) { if (d.total > BLACKLIST_THRESHOLD) db.plans.update({number : d.number}, { $set : { blacklisted : true }}, false, true); }
# 	);	

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

