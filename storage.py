import getpass
import json
import requests
from get_token import get_token
from log_setup import Logging

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

class Clusters():
    def get_storage_info(repo):
        get_token(repo)
        filename = ("{}support-storage-info.json".format(repo.SUPPORT_DIR))
        storage = len(repo.CURRENT_ASSET_JSON[0]['storage'])
        x = 0
        try:
            with open(filename, 'a') as outfile:
                while x < storage:
                    storage_id = repo.CURRENT_ASSET_JSON[0]['storage'][x]['id']
                    url = ('{}/storage/1/{}/info'.format(repo.URL,storage_id))
                    try:
                        logmsg.debug("Sending GET {}".format(url))
                        response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                        logmsg.debug(response.text)
                        if response.status_code == 200 :
                            outfile.write(json.dumps(response.text))
                        else:
                            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                            logmsg.debug(response.text)
                        x += 1
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug(response.text) 
            outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    def get_clusters(repo):
        get_token(repo)
        try:
            url = ('{}/storage/1/clusters?installationId={}'.format(repo.URL,repo.PARENT_ID))
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200 :
                repo.CLUSTERS = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    # remove - no longer functions in 12.3.1+    
    def check_auth_container(repo):
        get_token(repo)
        url = ('{}/storage/1/clusters/check-auth-container'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200 :
                repo.CHECK_AUTH = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 
    
    def check_auth_config(repo):
        # SUST-1292 element-auth requires clientid mnode-init. The mnode service id's require mnode-client
        # first force a new token with mnode-init. Later force a new token with mnode-client
        repo.TOKEN_CLIENT = "mnode-init"
        repo.NEW_TOKEN = True
        get_token(repo)
        url = ('https://{}/auth/api/1/configuration'.format(repo.INVENTORY_AUTHORATIVE_CLUSTER))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200 :
                repo.AUTH_CONFIG = json.loads(response.text)
                #for client in repo.AUTH_CONFIG["apiClients"]:
                #    logmsg.info("apiClient: {}".format(client["clientId"]))
                #for resource in repo.AUTH_CONFIG["apiResources"]:
                #    logmsg.info("apiResource: {}".format(resource["name"]))
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
            # SUST-1292
            repo.TOKEN_CLIENT = "mnode-client"
            get_token(repo)
            repo.NEW_TOKEN = False
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def get_health_check(repo):
        get_token(repo)
        url = ('{}/storage/1/health-checks?includeCompleted=true'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False) 
            logmsg.debug(response.text)
            if response.status_code == 200 :
                repo.HEALTH_CHECK = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def get_health_check_logs(repo):
        get_token(repo)
        filename = ("{}support-health-check-logs.json".format(repo.SUPPORT_DIR))
        x = 0
        try:
            with open(filename, 'a') as outfile:
                for check in repo.HEALTH_CHECK:
                    health_check_id = repo.HEALTH_CHECK[x]['healthCheckId']
                    url = ('{}/storage/1/health-checks/{}'.format(repo.URL,health_check_id))
                    try:
                        logmsg.debug("Sending GET {}".format(url))
                        response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                        logmsg.debug(response.text)
                        if response.status_code == 200 :
                            outfile.write(json.dumps(response.text))
                        else:
                            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                            logmsg.debug(response.text)
                        x += 1
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug(response.text) 
        except FileNotFoundError:
                logmsg.info("Could not open {}".format(filename))

    def check_cluster_creds(repo, mvip, host_name):
        # Ensure the creds specified with ('-su', '--stuser') ('-sp', '--stpw') work on the current cluster
        # Prompt for creds if the given creds fail
        url = "https://{}/json-rpc/10.0".format(mvip)
        payload = "{\n\t\"method\": \"GetClusterInfo\",\n    \"params\": {},\n    \"id\": 1\n}"
        try:
            response = requests.post(url, auth=(repo.STORAGE_USER, repo.STORAGE_PASSWD), data=payload, verify=False)
            stuser = repo.STORAGE_USER
            stpw = repo.STORAGE_PASSWD
            if response.status_code == 401:
                while response.status_code == 401:
                    logmsg.info("The provided credentials failed on cluster {}".format(host_name))
                    stuser = input("Enter admin userid for cluster {} : ".format(host_name))
                    stpw = getpass.getpass(prompt="Enter admin password: ")
                    response = requests.post(url, auth=(stuser, stpw), data=payload, verify=False)
            return response.status_code, stuser, stpw
        except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug(response.text) 