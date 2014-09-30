##Deploy a New Municipality
(The examples use givataiim. You should change it to whatever municipality
you are deploying)

###Server
To deploy a scraper-server app for a brand new municipality, follow these steps:
  1. Make sure the geojson map file with the name of the municipality has 
     been added to [this repository](http://github.com/niryariv/israel_gushim)
  2. Add the new gush ids to the tools/gushim.py file, then create and configure 
     the new Heroku app. This will also scrape the municipality's plans for the 
     first time. Run:
     `fab create_server:givataiim,"גבעתיים"`
  3. When the task finishes running, a browser window (or tab) will be open with 
     the new app's scheduler dashboard. Add a new scheduled task with the 
     command: "python scrape.py -g all ; python worker.py" (without both "), 
     leave it at 1X dyno, set it to run daily and set the next run for 4:00 AM.
  4. Scraping is being done in the background. Depending on how many gushim and 
     plans your municipality has, this can take anywhere from about 15 minutes 
     to a few hours. When it's done all plans will be scraped and your new server 
     will be ready to work with.
  5. The display name for the municipality (as can be seen in the title of the 
     plans atom feed) is set automatically by the fabric task. If you want to 
     edit it, you just need to set the MUNICIPALITY_NAME environment variable 
     of the heroku app like so: 
     `heroku config:set MUNICIPALITY_NAME="גבעתיים" --app opentaba-server-givataiim`

###Client
To deploy a website for a brand new municipality, follow these steps:
  1. Make sure both the geojson and topojson files with the name of the municipality
     have been added to [this repository](http://github.com/niryariv/israel_gushim)
  2. Run: `fab create_client:givataiim,"גבעתיים"`
  3. All changes are automatically made, committed and pushed. If you need to add
     more settings to the munis.js, you can do it after and you will need to
     commit and push the file again.
     All changes to munis.js must be done in compliance to the [Municipality 
     Index File syntax](http://github.com/niryariv/opentaba-client/blob/master/DEPLOYMENT.md#municipality-index-file).

##All Fabric Tasks
###Server
+ create_server(muni_name, display_name) - Create a new heroku app with all the
  needed addons. Set app's display name (MUNICIPALITY_NAME env var). Call 
  update_gushim_server so the new server will have its municipality's gushim. Deploy 
  to the new app. Create_db and scrape data for the first time. Open heroku-scheduler
  dashboard because we can't set a scheduled task automatically. After this task
  is run and scraping ends, the new server is fully ready to start working with.
+ delete_server(muni_name, ignore_errors=False) - Delete a heroku app.
  ignore_errors is set to false by default because if this task fails it most
  likely means the app does not exist to begin with.
+ update_gushim_server(muni_name) - Update the [tools/gushim.py](tools/gushim.py) file with the
  gushim of a new municipality or the updated ones of an existing municipality.
  This task downloads the gush map file from [israel_gushim](http://github.com/niryariv/israel_gushim), parses its data, and
  if there are new gushim it updates the [tools/gushim.py](tools/gushim.py) file and the 
  [Tests/functional_tests/test_return_json.py](Tests/functional_tests/test_return_json.py) file (with the new amount of gushim),
  commits and pushes on the master branch. Note that this task does not deploy
  anywhere, and the new gushim data will not exist on active servers until you
  deploy changes to them.
+ deploy_server(muni_name) - Push the current repository's changes to the
  municipality's heroku app.
+ deploy_server_all() - Find servers by looking at your `heroku list` and filtering
  out the ones that don't match our server name pattern. Run deploy_server task
  on each of the discovered servers.
+ create_db(muni_name) - Run the [tools/create_db.py](tools/create_db.py) script on the given
  municipality's heroku app. Will only create db for the given municipality's
  gushim.
+ update_db(muni_name) - Run the [tools/update_db.py](tools/update_db.py) script on the given
  municipality's heroku app. Will only update db for the given municipality's
  gushim.
+ scrape(muni_name, show_output=False) - Run the [scrape.py](scrape.py) script on the
  given municipality's heroku app. All of the municipality's gushim will
  be scraped. show_output=True will bind your shell to the app's and give
  all the output in real time. False will run it in detached mode.
+ renew_db(muni_name) - Run the create_db and then the scrape tasks on
  the given municipality's heroku app.
+ renew_db_all() - Find servers by looking at your `heroku list` and filtering
  by our naming pattern. Run the renew_db task on each one discovered.
+ refresh_db(muni_name) - Run the update_db and then the scrape tasks on
  the given municipality's heroku app.
+ refresh_db_all() - Find servers by looing at your `heroku list` and filtering
  by our naming pattern. Run the refresh_db task on each one discovered.

###Client
+ create_client(muni_name, display_name='') - For client creation, all we need
  is for the municipality to exist in the [munis.js](munis.js) file. This task downloads
  the gush map for the municipality from [israel_gushim](http://github.com/niryariv/israel_gushim), parses its data and
  checks if changes were made. If there are changes they will be committed
  and pushed on the master branch, then merged and pushed on the gh-pages
  branch to "publish" to every municipality's site (which are all in fact
  one site). display_name is only optional when updating an existing
  municipality's data, not for new municipalities.
