#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import *
from app import app
from nose.tools import eq_, assert_true
from nose import with_setup
import json


# get the test client for communicating with our flask app
testapp = app.test_client()


def setup_module(module):
    app.config['TESTING'] = True


def teardown_module(module):
    app.config['TESTING'] = False


def test_root_working():
    response = testapp.get('/')
    eq_(response.status_code, 200)
    msg = "reached the server side"
    assert_true(msg in response.data)


def test_api_gushim():
    response = testapp.get('/gushim.json')
    print(dir(response))
    j = json.loads(response.data)
    eq_(len(j), 729)  # the correct number
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')


def test_api_get_gush():
    response = testapp.get('/gush/30649.json')
    j = json.loads(response.data)
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')
    eq_(sorted(j.keys()), ['_id', 'gush_id', 'json_hash', 'last_checked_at'])
    eq_(j['gush_id'], '30649')


def test_api_get_plan():
    response = testapp.get('/gush/30649/plans.json')
    j = json.loads(response.data)
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')

    # I don't know the correct number, since it's changes with each update, but it should be more then this
    assert_true(len(j) >= 10)

    sample = j[0]
	
    eq_(sorted(sample.keys()), [u'_id',
                                u'area',
                                u'committee_type',
                                u'day',
                                u'details_link',
                                u'essence',
                                u'files_link',
                                u'govmap_link',
                                u'gushim',
                                u'housing_units',
                                u'location_string',
                                u'mavat_code',
                                u'mavat_files',
                                u'mavat_meetings',
                                u'month',
                                u'nispahim_link',
                                u'number',
                                u'plan_id',
                                u'plan_type',
                                u'region',
                                u'status',
                                u'takanon_link',
                                u'tasrit_link',
                                u'year'])

    #eq_(sample['status'], u"פרסום בעיתונות להפקדה ")
    assert_true('30649' in sample['gushim'])
    msg = 'taba2.aspx'
    assert_true(msg in sample['details_link'])
    eq_(sample['takanon_link'], [u'http://mmi.gov.il/IturTabotData/takanonim/jerus/1013209.pdf'])
    # eq_(sample['essence'], u"השלמת קומה והרחבות דיור")


def test_api_wakeup():
    response = testapp.get('/wakeup')
    j = json.loads(response.data)
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')
    eq_(j, {"morning": "good"})
