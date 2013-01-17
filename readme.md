This is the server part for http://niryariv.github.com/citymap-client

The code is Flask based, working with MongoDB as database, written to run on Heroku.

## Installation

    git clone https://github.com/niryariv/citymap-server.git
    cd citymap-server
    pip install -r requirements.txt
    python app.py

#### Create initial DB

    python create_db --force

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

## API

Currently only two API calls are supported.

Get block (gush) data:

    GET /gush/30035

    {"_id": {"$oid": "50ec3aa7e16ddfd10b275d01"}, "gush_id": "30035", "last_checked_at": {"$date": 1358175962596}, "html_hash": "041363772c628becdd339a16d5f7cf2a"}

Get plans for a block:

    GET /gush/30540/plans

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