import getpass
import json
import os.path
import requests
import urllib3
from get_token import get_token
from log_setup import Logging, MLog

#============================================================
# set up logging
logmsg = Logging.logmsg()

#============================================================
# disable warnings so the log doesn't fill up
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# mnode end point tasks
#============================================================

def about(repo):
    #============================================================
    # Get assets /mnode/#/about/routes.v1.about.get
    # Populate the instance ABOUT
    url = ('{}/mnode/1/about'.format(repo.BASE_URL))
    header = { 'accept': 'application/json' }
    try:
        logmsg.debug("Sending GET about {}".format(url))
        response = requests.get(url, headers=header, data={}, verify=False)
        if response.status_code == 200:
            logmsg.debug(response.text)
            about = json.loads(response.text)
            return about
        else:
            MLog.log_failed_return(response.status_code, response.text)
    except requests.exceptions.RequestException as exception:
        MLog.log_exception(exception)



class Assets():
    #============================================================
    # Get assets mnode/#/assets/routes.v1.assets_api.get_assets
    # Populate the instance CURRENT_ASSET_JSON
    def get_assets(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets'.format(repo.BASE_URL))
        try:
            logmsg.debug("Sending GET assets {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if response.status_code == 200:
                logmsg.debug(response.text)
                repo.ASSETS = json.loads(response.text)
            else:
                MLog.log_failed_return(response.status_code, response.text)
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # get compute /mnode/#/assets/routes.v1.assets_api.get_compute_nodes
    # return response body
    def get_compute(repo):
        get_token(repo)
        url = ('{}/mnode/1/mnode/assets/compute-nodes'.format(repo.BASE_URL))
        try:
            logmsg.debug("Sending GET compute {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if response.status_code == 200:
                logmsg.debug(response.text)
                response_body = json.loads(response.text)
                return response_body
            else:
                MLog.log_failed_return(response.status_code, response.text)
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

class Services():
    #============================================================
    # Get services status = all, helper = yes /mnode/#/services/routes.v1.services_api.get_services
    # return response body
    def get_services(repo):
        get_token(repo)
        url = ('{}/mnode/services?status=all&helper=true'.format(repo.BASE_URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False) 
            if response.status_code == 200 :
                logmsg.debug(response.text)
                services = json.loads(response.text)
                return services
            else:
                MLog.log_failed_return(response.status_code, response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

class Settings():
    def get_settings(repo):
        get_token(repo)
        url = ('{}/mnode/settings'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                logmsg.debug(response.text)
                settings = json.loads(response.text)
                return settings
            else:
                MLog.log_failed_return(response.status_code, response.text)
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)
