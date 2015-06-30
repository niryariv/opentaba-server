#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import *
from app import app
from nose.tools import eq_, assert_true


# get the test client for communicating with our flask app
testapp = app.test_client()


def setup_module(module):
    app.config['TESTING'] = True


def teardown_module(module):
    app.config['TESTING'] = False


def test_plan_mavat_link():
    # invalid plan id
    response = testapp.get('/plan/1014537xx/mavat')
    eq_(response.status_code, 400)

    # plan not found
    response = testapp.get('/plan/1/mavat')
    eq_(response.status_code, 404)

    # plan without mavat link
    response = testapp.get('/plan/1013207/mavat')
    eq_(response.status_code, 404)

    # valid plan !
    response = testapp.get('/plan/1014537/mavat')
    eq_(response.status_code, 200)
    msg = "http://mavat.moin.gov.il/MavatPS/Forms/SV4.aspx?tid=4" # the redirect url
    assert_true(msg in response.data)