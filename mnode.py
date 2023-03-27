import getpass
import json
import os.path
import requests
import urllib3
from datetime import datetime
from get_token import get_token
from log_setup import Logging
from storage import Clusters

logmsg = Logging.logmsg()

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

def get_logs(repo):
    get_token(repo)
    url = ('{}/mnode/services?status=running&helper=false'.format(repo.URL))
    service_list = []
    try:
        logmsg.debug("Sending GET {}".format(url))
        response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
        if response.status_code == 200:
            service_list = json.loads(response.text)
            for service in service_list:
                url = ('{}/mnode/logs?lines=1000&service-name={}&stopped=true'.format(repo.URL,service))
                try:
                    logmsg.info("Retrieving {} logs".format(service))
                    response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                    if response.status_code == 200:
                        logmsg.debug("{} logs = {}".format(service, response.status_code))
                    else:
                        logmsg.debug("{} logs = {}".format(service, response.status_code))
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
                    logmsg.debug("{}: {}".format(response.status_code, response.text)) 
        else:
            logmsg.debug("Failed to retrieve service list")
            logmsg.debug(response.status_code)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
    except requests.exceptions.RequestException as exception:
        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
        logmsg.debug(exception)
        logmsg.debug("{}: {}".format(response.status_code, response.text)) 
        

class AssetMgmt():
    #============================================================
    # Get parent id
    #============================================================
    def get_parent_id(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets'.format(repo.URL))
        try:
            if not repo.CURRENT_ASSET_JSON:
                try:
                    logmsg.debug("Sending GET {}".format(url))
                    response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    if response.status_code == 200:
                        repo.CURRENT_ASSET_JSON = json.loads(response.text)
                    else:
                        logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        exit(1)
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
                    logmsg.debug("{}: {}".format(response.status_code, response.text)) 
            repo.PARENT_ID = (repo.CURRENT_ASSET_JSON[0]['id'])
        except:
            logmsg.debug("{}: {}".format(response.status_code, response.text))

    #============================================================
    # Set asset type for removal or update tasks
    #============================================================
    def set_asset_type(args, repo):
        logmsg.info("What type of asset to work on?\nc = compute\ns = storage\nb = BMC\nv = vCenter\na = all")
        asset_type = str.lower(input("> "))
        if asset_type == 'c': 
            repo.ASSET_TYPE = ['compute']
            repo.ASSET_URL_TYPE = 'compute-nodes'
            repo.USERID = args.computeuser
        elif asset_type == 's': 
            repo.ASSET_TYPE = ['storage']
            repo.ASSET_URL_TYPE = 'storage-clusters'
            repo.USERID = args.stuser
        elif asset_type == 'b': 
            repo.ASSET_TYPE = ['hardware']
            repo.ASSET_URL_TYPE = 'hardware-nodes'
            repo.USERID = args.bmcuser
        elif asset_type == 'v': 
            repo.ASSET_TYPE = ['controller']
            repo.ASSET_URL_TYPE = 'controllers'
            repo.USERID = args.vcuser
        elif asset_type == 'a':
            return 'all'

    #============================================================
    # Get current assets
    #============================================================
    def get_current_assets(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                repo.CURRENT_ASSET_JSON = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured attempting to gather assets. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def list_assets(repo): 
        get_token(repo)
        for asset_type in repo.ASSET_TYPE:
            logmsg.info("\nAvailable {} assets".format(asset_type))
            if len(repo.CURRENT_ASSET_JSON[0][asset_type]) == 0:
                logmsg.info("No {} assets found in inventory".format(asset_type))
                return_code = 1
            else:
                for asset in repo.CURRENT_ASSET_JSON[0][asset_type]:
                    if asset['host_name']:
                        logmsg.info("{:<15} assetID: {:<20} parentID: {:<}".format(asset['host_name'],asset['id'],asset['parent']))
                    else:
                        logmsg.info("{:<15} assetID: {:<20} parentID: {:<}".format(asset['ip'],asset['id'],asset['parent']))
                return_code = 0
        return return_code


    #============================================================
    # Backup assets
    #============================================================
    def backup_assets(repo):
        date_time = datetime.now()
        repo.TIME_STAMP = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        backup_file = ("{}-{}.json".format(repo.BACKUP_PREFIX,repo.TIME_STAMP))
        try:
            with open(backup_file, 'w') as outfile:
                if not repo.CURRENT_ASSET_JSON:
                    logmsg.info("Current assets not available. Not able to perform backup")
                else:
                    logmsg.info("Backing up current assets to {}".format(backup_file))
                    json.dump(repo.CURRENT_ASSET_JSON, outfile)
        except OSError as error :
            logmsg.info("Failed to open backup file. See /var/log/mnode-support-util.log for details")
            logmsg.debug(error)

    #============================================================
    # Remove the current assets
    #============================================================
    def remove_assets_by_type(repo):
        get_token(repo)
        input("Press Enter to continue removing {} assets".format(repo.ASSET_TYPE[0]))
        for asset in repo.CURRENT_ASSET_JSON[0][repo.ASSET_TYPE[0]]:
                asset_id = asset['id']
                url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.URL,repo.PARENT_ID,repo.ASSET_URL_TYPE,asset_id))
                logmsg.info("Removing asset id: {}".format(asset_id))
                try:
                    logmsg.debug("Sending DELETE {}".format(url))
                    response = requests.delete(url, headers=repo.HEADER_READ, data={}, verify=False)
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    if response.status_code == 204: 
                        logmsg.info("Successfully deleted asset")
                    else:
                        logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        exit(1)
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
                    logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def remove_all_assets(repo):
        get_token(repo)
        count = 0
        for asset_type in repo.ASSET_TYPE:
                input("Press Enter to continue removing {} assets".format(asset_type))
                for asset in repo.CURRENT_ASSET_JSON[0][asset_type]:
                    asset_id = asset['id']
                    url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.URL,repo.PARENT_ID,repo.ASSET_URL_TYPE[count],asset_id))
                    logmsg.info("Removing asset id: {}".format(asset_id))
                    try:
                        logmsg.debug("Sending DELETE {}".format(url))
                        response = requests.delete(url, headers=repo.HEADER_READ, data={}, verify=False)
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        if response.status_code == 204: 
                            logmsg.info("Successfully deleted asset")
                        else:
                            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                            logmsg.debug("{}: {}".format(response.status_code, response.text))
                            exit(1)
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug("{}: {}".format(response.status_code, response.text)) 
                count += 1

    def remove_one_asset(repo):
        asset_id = input("Provide the asset id: ")
        get_token(repo)
        url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.URL,repo.PARENT_ID,repo.ASSET_URL_TYPE,asset_id))
        logmsg.info("Removing asset id: {}".format(asset_id))
        try:
            logmsg.debug("Sending DELETE {}".format(url))
            response = requests.delete(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 204: 
                logmsg.info("Successfully deleted asset")
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    #============================================================
    # Add the assets
    #============================================================
    def add_assets(args, repo):
        count = 0
        payload_hardware_tag = ""
        payload_host_name = ""
        payload_ip = ""
        payload_username = ""
        payload_password = ""
        payload_type = ""
        for asset in repo.ASSET_TYPE:
            url = ('{}/mnode/1/assets/{}/{}'.format(repo.URL,repo.PARENT_ID,repo.ASSET_URL_TYPE[count]))
            for addasset in repo.JSON_DATA[0][asset]:
                logmsg.info("Adding {}".format(asset))
                payload_host_name = addasset['host_name']
                payload_ip = addasset['ip']

                if asset == 'compute':
                    if args.computeuser and not args.computepw:
                        try:
                            args.computepw = getpass.getpass(prompt="compute {} password: ".format(args.computeuser))
                        except Exception as error:
                            logmsg.info('ERROR', error)    
                    if not args.computeuser and not args.computepw:
                        logmsg.info("No compute user/passwd specified. Skipping compute assets")
                        break
                    payload_username = args.computeuser
                    payload_password = args.computepw
                    payload_hardware_tag = addasset['hardware_tag']
                    payload_type = addasset['type']
                    payload = {"config":{}, "hardware_tag": payload_hardware_tag, "host_name": payload_host_name, "ip": payload_ip, "username": payload_username, "password": payload_password, "type": payload_type}

                elif asset == 'hardware':
                    if args.bmcuser and not args.bmcpw:
                        try:
                            args.bmcpw = getpass.getpass(prompt="BMC {} password: ".format(args.bmcuser))
                        except Exception as error:
                            logmsg.info('ERROR: {}'.format(error))
                    if not args.bmcuser and not args.bmcpw:
                        logmsg.info("No hardware user/passwd specified. Skipping hardware assets")
                        break
                    payload_username = args.bmcuser
                    payload_password = args.bmcpw
                    payload_hardware_tag = addasset['hardware_tag']
                    payload_type = addasset['type']
                    payload = {"config":{}, "hardware_tag": payload_hardware_tag, "host_name": payload_host_name, "ip": payload_ip, "username": payload_username, "password": payload_password, "type": payload_type}
                
                elif asset == 'controller':
                    if args.vcuser and not args.vcpw:
                        try:
                            args.vcpw = getpass.getpass(prompt="vCenter {} password: ".format(args.vcuser))
                        except Exception as error:
                            logmsg.info('ERROR', error)    
                    if not args.vcuser and not args.vcpw:
                        logmsg.info("No controller user/passwd specified. Skipping controller assets")
                        break
                    payload_username = args.vcuser
                    payload_password = args.vcpw
                    payload_type = addasset['type']
                    payload = {"config":{}, "host_name": payload_host_name, "ip": payload_ip, "username": payload_username, "password": payload_password, "type": payload_type}

                elif asset == 'storage':
                    creds = Clusters.check_cluster_creds(repo, addasset['ip'], addasset['host_name'])
                    if creds == 200:
                        payload_username = args.stuser
                        payload_password = args.stpw
                    else:
                        payload_username = creds[1]
                        payload_password = creds[2]
                    payload = {"config":{}, "host_name": payload_host_name, "ip": payload_ip, "username": payload_username, "password": payload_password}

                get_token(repo)
                try:
                    logmsg.debug("Sending POST {}".format(url)) # cannot send password to the log. Figure something else out ,json.dumps(payload)))
                    response = requests.post(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    if response.status_code == 201:
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        logmsg.info("Added {}".format(payload_host_name))
                    if(response.status_code == 409): 
                        logmsg.info("{} Asset already exists in inventory. Skipping.".format(payload['host_name'])) 
                    if(response.status_code != 201 and response.status_code != 409):
                        logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        exit(1)
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
                    logmsg.debug("{}: {}".format(response.status_code, response.text)) 
            count += 1
    
    def update_passwd_by_type(repo):
        newpassword = ""
        newpassword_verify = "passwd"

        while newpassword != newpassword_verify:
            newpassword = getpass.getpass(prompt="Enter new password: ")
            newpassword_verify = getpass.getpass(prompt="Enter new password to verify: ")
            if newpassword != newpassword_verify:
                logmsg.info("Passwords do not match")
        
        get_token(repo)
        x = 0
        input("Press Enter to continue updating {} assets".format(repo.ASSET_TYPE[0]))
        while x < len(repo.CURRENT_ASSET_JSON[0][repo.ASSET_TYPE[0]]):
                asset_id = repo.CURRENT_ASSET_JSON[0][repo.ASSET_TYPE[0]][x]['id']
                payload = {"config":{}, "password": newpassword}
                url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.URL,repo.PARENT_ID,repo.ASSET_URL_TYPE,asset_id))
                logmsg.info("Updating asset id: {}".format(asset_id))
                try:
                    logmsg.debug("Sending PUT {}  password: new password".format(url))
                    response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    if response.status_code == 200: 
                        logmsg.info("Successfully updated asset")
                    else:
                        logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                        logmsg.debug("{}: {}".format(response.status_code, response.text))
                        exit(1)
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
                    logmsg.debug("{}: {}".format(response.status_code, response.text))        
                x += 1
                
    def update_passwd(repo):
        newpassword = ""
        newpassword_verify = "passwd"

        asset_id = input("Provide the asset id: ")
        
        while newpassword != newpassword_verify:
            newpassword = getpass.getpass(prompt="Enter new password: ")
            newpassword_verify = getpass.getpass(prompt="Enter new password to verify: ")
            if newpassword != newpassword_verify:
                logmsg.info("Passwords do not match")

        get_token(repo)
        payload = {"config":{}, "password": newpassword}
        url = ('{}/mnode/1/assets/{}/{}/{}'.format(repo.URL,repo.PARENT_ID,repo.ASSET_URL_TYPE,asset_id))
        logmsg.info("Updating asset id: {}".format(asset_id))
        try:
            logmsg.debug("Sending PUT {} config:, password: new password".format(url))
            response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200: 
                logmsg.info("Successfully updated asset")
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def addConfig(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets/{}/'.format(repo.URL,repo.PARENT_ID))
        payload =  {"config":{"collector":{"noVerifyCert":"true","remoteHost":"monitoring.solidfire.com"}}}
        ## for internal use
        #payload =  {"config":{"collector":{"noVerifyCert":"true","remoteHost":"monitoring.staging.activeiq.io"}}}
        try:
            logmsg.debug("Sending PUT {} {}".format(url,json.dumps(payload)))
            response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                logmsg.info("Applying config \n {}".format(response.request.body))
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug("{}: {}".format(response.status_code, response.text)) 
    
class Services():
    def get_services(repo):
        get_token(repo)
        url = ('{}/mnode/services?status=all&helper=true'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False) 
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200 :
                services = json.loads(response.text)
                return services
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def update_status(repo):
        get_token(repo)
        service_status = ""
        url = ('{}/mnode/services/update/status'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                service_status = json.loads(response.text)
                logmsg.debug(service_status)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def get_service_log(repo, service):
        log = []
        get_token(repo)
        url = ('{}/mnode/logs?lines=1000&service-name={}&stopped=true'.format(repo.URL, service))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False) 
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200 :
                log = response.text.splitlines()
                return log
            else:
                log = "Failed to retrieve log"
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

class Settings():
    def get_settings(repo):
        get_token(repo)
        url = ('{}/mnode/settings'.format(repo.URL))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                repo.SETTINGS = json.loads(response.text)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def add_settings(repo):
        get_token(repo)
        url = ('{}/mnode/2/settings'.format(repo.URL))
        json_file = "{}support-mnode-settings.json".format(repo.SUPPORT_DIR)
        if os.path.isfile(json_file):
            try:
                json_input = open(json_file, "r")
                json_data = json.load(json_input)
                json_input.close()
                payload = {"mnode_fqdn": json_data['mnode_fqdn'],  "proxy_ssh_port": json_data['proxy_port'], "proxy_username": json_data['proxy_username'],"proxy_port": json_data['proxy_port'],"use_proxy": json_data['use_proxy'],"proxy_ip_or_hostname": json_data['proxy_ip_or_hostname']}
                logmsg.debug("Sending PUT {} {}".format(url,json.dumps(payload)))
                response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                if response.status_code == 200:
                    logmsg.info("Applying settings\n {}".format(response.text))
                else:
                    logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    exit(1)
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug("{}: {}".format(response.status_code, response.text)) 

def about(repo):
    url = ('{}/mnode/1/about'.format(repo.URL))
    header = { 'accept': 'application/json' }
    try:
        logmsg.debug("Sending GET {}".format(url))
        response = requests.get(url, headers=header, data={}, verify=False)
        logmsg.debug("{}: {}".format(response.status_code, response.text))
        if response.status_code == 200:
            repo.ABOUT = json.loads(response.text)
            authmvip = repo.ABOUT["token_url"].split('/')
            repo.INVENTORY_AUTHORATIVE_CLUSTER = authmvip[2]
            repo.MNODEIP = repo.ABOUT["mnode_host_ip"]
            logmsg.debug("+ mNode ip/name: {}".format(repo.MNODEIP))
            logmsg.info("+ MS version: {}".format(repo.ABOUT["mnode_bundle_version"]))
            logmsg.info("+ mnode-support-util version: {}".format(repo.UTIL_VERSION))
            logmsg.info("+ Authorative cluster: {}".format(repo.INVENTORY_AUTHORATIVE_CLUSTER))
        else:
            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            exit(1)
    except requests.exceptions.RequestException as exception:
        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
        logmsg.debug(exception)
        logmsg.debug("{}: {}".format(response.status_code, response.text))