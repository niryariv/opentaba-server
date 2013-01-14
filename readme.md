This is the server part for http://niryariv.github.com/citymap-client

The code is Flask based, working with MongoDB as database, written to run on Heroku.

### Installation

    git clone https://github.com/niryariv/citymap-server.git
    cd citymap-server
    pip install -r requirements.txt
    python app.py

### Create initial DB

    python create_db --force

### Scrape data into DB:

1. Queue scrape task
2. Run Heroku worker on tasks
	
Locally:

	redis-server
	python scrape.py -g [all | <gush_id>]
	python worker.py

On Heroku:

    heroku run python scrape.py -g [all | <gush_id>]
    heroku run worker
