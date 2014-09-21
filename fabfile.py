"""
Fabfile encapsulating both the server and client fabfiles of opentaba since they now both reside
in the server repository
"""

from fabric.api import prompt, task


from scripts.client_fabfile import add_muni

from scripts.server_fabfile import create_server, delete_server, update_gushim_server, deploy_server, deploy_server_all, create_db
from scripts.server_fabfile import update_db, scrape_all, renew_db, renew_db_all, refresh_db, refresh_db_all


@task
def create_municipality(muni_name, display_name):
    """Run both server and client creation tasks automatically"""
    
    print 'This task is not recommended for use as it is too automatic. We advise you '
    print 'to follow the instructions found in DEPLOYMENT.md instead.'
    
    sure = ''
    while sure not in ['yes', 'no']:
        sure = prompt('Are you sure you want to use this task (yes/no) ?')
    
    if sure == 'yes':
        create_server(muni_name, display_name)
        add_muni(muni_name, display_name)
