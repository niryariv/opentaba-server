##Deploy a New Municipality
To deploy a scraper-server app for a brand new municipality, follow these steps:
(The steps use givataiim as example. You should change that to whatever
municipality you are deploying)
1. Make sure the geojson map file with the name of the municipality has 
   been added to [this repository](http://github.com/niryariv/israel_gushim)
2. Add the new gush ids to the tools/gushim.py file:
   `fab add_gushim:givataiim,גבעתיים`
3. The changes will be made locally and not comitted so you can review them.
   If all looks good, commit the changes and push to origin.
4. Now create and configure the new Heroku app. This will also scrape the 
   municipality's plans for the first time. Run:
   `fab create_app:givataiim`
5. When the task finishes running, a browser window (or tab) will be open with 
   the new app's scheduler dashboard. Add a new scheduled task with the 
   command: "python scrape.py -g all ; python worker.py" (without both "), 
   leave it at 1X dyno, set it to run daily and set the next run for 4:00 AM.
6. Scraping is being done in the background. Depending on how many gushim and 
   plans your municipality has, this can take anywhere from about 15 minutes 
   to a few hours. When it's done all plans will be scraped and your new server 
   will be ready to work with.
