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
    # =====================================================================
    # Get storage info for a single asset
    # =====================================================================
    def get_cluster_by_id(cluster_id, repo):
        try:
            get_token(repo) 
            url = ("{}/storage/1/{}/info".format(repo.URL,cluster_id))
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                cluster_info = json.loads(response.text)
            else:
                cluster_info = "Unable to fetch cluster data"
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
        return cluster_info

    # =====================================================================
    # Get the last upgrade log
    # =====================================================================
    def get_upgrade_log(repo):
        logmsg.info("\nChecking for previous upgrade log. Please wait...")
        try:
            get_token(repo) 
            url = ("{}/storage/1/upgrades?includeCompleted=true".format(repo.URL))
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                upgrade = json.loads(response.text)
                try:
                    if (upgrade[0]['upgradeId']):
                        repo.UPGRADE_ID = upgrade[0]['upgradeId']
                        repo.STORAGE_ELEMENT_UPGRADE_TARGET = upgrade[0]['storageId']
                        repo.STORAGE_UPGRADE_LOG = ("/var/log/ElementUpgrade-{}.log".format(repo.STORAGE_ELEMENT_UPGRADE_TARGET))
                except:
                    logmsg.info("No prior upgrade detected")

                try:
                    url = ("{}/storage/1/upgrades/{}/log".format(repo.URL,repo.UPGRADE_ID))
                    logmsg.debug("Sending GET {}".format(url))
                    response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    if response.status_code == 200:
                        try:
                            with open(repo.STORAGE_UPGRADE_LOG, 'w') as outfile:               
                                outfile.write(response.text)
                                logmsg.info("Previous upgrade log saved to {}".format(repo.STORAGE_UPGRADE_LOG))
                                outfile.close()
                        except FileNotFoundError:
                            logmsg.info("Could not open {}".format(outfile)) 
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
            else:
                logmsg.info("No previous upgrade found")
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)

    # =====================================================================
    # Get storage info for support bundle
    # =====================================================================
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
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        if response.status_code == 200 :
                            outfile.write(json.dumps(response.text))
                        else:
                            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                            logmsg.debug("{}: {}".format(response.status_code, response.text))
                        x += 1
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug("{}: {}".format(response.status_code, response.text)) 
            outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    def get_clusters(repo):
        get_token(repo)
        try:
            url = ('{}/storage/1/clusters?installationId={}'.format(repo.URL,repo.PARENT_ID))
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200 :
                repo.CLUSTERS = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def check_auth_container(repo):
        get_token(repo)
        url = ('{}/storage/1/clusters/check-auth-container'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200 :
                return(json.loads(response.text))
            elif response.status_code == 500:
                logmsg.info("API call not supported on target cluster. Don't panic. Expected with EOS 12.3 and higher")
                return str(response.status_code)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                return str(response.status_code)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text))  
    
    def check_auth_config(repo):
        # SUST-1292 element-auth requires clientid mnode-init. The mnode service id's require mnode-client
        # first force a new token with mnode-init. Later force a new token with mnode-client
        authconfig = []
        repo.TOKEN_CLIENT = "mnode-init"
        repo.NEW_TOKEN = True
        get_token(repo)
        url = ('https://{}/auth/api/1/configuration'.format(repo.INVENTORY_AUTHORATIVE_CLUSTER))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200 :
                authconfig = json.loads(response.text)
                logmsg.debug(authconfig)
                if len(authconfig["apiClients"]) == 0 and len(authconfig['apiResources'] == 0):
                    msg = ("\tThere is problem with the auth configuration\n\tSee Solution in KB\nhttps://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/setup-mnode_script_or_Management_Services_update_fails_on_Element_mNode_12.2_with_configure_element_auth_error")
                else:
                    msg = ("\tapiClient and apiResources looks good. See /var/log/mnode-support-util.log to verify")
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
            # SUST-1292
            repo.TOKEN_CLIENT = "mnode-client"
            get_token(repo)
            repo.NEW_TOKEN = False
            return msg
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def get_health_check(repo):
        get_token(repo)
        url = ('{}/storage/1/health-checks?includeCompleted=true'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False) 
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200 :
                repo.HEALTH_CHECK = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

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
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        if response.status_code == 200 :
                            outfile.write(json.dumps(response.text))
                        else:
                            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                            logmsg.debug("{}: {}".format(response.status_code, response.text))
                        x += 1
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug("{}: {}".format(response.status_code, response.text)) 
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
                logmsg.debug("{}: {}".format(response.status_code, response.text)) 