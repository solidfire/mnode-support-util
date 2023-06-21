import json
import os.path
import urllib3
from get_token import get_token
from log_setup import Logging, MLog
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# mnode end point api calls
# https://mnodeip/mnode
#============================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

#============================================================
# disable ssl warnings so the log doesn't fill up
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def about(repo):
    #============================================================
    # Get assets /mnode/#/about/routes.v1.about.get
    # Populate the instance ABOUT
    url = ('{}/mnode/1/about'.format(repo.BASE_URL))
    json_return = PDApi.send_get_return_json(repo, url)
    if json_return:
        return json_return
    

class Assets():
    #============================================================
    # Get assets mnode/#/assets/routes.v1.assets_api.get_assets
    # Populate the instance CURRENT_ASSET_JSON
    def get_assets(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # Add config{} options
    def addConfig(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets/{}/'.format(repo.BASE_URL,repo.PARENT_ID))
        payload =  {"config":{"collector":{"noVerifyCert":"true","remoteHost":"monitoring.solidfire.com"}},"telemetry_active": True}
        status = PDApi.send_put_return_status(repo, url, payload)
        if status == 200:
            logmsg.info("Applied config \n {}".format(payload))
            

    #============================================================
    # get a list of assets by type
    def get_asset_by_type(repo, url):
        get_token(repo)
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # add an asset
    def post_asset(repo, url, payload):
        get_token(repo)
        logmsg.info("Adding asset id: {}".format(payload['ip']))
        status = PDApi.send_post_return_status(repo, url, payload)
        if status == 201:
                logmsg.info("Added {}".format(payload['ip'])) # host_name and/or ip from payload
        elif status == 409: 
                logmsg.info("{} Asset already exists in inventory. Skipping.".format(payload['host_name'])) 
                
    #============================================================
    # delete an asset
    def delete_asset(repo, asset_type, asset_id):
        url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.BASE_URL, repo.PARENT_ID, asset_type['asset_type'], asset_id))
        get_token(repo)
        logmsg.info("Removing asset id: {}".format(asset_id))
        status = PDApi.send_delete_return_status(repo, url)
        if status == 204: 
            logmsg.info("\tSuccessfully deleted asset")
        else:
            logmsg.info("Error deleteing asset. See /var/log/mnode-support-util.log for details")

    #============================================================
    # update an asset
    def put_asset(repo, asset_type, asset_id, payload):
        url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.BASE_URL,repo.PARENT_ID, asset_type, asset_id))
        logmsg.info("Updating asset id: {}".format(asset_id))
        status = PDApi.send_put_return_status(repo, url, payload)
        if status == 200: 
                logmsg.info("Successfully updated asset")

class Services():
    #============================================================
    # Get services status = all, helper = yes 
    # return response body
    def get_services(repo):
        get_token(repo)
        url = ('{}/mnode/services?status=all&helper=true'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # deploy Management Services from tar.gz file
    def put_deploy(repo):
        url = ('{}/mnode/1/services/deploy'.format(repo.BASE_URL))
        get_token(repo)
        status = PDApi.send_put_return_status(repo, url, "")
        if status == 200:
            logmsg.info("Deploying new MS packages and services. Monitor docker ps until all services have restarted.")

    #============================================================
    # get service log. 
    def get_service_log(repo, service, log):
        log = []
        get_token(repo)
        url = ('{}/mnode/logs?lines=1000&service-name={}&stopped=true'.format(repo.BASE_URL, service))
        text = PDApi.send_get_return_text(repo, url, debug=log)
        if text:
            log = text.splitlines()
            return log

class Settings():
    #============================================================
    # get current settings
    def get_settings(repo):
        get_token(repo)
        url = ('{}/mnode/settings'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # update settings
    def put_settings(repo):
        get_token(repo)
        url = ('{}/mnode/2/settings'.format(repo.BASE_URL))
        json_file = "{}support-mnode-settings.json".format(repo.SUPPORT_DIR)
        if os.path.isfile(json_file):
            json_input = open(json_file, "r")
            json_data = json.load(json_input)
            json_input.close()
            payload = {"mnode_fqdn": json_data['mnode_fqdn'],  "proxy_ssh_port": json_data['proxy_port'], "proxy_username": json_data['proxy_username'],"proxy_port": json_data['proxy_port'],"use_proxy": json_data['use_proxy'],"proxy_ip_or_hostname": json_data['proxy_ip_or_hostname']}
            json_return = PDApi.send_put_return_json(repo, url, payload)
            if json_return:
                logmsg.info("Applying settings\n {}".format(json_return))
