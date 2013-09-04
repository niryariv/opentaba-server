#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import *
from flask.ext.testing import TestCase
from nose.tools import eq_

class Json_test(TestCase):

    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_get_gush(self):
        response = self.client.get("/gush/30035")
        eq_(response, 
{"_id": {"$oid": "50ec3aa7e16ddfd10b275d01"}, "gush_id": "30035", "last_checked_at": {"$date": 1358175962596}, "html_hash": "041363772c628becdd339a16d5f7cf2a"})

    def test_get_block(self):
        response = self.client.get("/gush/30540/plans")
        data = response.json() #maybe should be without the () to be a method
        print(len(data))
        eq_(len(data),3)
        d1 = data[0]
        eq_(len(d1['tasrit_link']),2)
        eq_(d1['tasrit_link'][0],'http://mmi.gov.il//IturTabotData/tabot/jerus/1011879_K.pdf')
        eq_(d1['gush_id'],"30540")
        eq_(d1['area'],u"ירושלים")
        eq_(d1['takanon_link'][0],'http://mmi.gov.il//IturTabotData/takanonim/jerus/1011879.pdf')



