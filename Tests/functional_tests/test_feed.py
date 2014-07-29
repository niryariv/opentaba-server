#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import *
from app import app
from nose.tools import eq_, assert_true
from nose import with_setup
from lxml import etree


# get the test client for communicating with our flask app
testapp = app.test_client()


def setup_module(module):
    app.config['TESTING'] = True


def teardown_module(module):
    app.config['TESTING'] = False


def test_basic_feed_sane():
    response = testapp.get('/plans.atom')
    eq_(response.status_code, 200)

    # Check that the XML tree is parsable and is an ATOM feed
    tree = etree.fromstring(response.data)
    eq_("{http://www.w3.org/2005/Atom}feed", tree.tag)


def test_gush_feed_sane_single():
    response = testapp.get('/gush/28108/plans.atom')
    eq_(response.status_code, 200)

    # Check that the XML tree is parsable and is an ATOM feed
    tree = etree.fromstring(response.data)
    eq_("{http://www.w3.org/2005/Atom}feed", tree.tag)


def test_gush_feed_sane_multi():
    response = testapp.get('/gush/28108,28107/plans.atom')
    eq_(response.status_code, 200)

    # Check that the XML tree is parsable and is an ATOM feed
    tree = etree.fromstring(response.data)
    eq_("{http://www.w3.org/2005/Atom}feed", tree.tag)


def test_gush_feed_sane_single():
    response = testapp.get('/gush/28108/plans.atom')
    eq_(response.status_code, 200)

    # Check that the XML tree is parsable and is an ATOM feed
    tree = etree.fromstring(response.data)
    eq_("{http://www.w3.org/2005/Atom}feed", tree.tag)


def test_gush_feed_sane_multi():
    response = testapp.get('/gush/28108,28107,28106/plans.atom')
    eq_(response.status_code, 200)

    # Check that the XML tree is parsable and is an ATOM feed
    tree = etree.fromstring(response.data)
    eq_("{http://www.w3.org/2005/Atom}feed", tree.tag)
