import os
import datetime
import json
import pymongo

from flask import Flask
from flask import Response
from flask import abort, redirect, url_for

from rq import Queue
from worker import conn
import scraper

# from flask.ext.sqlalchemy import SQLAlchemy
# from flask.ext.pymongo import PyMongo

app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/citymap')
# db = SQLAlchemy(app)
# from models import *

MONGO_URL = os.environ.get('MONGOHQ_URL')

if MONGO_URL:	# on Heroku, get a connection
    m_conn = pymongo.Connection(MONGO_URL)   
    db = m_conn[urlparse(MONGO_URL).path[1:]]
else:			# work locally
    m_conn = pymongo.Connection('localhost', 27017)
    db = m_conn['citymap']
    app.debug = True # since we're local, keep debug on


q = Queue(connection=conn)

# Test stuff
# db.test_collection.insert({"testdoc":"totaltest"})
# print db.test_collection.find()[0]


# def json_results(result_set):
# 	return json.dumps([i.to_dict() for i in result_set])

@app.route('/_scrape/<gush_id>')
def scrape(gush_id):
	gush = db.gushim.find_one({"gush_id" : gush_id})
	if gush is None:
		abort(404)

	q.enqueue(scraper.scrape_gush, gush)
	return "ok"

@app.route('/_scrape/all')
def scrape_all():
	# gushim = db.gushim.find() #[:30]
	gushim = db.gushim.find({ "gush_id": { "$regex" : "300.*"} }) # sample

	for g in gushim:
		q.enqueue(scraper.scrape_gush, g)
	return "ok all "


@app.route('/')
def hello():
	return "Hello"


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



