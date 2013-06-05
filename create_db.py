from app import *
from tools.gushim import GUSHIM
# from models import *
# from flaskr import init_db

from optparse import OptionParser

parser = OptionParser()
parser.add_option("--force", dest="force", default=False, action="store_true", help="delete existing dbs")

(options, args) = parser.parse_args()

if not options.force:
	print "This script will delete the gushim and plans collection. To make sure this isn't running by mistake, run this with --force"
	exit()

# print "Deleting db.gushim and db.plans"
db.gushim.drop()
db.plans.drop()

db.gushim.create_index([('gush_id', 1)], unique=True)

bad_gushim = [30160, 30343, 30361, 0]

for g in GUSHIM:
	if g["properties"]["Name"]:
		try:
			gush_id = int(g["properties"]["Name"])
		except ValueError:
			continue

		# some gushim are bad, so skip them
		if gush_id in bad_gushim:
			continue

		for ring in range(len(g["geometry"]["coordinates"])):
			newcoords = []
			for coord in g["geometry"]["coordinates"][ring]:
				#print coord[0], coord[1]
				newcoords.append([coord[0], coord[1]])

			#if newcoords[-1][0] == newcoords[0][0] and newcoords[-1][1] == newcoords[0][1]:
			#	newcoords = newcoords[:-1]
			
			g["geometry"]["coordinates"][ring] = newcoords

		print "inserting gush number ", gush_id, "number of coords", len(g["geometry"]["coordinates"][0])
		db.gushim.insert({
			'gush_id'	: gush_id,
			'html_hash' : '',
			'last_checked_at': '',
			'gush_geo': g["geometry"]
		})

print "Inserted %d gushim" % (len(GUSHIM))

#db.gushim.create_index([("gush_geo", pymongo.GEOSPHERE)])
		

db.plans.create_index([
	('gush_id', pymongo.ASCENDING),
	('year'	  , pymongo.DESCENDING),
	('month'  , pymongo.DESCENDING),
	('day'	  , pymongo.DESCENDING),
	('number' , pymongo.ASCENDING),
	('essence', pymongo.ASCENDING)
	], unique = True) #, drop_dups = True)

db.blacklist.insert({'blacklist' : []})
