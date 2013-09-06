#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import *
from app import app
from nose.tools import eq_, assert_true
from nose import with_setup
import json

testapp = app.test_client()

def setup():
    app.config['TESTING'] = True

def teardown():
    app.config['TESTING'] = False

@with_setup(setup, teardown)
def test_root_working():
    response = testapp.get('/')
    eq_(response.status_code,200)
    msg = "reached the server side"
    assert_true(msg in response.data)

@with_setup(setup, teardown)
def test_api_gushim():
    response = testapp.get('/gushim')
    print(dir(response))
    j = json.loads(response.data)
    eq_(len(j), 644) #the correct number
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')

@with_setup(setup, teardown)
def test_api_get_gush():
    response = testapp.get('/gush/30035')
    j = json.loads(response.data)
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')
    eq_(j.keys(), ['_id','gush_id', 'last_checked_at', 'html_hash'])
    eq_(j['gush_id'], '30035')

@with_setup(setup, teardown)
def test_api_get_plan():
    response = testapp.get('/gush/30035/plans')
    j = json.loads(response.data)
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')
    #eq_(len(j), 47) # The correct number
    sample = j[0]
    eq_(sample.keys(),[u'status',
                        u'tasrit_link',
                        u'gush_id',
                        u'area',
                        u'essence',
                        u'files_link',
                        u'nispahim_link',
                        u'number',
                        u'month',
                        u'takanon_link',
                        u'govmap_link',
                        u'year',
                        u'details_link',
                        u'_id',
                        u'day'])
    eq_(sample['status'], u"פרסום בעיתונות להפקדה ")
    eq_(sample['gush_id'], '30035')
    eq_(sample['details_link'], u'taba4.asp?num=249&rec=79&gis=false')
    eq_(sample['takanon_link'], [])
    eq_(sample['essence'], u"השלמת קומה והרחבות דיור")


@with_setup(setup, teardown)
def test_api_wakeup():
    response = testapp.get('/wakeup')
    j = json.loads(response.data)
    eq_(response.status_code, 200)
    eq_(response.mimetype, 'application/json')
    eq_(j, {"morning": "good"})

