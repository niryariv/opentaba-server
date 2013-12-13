#place holder for unittesting scraper
from flask import *
from app import app
from nose.tools import eq_, assert_true
from nose import with_setup
from tools.scrapelib import scrape_gush
import os

testapp = app.test_client()

def setup():
  app.config['TESTING'] = True
  RUNNING_LOCAL = True

def teardown():
  app.config['TESTING'] = False
  RUNNING_LOCAL = False

@with_setup(setup, teardown)
def test_scrape_wellformed_html():
  RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))
  fixture = {'html_hash':'aaaa'} #mocking the hash

  fixture['gush_id'] = 'current.fixed'
  data = scrape_gush(fixture, RUN_FOLDER)
  eq_(len(data),10)
  eq_(data[0]['year'],2010)
  eq_(len(data[0]['files_link']),1)

  # ee

@with_setup(setup, teardown)
def test_scrape_missing_open_tr():
  #
  RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))

  fixture = {'html_hash':'aaaa'} #mocking the hash
  fixture['gush_id'] = 'current.fixed'
  data = scrape_gush(fixture, RUN_FOLDER)
  eq_(len(data),10)
  eq_(data[0]['year'],2010)
  eq_(len(data[0]['files_link']),1)


@with_setup(setup, teardown)
def test_scrape_missing_closing_tr():
  #s
  RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))

  fixture = {'html_hash':'aaaa'} #mocking the hash
  fixture['gush_id'] = 'current.fixed'
  data = scrape_gush(fixture, RUN_FOLDER)
  eq_(len(data),10)
  eq_(data[0]['year'],2010)
  eq_(len(data[0]['files_link']),1)


@with_setup(setup, teardown)
def test_scrape_non_standard_attribute():
  #
  RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))

  fixture = {'html_hash':'aaaa'} #mocking the hash
  fixture['gush_id'] = 'current.fixed'
  data = scrape_gush(fixture, RUN_FOLDER)
  eq_(len(data),10)
  eq_(data[0]['year'],2010)
  eq_(len(data[0]['files_link']),1)


@with_setup(setup, teardown)
def test_scrape_non_standard_tag():
  #
  RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))

  fixture = {'html_hash':'aaaa'} #mocking the hash
  fixture['gush_id'] = 'current.fixed'
  data = scrape_gush(fixture, RUN_FOLDER)
  eq_(len(data),10)
  eq_(data[0]['year'],2010)
  eq_(len(data[0]['files_link']),1)


@with_setup(setup, teardown)
def test_scrape_quote_mark():
  #when quote mark appears in the middle of a string
  fixture = {'html_hash':'aaaa'} #mocking the hash
  fixture['gush_id'] = 'current.fixed'
  RUN_FOLDER = os.path.dirname(os.path.realpath(__file__))
  data = scrape_gush(fixture, RUN_FOLDER)
  eq_(len(data),10)
  eq_(data[0]['year'],2010)
  eq_(len(data[0]['files_link']),1)

#@with_setup(setup, teardown)
#def test_scrape_mimetype():
  #
  #fixture = {'gush_id':'non.standard.attribute'}
  #data = scrape_gush(fixture, RUN_FOLDER)

