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
     `fab create_app:givataiim,"גבעתיים"`
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
  2. Add the data about the new municipality to the repository, then create the 
     new site. Run:
     `fab create_site:givataiim,"גבעתיים"`
  3. All changes are automatically made, committed and pushed. If you need to add
     more settings to the data/index.js, you can do it after and you will need to
     deploy the new municipality again (`fab -f client_fabfile.py deploy:givataiim`)
     All changes to data/index.js must be done in compliance to the [Municipality 
     Index File syntax](http://github.com/niryariv/opentaba-client/blob/master/DEPLOYMENT.md#municipality-index-file).
  4. Add a new hostname (subdomain) in your domain management control panel. Set
     the name to your municipality's name (givataiim for this example), record
     type to "CNAME (Alias)" and url to "<your-github-account>.github.io."ץ
     It will take a few minutes to make the link (DNS and Github).
