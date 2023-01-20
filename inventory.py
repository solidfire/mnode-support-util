import json
import requests
from get_token import get_token
from log_setup import Logging
from mnode import AssetMgmt

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# Inventory end point tasks
#============================================================

class Inventory(object):
    def refresh_inventory(repo):
        get_token(repo)
        AssetMgmt.get_parent_id(repo)
        url = ('{}/inventory/1/installations/{}?refresh=true'.format(repo.URL,repo.PARENT_ID))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_WRITE, data='{}', verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                logmsg.debug(json.loads(response.text))
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def get_inventory(args, repo):
        get_token(repo)
        AssetMgmt.get_parent_id(repo)
        url = ('{}/inventory/1/installations/{}?refresh=false'.format(repo.URL,repo.PARENT_ID))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data='{}', verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                repo.inventory_get = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def get_compute_upgrades(args, repo):
        get_token(repo)
        if not repo.PARENT_ID:  
            AssetMgmt.get_current_assets(repo)
        try:
            url = ('{}/inventory/1/installations/{}/compute/upgrades?refresh=false'.format(repo.URL,repo.PARENT_ID))
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data='{}', verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                repo.COMPUTE_UPGRADE = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def get_storage_upgrades(args, repo):
        get_token(repo)
        if not repo.PARENT_ID:  
            AssetMgmt.get_current_assets(repo)
        try:
            url = ('{}/inventory/1/installations/{}/compute/upgrades?refresh=false'.format(repo.URL,repo.PARENT_ID))
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data='{}', verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                repo.STORAGE_UPGRADE = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text)