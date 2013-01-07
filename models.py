from app import *
from sqlalchemy.dialects.postgresql import ARRAY


class Plan(db.Model):
	id 		= db.Column(db.Integer, primary_key=True, autoincrement=True)
	gush_id = db.Column(db.String, index=True)
	area 	= db.Column(db.String)
	number 	= db.Column(db.String, index=True)
	status 	= db.Column(db.String)
	date 	= db.Column(db.Date, index=True)
	essence = db.Column(db.String)
	details_link  = db.Column(db.String)

	takanon_link  = db.Column(ARRAY(db.String), default = [])
	tasrit_link   = db.Column(ARRAY(db.String), default = [])
	nispahim_link = db.Column(ARRAY(db.String), default = [])
	files_link 	  = db.Column(ARRAY(db.String), default = [])
	govmap_link   = db.Column(ARRAY(db.String), default = [])

	created_at = db.Column(db.Date, default = datetime.datetime.now())

	# turn to dictionary and clean up datetime / empty values as prep for jsoning
	def to_dict(self):
		d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		for i in d:
			if d[i] == None:
				d[i] = ''
			elif isinstance(d[i], datetime.date):
				d[i] = d[i].isoformat()
		return d


class Gush(db.Model):
	id 		= db.Column(db.Integer, primary_key=True, autoincrement=True)
	gush_id = db.Column(db.String, index=True)
	last_checked_at= db.Column(db.Date)
	html_hash	= db.Column(db.String)



# db.create_all()
# p = Plan(gush=1, area='area', number='number', status='status', date=datetime.datetime.now(), essence="essence", details_link ="http://details", takanon_link=['ht1', 'ht2'])
# db.session.add(p)
# db.session.commit()
# Plan.query.all()
# db.drop_all()

# json.dumps([i.to_dict() for i in Plan.query.all()])
