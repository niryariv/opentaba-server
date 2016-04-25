[![Build Status](https://travis-ci.org/niryariv/opentaba-server.png?branch=master)](https://travis-ci.org/niryariv/opentaba-server)

This is the server part for http://github.com/niryariv/opentaba-client

The code is Flask based, working with MongoDB as database, Uses redis to handle queue. written to run on Heroku.

## Installation

    git clone git@github.com:niryariv/opentaba-server.git
    cd opentaba-server
    virtualenv .
    pip install -r requirements.txt
    mkdir filecache
    python app.py

Notice that if you are running this on a local dev machine you need to have mongodb running and listening in port 27017
#### Create initial DB

Make sure mongo daemon (mongod) is running.

    mongo
    use citymap
    exit
    python scripts/create_db.py --force -m [all | <muni>]

#### Scrape data into DB

1. Queue scrape task
2. Run Heroku worker on tasks

Locally:

    redis-server
    python scrape.py -g [all | <gush_id>]
    python worker.py

On Heroku:

    heroku run python scrape.py -g [all | <gush_id>]
    heroku run worker

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
        "status": "פרסום תוקף ברשומות ",
        "tasrit_link": [
            "http://mmi.gov.il//IturTabotData/tabot/jerus/1011879_K.pdf",
            "http://mmi.gov.il//IturTabotData/tabot/jerus/1011879_M.pdf"
        ],
        "gush_id": "30540",
        "area": "ירושלים",
        "essence": "איצטדיון אולימפי לאומי לאתלטיקה",
        "files_link": [
            "/IturTabotData/download/jerus/1011879.zip"
        ],
        "nispahim_link": [
            "http://mmi.gov.il//IturTabotData/nispachim/jerus/1011879/100/תשריט עצים.pdf",
            "http://mmi.gov.il//IturTabotData/nispachim/jerus/1011879/38.pdf",
            "http://mmi.gov.il//IturTabotData/nispachim/jerus/1011879/4_1.pdf",
            "http://mmi.gov.il//IturTabotData/nispachim/jerus/1011879/4_2.pdf"
        ],
        "number": "מק/14177",
        "month": 8,
        "takanon_link": [
            "http://mmi.gov.il//IturTabotData/takanonim/jerus/1011879.pdf"
        ],
        "govmap_link": [],
        "year": 2012,
        "details_link": "taba4.asp?num=4&rec=4&gis=false",
        "_id": {
            "$oid": "50ec4420e16ddfd5a2fe7c0c"
        },
        "day": 2
    },
    {
        "status": "פרסום תוקף ברשומות ",
        "tasrit_link": [
            "http://mmi.gov.il//IturTabotData/tabot/jerus/1011319_K.pdf",
            "http://mmi.gov.il//IturTabotData/tabot/jerus/1011319_M.pdf",
            "http://mmi.gov.il//IturTabotData/tabot/jerus/1011319_T.pdf"
        ],
        "gush_id": "30540",
        "area": "ירושלים",
        "essence": "הוספת נתיב הסעה שלישי לשדרות מנחם בגין מרכז",
        "files_link": [
            "/IturTabotData/download/jerus/1011319.zip"
        ],
        "nispahim_link": [],
        "number": "2855/ב",
        "month": 8,
        "takanon_link": [
            "http://mmi.gov.il//IturTabotData/takanonim/jerus/1011319.pdf"
        ],
        "govmap_link": [],
        "year": 2011,
        "details_link": "taba4.asp?num=4&rec=2&gis=false",
        "_id": {
            "$oid": "50ec4420e16ddfd5a2fe7c0a"
        },
        "day": 31
    },
    ....
    ]

Get all blocks info (current just gush_id)

    GET /gushim.json

    [{"gush_id": "30019S"}, {"gush_id": "30000"}, {"gush_id": "30001"}, {"gush_id": "30002"}, {"gush_id": "30003"}, {"gush_id": "30004"}, {"gush_id": "30005"}, {"gush_id": "30006"}, {"gush_id": "30007"}, {"gush_id": "30008"}, {"gush_id": "30009"}, {"gush_id": "30010"}, {"gush_id": "30011"}, {"gush_id": "30012"}, {"gush_id": "30013"}, {"gush_id": "30014"}, {"gush_id": "30015"}, {"gush_id": "30016"}, {"gush_id": "30017"}, {"gush_id": "30018"}, {"gush_id": "30019"}, {"gush_id": "30020"}, {"gush_id": "30021"}, {"gush_id": "30022"}, {"gush_id": "30023"}, {"gush_id": "30024"}, {"gush_id": "30025"}, {"gush_id": "30026"}, {"gush_id": "30027"}, {"gush_id": "30028"}, {"gush_id": "30029"}, {"gush_id": "30030"}, {"gush_id": "30031"}, {"gush_id": "30032"}, {"gush_id": "30033"}, {"gush_id": "30034"}, {"gush_id": "30035"}, {"gush_id": "30036"}, {"gush_id": "30037"}, {"gush_id": "30038"}, {"gush_id": "30039"}, {"gush_id": "30040"}, {"gush_id": "30041"}, {"gush_id": "30042"}, {"gush_id": "30043"}, {"gush_id": "30044"}, {"gush_id": "30045"}, {"gush_id": "30046"}, {"gush_id": "30047"}, {"gush_id": "30048"}, {"gush_id": "30049"}, {"gush_id": "30050"}, {"gush_id": "30051"}, {"gush_id": "30052"}, {"gush_id": "30053"}, {"gush_id": "30054"}, {"gush_id": "30055"}, {"gush_id": "30056"}, {"gush_id": "30057"}, {"gush_id": "30058"}, {"gush_id": "30059"}, {"gush_id": "30060"}, {"gush_id": "30061"},
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
      <entry xml:base="http://opentaba-server.herokuapp.com/feed.atom">
        <title type="text">פארק עמק רפאים</title>
        <id>http://mmi.gov.il/IturTabot/taba4.asp?kod=3000&amp;MsTochnit=12222&amp;status=פרסום תוקף ברשומות </id>
        <updated>2013-11-28T00:00:00Z</updated>
        <link href="http://mmi.gov.il/IturTabot/taba4.asp?kod=3000&amp;MsTochnit=12222" />
        <author>
          <name>OpenTABA.info</name>
        </author>
        <content type="html">פרסום תוקף ברשומות 12222</content>
      </entry>
      <entry xml:base="http://opentaba-server.herokuapp.com/feed.atom">
        <title type="text">פארק עמק רפאים</title>
        <id>http://mmi.gov.il/IturTabot/taba4.asp?kod=3000&amp;MsTochnit=12222&amp;status=פרסום תוקף ברשומות </id>
        <updated>2013-11-28T00:00:00Z</updated>
        <link href="http://mmi.gov.il/IturTabot/taba4.asp?kod=3000&amp;MsTochnit=12222" />
        <author>
          <name>OpenTABA.info</name>
        </author>
        <content type="html">פרסום תוקף ברשומות 12222</content>
      </entry>
      ....
    </feed>
