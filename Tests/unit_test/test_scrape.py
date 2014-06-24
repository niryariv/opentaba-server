#place holder for unittesting scraper
from flask import *
from app import app
from nose.tools import eq_, assert_true
from nose import with_setup
from tools.scrapelib import scrape_gush
import os

testapp = app.test_client()
fixture = None
RUNNING_LOCAL = None
RUN_FOLDER = None


def setup():
    global fixture, RUNNING_LOCAL, RUN_FOLDER
    fixture = {'json_hash': 'aaaa'} # mocking tha hash
    RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))
    app.config['TESTING'] = True
    RUNNING_LOCAL = True


def teardown():
    app.config['TESTING'] = False
    RUNNING_LOCAL = False
    fixture = None


@with_setup(setup, teardown)
def test_scrape_wellformed_json():
    fixture['gush_id'] = '30649'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 35)
    eq_(data[0]['year'], 2006)
    eq_(len(data[0]['files_link']), 1)

    # ee


@with_setup(setup, teardown)
def test_scrape_empty_result():
    #when quote mark appears in the middle of a string
    fixture['gush_id'] = 'empty'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 0)
    
"""   
@with_setup(setup, teardown)
def test_scrape_quote_mark():
    #when quote mark appears in the middle of a string
    fixture['gush_id'] = '30649.bad.quote.mark'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 34)
    eq_(data[0]['year'], 6)
    eq_(len(data[0]['files_link']), 1)
"""

"""
@with_setup(setup, teardown)
def test_scrape_missing_open_tr():
    #

    fixture['gush_id'] = 'current.fixed'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 10)
    eq_(data[0]['year'], 2010)
    eq_(len(data[0]['files_link']), 1)


@with_setup(setup, teardown)
def test_scrape_missing_closing_tr():
    #s

    fixture['gush_id'] = 'current.fixed'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 10)
    eq_(data[0]['year'], 2010)
    eq_(len(data[0]['files_link']), 1)


@with_setup(setup, teardown)
def test_scrape_non_standard_attribute():
    #
    fixture['gush_id'] = 'current.fixed'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 10)
    eq_(data[0]['year'], 2010)
    eq_(len(data[0]['files_link']), 1)


@with_setup(setup, teardown)
def test_scrape_non_standard_tag():
    #
    fixture['gush_id'] = 'current.fixed'
    data = scrape_gush(fixture, RUN_FOLDER)
    eq_(len(data), 10)
    eq_(data[0]['year'], 2010)
    eq_(len(data[0]['files_link']), 1)
"""

#@with_setup(setup, teardown)
#def test_scrape_mimetype():
#
#fixture = {'gush_id':'non.standard.attribute'}
#data = scrape_gush(fixture, RUN_FOLDER)

