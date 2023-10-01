import json
import os.path
import requests
from log_setup import Logging
from program_data import PDApi
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""
"""
 mnode end point api calls
 https://mnodeip/mnode
"""


# set up logging
logmsg = Logging.logmsg()


# disable ssl warnings so the log doesn't fill up
requests.packages.urllib3.disable_warnings()


def about(repo):
    """ Get assets /mnode/#/about/routes.v1.about.get
        Populate the instance ABOUT
    """
    url = ('{}/mnode/1/about'.format(repo.base_url))
    json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
    if json_return:
        return json_return
    
class Assets():
    def __init__(self, repo):
        """ repo.parent_id
        """ 
        self.get_assets(repo)
        repo.parent_id = repo.assets[0]["id"]
                
    def get_assets(self, repo):
        """ Get assets mnode/#/assets/routes.v1.assets_api.get_assets
            Populate the instance CURRENT_ASSET_JSON
        """
        url = f'{repo.base_url}/mnode/1/assets'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return:
            repo.assets = json_return

    def addConfig(repo):
        """  Add config{} options """
        url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/'
        payload =  {"config":{"collector":{"noVerifyCert":"true","remoteHost":"monitoring.solidfire.com"}},"telemetry_active": True}
        status = PDApi.send_put_return_status(repo, url, payload)
        if status == 200:
            logmsg.info(f'Applied config \n {payload}')

    def get_asset_by_type(repo, url):
        """  get a list of assets by type """
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return:
            return json_return

    def post_asset(repo, url, payload):
        """  add an asset """
        logmsg.info(f'Adding asset id: {payload["ip"]}')
        response = PDApi.send_post_return_status(repo, url, payload)
        if response == 201:
                logmsg.info('\tSuccessfully added')
        if response == 409: 
                logmsg.info('\tStatus: 409 Already in inventory Skipping.')

    def delete_asset(repo, asset_type, asset_id):
        """  delete an asset """
        url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type["asset_type"]}/{asset_id}'
        logmsg.info(f'Removing asset id: {asset_id}')
        status = PDApi.send_delete_return_status(repo, url)
        if status == 204: 
            logmsg.info("\tSuccessfully deleted asset")
        else:
            logmsg.info("Error deleteing asset. See /var/log/mnode-support-util.log for details")

    def put_asset(repo, asset_type, asset_id, payload):
        """ update an asset """
        url = f'{repo.base_url}/mnode/1/assets/{repo.parent_id}/{asset_type}/{asset_id}'
        logmsg.info(f'Updating asset id: {asset_id}')
        status = PDApi.send_put_return_status(repo, url, payload)
        if status == 200: 
                logmsg.info("Successfully updated asset")

class Services():
    def get_services(repo):
        """ Get services status = all, helper = yes 
        return response body
        """
        
        url = f'{repo.base_url}/mnode/services?status=all&helper=true'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return:
            return json_return

    def put_deploy(repo):
        """ deploy Management Services from tar.gz file """
        url = f'{repo.base_url}/mnode/1/services/deploy'
        
        status = PDApi.send_put_return_status(repo, url, "")
        if status == 200:
            logmsg.info("Deploying new MS packages and services. Monitor docker ps until all services have restarted.")

    def get_service_log(repo, service, log):
        """ get service log """
        log = []
        
        url = f'{repo.base_url}/mnode/logs?lines=1000&service-name={service}&stopped=true'
        text = PDApi.send_get_return_text(repo, url, True)
        if text:
            log = text.splitlines()
            return log

class Settings():
    def get_settings(repo):
        """ get current settings """
        
        url = f'{repo.base_url}/mnode/settings'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return:
            return json_return

    def put_settings(repo):
        """ update settings """
        
        url = f'{repo.base_url}/mnode/2/settings'
        json_file = f'{repo.support_dir}support-mnode-settings.json'
        if os.path.isfile(json_file):
            json_input = open(json_file, "r")
            json_data = json.load(json_input)
            json_input.close()
            payload = {"mnode_fqdn": json_data["mnode_fqdn"],  "proxy_ssh_port": json_data["proxy_port"], "proxy_username": json_data["proxy_username"],"proxy_port": json_data["proxy_port"],"use_proxy": json_data["use_proxy"],"proxy_ip_or_hostname": json_data["proxy_ip_or_hostname"]}
            json_return = PDApi.send_put_return_json(repo, url, payload)
            if json_return:
                logmsg.info(f'Applying settings\n {json_return}')
