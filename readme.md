[![Build Status](https://travis-ci.org/niryariv/opentaba-server.png?branch=master)](https://travis-ci.org/niryariv/opentaba-server)

This is the server part for http://github.com/niryariv/opentaba-client

The code is Flask based, working with MongoDB as database, Uses redis to handle queue. written to run on Heroku.

## Installation
#### Manual
    git clone git@github.com:niryariv/opentaba-server.git
    cd opentaba-server
    virtualenv .
    pip install -r requirements.txt
    mkdir filecache
    python app.py

#### Docker
    git clone git@github.com:niryariv/opentaba-server.git
    cd opentaba-server
    docker build -t hasadna/opentaba-server .
    docker run -t -d -p 5000:5000 -v XMONGOX:/data/db hasadna/opentaba-server
    
_XMONGOX_: This will hold the Mongo database files on your local filesystem path (not in the docker container).
Provide an **absolute path** available on the local filesystem (e.g: _/mnt/data/db_).
it is possible to omit the _-v XMONGOX:/data/db_ but then it means that when the container exits and removed all the scraped data is lost.

You can _tail_ the output of the container and wait until the flask server is up by:

    docker logs -f CONTAINER_ID

_CONTAINER_ID_ is the _hasadna/opentaba-server_ container id found by running:

    docker ps

You can also run the container without starting the server ( _python app.py_ ) by adding _-e RUN_SERVER=0_ to the command:

    docker run -t -d -p 5000:5000 -e RUN_SERVER=0 -v XMONGOX:/data/db hasadna/opentaba-server

You can then _exec_ to the running container (see below) and run it manually.

## Create initial DB
#### Manual
Make sure mongo daemon (mongod) is running.

    mongo
    use citymap
    exit
    python scripts/create_db.py --force -m [all | <muni>]

#### Docker
Already done (with _-m all_) and not needed.

## Scrape data into DB
#### Manual
1. Queue scrape task
2. Run Heroku worker on tasks

Locally:

    redis-server
    python scrape.py -g [all | <gush_id>]
    python worker.py

On Heroku:

    heroku run python scrape.py -g [all | <gush_id>]
    heroku run worker

#### Docker
First fine the container Id (CONTAINER_ID) of the running instance ( _docker ps_ ). when you have it:
    
    docker exec -ti CONTAINER_ID /bin/bash
    cd /opt/opentaba-server
    python scrape.py -g [all | <gush_id>]
    python worker.py


##Testing

run the tests (needs ```pip install nose```):

    nosetests
or for a specifc test

    nosetests Tests/path/to/test

from the project root folder

##Production
###Architecture
The production environment is made up of a [Heroku](http://heroku.com) app per municipality
###Maintenance
Maintenance is done using [fabric](http://fabfile.org), by activating different tasks defined in fabfile.py
(for a list of all tasks, run `fab -l`, and for details about a specific task run `fab -d <task-name>`)
To execute a task, run: `fab task-name:arg1,arg2...` or `fab task-name:arg1=val1,arg2=val2...`
For step-by-step instructions on how to add a new municipality, check out [The Deployment Readme](DEPLOYMENT.md)

Main tasks: (for detailed information about these tasks and others, see [DEPLOYMENT.md](DEPLOYMENT.md))
+ create_server(muni_name, display_name) : create a new heroku app, set it up for running everything we need,
  push(deploy), run the create_db script for the given municipality, scrape all gushim, open scheduler dashboard
  to schedule a daily scraping.
+ delete_server(muni_name) : delete a heroku app.
+ deploy_server_all() : push all changes done in the local repository to all heroku apps with names that match
  our naming pattern. You can only deploy to apps if you are the owner or a collaborator.
+ scrape(muni_name, show_output=False) : scrape all gushim now in the given server. if show_output is False
  the heroku bash will be released and the scraping output will not be continuosly sent to your shell.

## API

Get block (gush) data:

    GET /gush/30035.json

    {"_id": {"$oid": "50ec3aa7e16ddfd10b275d01"}, "gush_id": "30035", "last_checked_at": {"$date": 1358175962596}, "json_hash": "041363772c628becdd339a16d5f7cf2a"}

Get plans for a block:

    GET /gush/30540/plans.json

    [
      {
        "gushim": [
          "30540"
        ],
        "housing_units": 0,
        "essence": "התוויה, סלילה והקמה של תוואי הרכבת הקלה",
        "number": "101-0209593",
        "month": 1,
        "year": 2017,
        "plan_id": 1014826,
        "area": "ירושלים",
        "mavat_meetings": [
          {
            "institute": "ועדה מחוזית לתכנון ולבניה מחוז ירושלים - ועדת משנה להתנגדויות",
            "date": "28/06/2016",
            "p_type": "unknown",
            "number": "2016040",
            "p_link": "http://mavat.moin.gov.il/MavatPS/Forms/Attachment.aspx?edid=77000153712813&edn=6467AAFEC7FCB52AC0015EDD49BA72FF0F58CBE314181F5497E0E34313A7A246"
          },
          {
            "institute": "ועדה מחוזית לתכנון ולבניה מחוז ירושלים - ועדת משנה להתנגדויות",
            "date": "14/06/2016",
            "p_type": "unknown",
            "number": "2016037",
            "p_link": "http://mavat.moin.gov.il/MavatPS/Forms/Attachment.aspx?edid=77000152680651&edn=C989465655D7B2DD7986BF46D64F9419B37B689FC7D782E61018C36AA9B746AA"
          }
        ],
        "takanon_link": [
          "/IturTabotData/takanonim/jerus/1014826.pdf"
        ],
        "status": "פרסום תוקף ברשומות",
        "nispahim_link": [
          "/IturTabotData/nispachim/jerus/1014826/46_1.pdf"
        ],
        "mavat_files": [
          {
            "type": "pdf",
            "link": "http://mavat.moin.gov.il/MavatPS/Forms/Attachment.aspx?edid=6000193188187&edn=D4572918B4DDD1DE100ED008AA05E6DE7A9E2385FFE1F11D1D44E86DFDA71FF8",
            "name": "תשריט מצב מוצע - תשריט מצב מוצע"
          }
        ],
        "plan_type": "מתאר מקומי",
        "govmap_link": [],
        "location_string": "הקו הירוק של הרכבת הקלה",
        "committee_type": "מחוזית",
        "day": 12,
        "mavat_code": "TOpflW7W09+sG7MxZz/tpkvl/K87CznXS0dQr1i1Q6kI3Jir4Lz+4ve6CeT8bKvXbvvKv8UiXvvF/MX49+VxhDxxRgEiRIniz/t8dLm8RY0=",
        "tasrit_link": [
          "/IturTabotData/tabot/jerus/1014826/מצב מאושר-גיליון 1.pdf"
        ],
        "files_link": [],
        "details_link": "http://apps.land.gov.il/iturTabot2/taba2.aspx?tbMerchav=102&tUniqueID=1&sSug=~&tblView=tblView_567f30260005&tbMsTochnit=101-0209593",
        "_id": {
          "$oid": "59c00e7ad02e544af9fe18ad"
        },
        "region": "ירושלים"
      },
      ....
    ]

Get all blocks info:

    GET /gushim.json

    [
      {
        "json_hash": "76c22121018934b5753c5f88a8e598ae",
        "_id": {
          "$oid": "59bd8ac6d02e5431278b4812"
        },
        "gush_id": "30540",
        "last_checked_at": {
          "$date": 1505769642818
        }
      },
      {
        "json_hash": "76c22121018934b5753c5f88a8e598ae",
        "_id": {
          "$oid": "59bd8ac6d02e5431278b4813"
        },
        "gush_id": "30541",
        "last_checked_at": {
          "$date": 1505769663818
        }
      },
      {
        "json_hash": "76c22121018934b5753c5f88a8e598ae",
        "_id": {
          "$oid": "59bd8ac6d02e5431278b4814"
        },
        "gush_id": "30542",
        "last_checked_at": {
          "$date": 1505769698818
        }
      }
      ....
    ]


Get an ATOM feed of recent plans (across all gushim):

    GET /feed.atom

    <?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title type="text">OpenTABA</title>
      <id>http://opentaba-server.herokuapp.com/feed.atom</id>
      <updated>2013-11-28T00:00:00Z</updated>
      <link href="http://opentaba-server.herokuapp.com/" />
      <link href="http://opentaba-server.herokuapp.com/feed.atom" rel="self" />
      <generator>Werkzeug</generator>
      <entry xml:base="http://opentaba-server-jerusalem.herokuapp.com/plans.atom">
        <title type="text">רח' ניימן שמואל 20,18,16,14 שכ' נווה יעקב</title>
        <id>רח' ניימן שמואל 20,18,16,14 שכ' נווה יעקב-פרסום תוקף ברשומות</id>
        <updated>2017-06-27T00:00:00Z</updated>
        <link href="http://apps.land.gov.il/iturTabot2/taba2.aspx?tbMerchav=102&amp;tUniqueID=3&amp;sSug=~&amp;tblView=tblView_5b012681d09e&amp;tbMsTochnit=101-0087650" />
        <author>
          <name>OpenTABA.info</name>
        </author>
        <link href="http://opentaba-server-jerusalem.herokuapp.com/plan/1015210/mavat" rel="related" title="מבא&quot;ת" />
        <content type="html">הרחבת יח"ד [פרסום תוקף ברשומות, 27/06/2017, 101-0087650]</content>
      </entry>
      <entry xml:base="http://opentaba-server-jerusalem.herokuapp.com/plans.atom">
        <title type="text">רח' זווין 28,30,32 שכ' נווה יעקב</title>
        <id>רח' זווין 28,30,32 שכ' נווה יעקב-פרסום בעיתונות להפקדה</id>
        <updated>2017-06-08T00:00:00Z</updated>
        <link href="http://apps.land.gov.il/iturTabot2/taba2.aspx?tbMerchav=102&amp;tUniqueID=8&amp;sSug=~&amp;tblView=tblView_5b012681d09e&amp;tbMsTochnit=101-0377861" />
        <author>
          <name>OpenTABA.info</name>
        </author>
        <link href="http://opentaba-server-jerusalem.herokuapp.com/plan/1015486/mavat" rel="related" title="מבא&quot;ת" />
        <content type="html">הרחבת יח"ד [»»פרסום בעיתונות להפקדה««, 08/06/2017, 101-0377861]</content>
      </entry>
      ....
    </feed>
