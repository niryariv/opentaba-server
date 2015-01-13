##Deploying a New Municipality
(The examples use Holon. You should change it to whatever municipality
you are deploying)

###Server
To deploy a server/database for a new municipality, follow these steps:
  1. Make sure the GeoJSON map file with the name of the municipality has 
     been added to the [map repository](http://github.com/niryariv/israel_gushim)
  2. Run `fab create_server:holon,"חולון"`. This will add the new gush ids to the lib/gushim.py file, create & configure the new Heroku app / MongoDB, and finally run the scraper to get all municipality's plans. 
  3. When the task finishes running, a browser window (or tab) will be open with 
     the new app's scheduler dashboard. Add a new scheduled task with the 
     command: `python scrape.py -g all ; python worker.py`. Do not change dyno settings.
  4. Data scraping takes place in the background. Depending on how many plans the new municipality has, this can take anywhere from a few minutes to several hours.
  5. The display name for the municipality (as can be seen in the title of the 
     plans Atom feed) is set in by the `fab create_server` (in the example above, "חולון". To edit it later, you'll need to set the MUNICIPALITY_NAME environment variable of the Heroku app, like so: 
     `heroku config:set MUNICIPALITY_NAME="חולון רבתי" --app opentaba-server-holon`

###Client
Unlike the server side, the client uses the same code for all municipalities. Deploying a new municipality just means adding it's information to the `munis.js` file. 

To deploy a new municipality, run: `fab create_client:holon,"חולון"` after the server was created. 

To change client configuration, you can edit `munis.js` manually later on, according to the [Municipality 
     Index File syntax](http://github.com/niryariv/opentaba-client/blob/master/DEPLOYMENT.md#municipality-index-file).

##Automatic Facebook and Twitter Posting
The server is able to post a plan's content to a Facebook page and Twitter feed every time a plan is created or updated, using a running instance of [opentaba-poster](https://github.com/hasadna/opentaba-poster).
To enable this feature, a poster must be registered with the needed tokens on the opentaba-poster instance, the opentaba-poster url and poster id must be set as 
environment variables on the opentaba-server, and lastly it is possible to register the Facebook page and Twitter feed in the client to have the municipality's
page link to them.
It is possible to enable Facebook only, Twitter only or both.

###Registering a New Poster
To register a new poster You must discover the page id and its access token for Facebook and the token and token secret for Twitter, and insert them in a new
document into the opentaba-poster instance's database.
You can do it manually, finding the necessary tokens using scripts available in the opentaba-poster repository, or use a fabric task provided in this repository:
`add_new_poster:poster_app_name,poster_desc='',fb_app_id=None,fb_app_secret=None,tw_con_id=None,tw_con_secret=None`
This task will do most of the work automatically (except authorize the Facebook and Twitter apps to use your accounts) and will output the new poster's id.
desc is not needed but will be useful to identify different posters in the database, and you must provide at least one of the couple of fb\tw parameters.

###Making an opentaba-server Post
To enable social posting, we must be configured to work with an instance of opentaba-poster, and supply it with out poster id.
This can be done using a fabric task, once we are sure we are defined as a poster on the opentaba-poster app:
`fab set_poster:muni_name,poster_base_url,poster_id`
example:
`fab set_poster:holon,http://poster.service.com/,holon_id`

It can also be done manually - just set the two environment variables -
`POSTER_SERVICE_URL` must be set to the url of the opentaba-poster app, and `POSTER_ID` must be set to our assigned id, eg:
```
heroku config:set POSTER_SERVICE_URL="http://poster.service.com/" --app opentaba-server-holon
heroku config:set POSTER_ID="holon_id" --app opentaba-server-holon
```

###Linking To The Social Pages From The Municipality's Page
Finally (and optionally), it is possible to link from the municipality's [opentaba-client](http://github.com/niryariv/opentaba-client) page to the Facebook page and Twitter
feed its plans are being published to using the top-right corner links.
This can be done with a fabric task:
`update_client_social_links:muni_name,facebook_link='',twitter_link=''`
(notice that empty links will not be ignored, but will instead be set to empty so the link will not appear)
Or it can be done manually by editing the [muni.js](http://github.com/niryariv/opentaba-client/blob/master/munis.js) file in opentaba-client and adding the links under your municipality.
Key names are `fb_link` and `twitter_link`, as can be seen in Jerusalem's entry.

##All Fabric Tasks
###Server
+ `fab create_server:muni_name, "display_name"`
  Create a new heroku app with all the
  needed addons. Set app's display name (MUNICIPALITY_NAME env var). Call 
  update_gushim_server so the new server will have its municipality's gushim. Deploy 
  to the new app. Create_db and scrape data for the first time. Open heroku-scheduler
  dashboard because we can't set a scheduled task automatically. After this task
  is run and scraping ends, the new server is fully ready to start working with.
  
+ `fab delete_server:muni_name,<ignore_errors True|False>` Delete a heroku app.
  ignore_errors is set to false by default because if this task fails it most
  likely means the app does not exist to begin with.

+ `fab update_gushim_server:muni_name` Update the [lib/gushim.py](lib/gushim.py) file with the
  gushim of a new municipality or the updated ones of an existing municipality.
  This task downloads the gush map file from [israel_gushim](http://github.com/niryariv/israel_gushim), parses its  data, and if there are new gushim it updates the [lib/gushim.py](lib/gushim.py) file and the 
  [Tests/functional_tests/test_return_json.py](Tests/functional_tests/test_return_json.py) file (with the new amount of gushim), commits and pushes on the master branch. Note that this task does not deploy
  anywhere, and the new gushim data will not exist on active servers until you
  deploy changes to them.

+ `fab deploy_server:muni_name` Push the current repository's changes to the
  municipality's heroku app.

+ `fab deploy_server_all` Find servers by looking at your `heroku list` and filtering
  out the ones that don't match our server name pattern. Run deploy_server task
  on each of the discovered servers.
+ `fab create_db:muni_name` Run the [scripts/create_db.py](scripts/create_db.py) script on the given
  municipality's heroku app. Will only create db for the given municipality's
  gushim.
+ `fab update_db:muni_name` Run the [scripts/update_db.py](scripts/update_db.py) script on the given
  municipality's heroku app. Will only update db for the given municipality's
  gushim.
+ `fab scrape:muni_name,<show_output=False|True>` Run the [scrape.py](scrape.py) script on the
  given municipality's heroku app. All of the municipality's gushim will
  be scraped. show_output=True will bind your shell to the app's and give
  all the output in real time. False will run it in detached mode.
+ `fab renew_db:muni_name` Drop the current DB, re-create it using create_db and run scrape tasks
+ `fab renew_db_all` Find servers by looking at your `heroku list` and filtering
  by our naming pattern. Run the renew_db task on each one discovered.
+ `fab refresh_db:muni_name` Update the DB with new gushim via update_db and run scrape tasks
+ `fab refresh_db_all` Find servers by looing at your `heroku list` and filtering
  by our naming pattern. Run the refresh_db task on each one discovered.
+ `fab sync_poster:muni_name,min_date` Run the [scripts/sync_poster.py](scripts/sync_poster.py) script on the given
  municipality's heroku app. min_date is the minimum date of plans to post, 
  and should be of the format: 1/1/2015.
+ `fab set_poster:muni_name,poster_base_url,poster_id` Set the required environment variables so
  that the opentaba-server instance can communicate with an opentaba-poster one and post its plans 
  to social media.

###Client
+ `fab create_client:muni_name,"display_name"` For client creation, all we need
  is for the municipality to exist in the [munis.js](munis.js) file. This task downloads
  the gush map for the municipality from [israel_gushim](http://github.com/niryariv/israel_gushim), parses its data and
  checks if changes were made. If there are changes they will be committed
  and pushed on the master branch, then merged and pushed on the gh-pages
  branch to "publish" to every municipality's site (which are all in fact
  one site). display_name is only optional when updating an existing
  municipality's data, not for new municipalities.
+ `fab update_client_social_links:muni_name,facebook_link='',twitter_link=''` Update the client's
  muni.js with links to Facebook, Twitter or both pages for the given municipality, then commit 
  and push the changes to publish them.

###Poster
+ `fab add_new_poster:poster_app_name,poster_desc='',fb_app_id=None,fb_app_secret=None,tw_con_id=None,tw_con_secret=None`
  Create a new poster record on an opentaba-poster server. Facebook details, Twitter details or both can be given.
  This task will attempt to authorize you on the given social networks and get the necessary tokens for you, then
  it will connect to the poster's database and add a new poster record for the given Facebook page and/or Twitter 
  account. It will eventually return a poster id which you can set on an opentaba-server instance to have it post 
  its plans through the opentaba-poster server.
