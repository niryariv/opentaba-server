import os
import datetime
import json

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Response

from flask import jsonify


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/')

db = SQLAlchemy(app)

from models import *


def json_results(result_set):
	return json.dumps([i.to_dict() for i in result_set])


@app.route('/')
def all():
	r = Plan.query.all()
	# return jsonify([i.to_dict() for i in result_set])
	js = json_results(r)
	resp = Response(js, status=200, mimetype='application/json')
	resp.headers['Access-Control-Allow-Origin'] = '*'

	return resp
	# return out


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)



