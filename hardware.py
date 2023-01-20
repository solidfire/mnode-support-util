import json
import requests
from get_token import get_token
from log_setup import Logging
from mnode import AssetMgmt
from package import list_packages

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

class Hardware():
    def get_hardware(args, repo):
        get_token(repo)
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)

        for hardware in repo.CURRENT_ASSET_JSON[0]['hardware']:
            hardware_id = hardware['id']
            url = ('{}/hardware/2/nodes/{}'.format(repo.URL,hardware_id))
            try:
                logmsg.debug("Sending GET {}".format(url))
                response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                logmsg.debug(response.text)
                if response.status_code == 200:
                    repo.HARDWARE.append(json.loads(response.text))
                else:
                    logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                    logmsg.debug(response.text)
                    exit(1)
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug(response.text) 

    def get_hardware_logs(args, repo):
        get_token(repo)
        filename = ("{}support-hardware-logs.json".format(repo.SUPPORT_DIR))
        if not repo.CURRENT_ASSET_JSON:
            AssetMgmt.get_current_assets(repo)

        try:
            with open(filename, 'a') as outfile:
                for hardware in repo.CURRENT_ASSET_JSON[0]['hardware']:
                    hardware_id = hardware['id']
                    url = ('{}/hardware/2/nodes/{}/bmc-logs'.format(repo.URL,hardware_id))
                    try:
                        logmsg.debug("Sending GET {}".format(url))
                        response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                        logmsg.debug(response.text)
                        if response.status_code == 200:
                            outfile.write(json.dumps(response.text))
                        else:
                            logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                            logmsg.debug(response.text)
                            exit(1)
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug(response.text) 
            outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    def select_hardware(repo):
        logmsg.info("Available compute hardware")
        if repo.CURRENT_ASSET_JSON[0]['hardware']:
            for BMC in repo.CURRENT_ASSET_JSON[0]['hardware']:
                for ESX in repo.CURRENT_ASSET_JSON[0]['compute']:
                    if ESX['hardware_tag'] == BMC['hardware_tag']:
                        logmsg.info("ESX hostname: {:<20}BMC IP: {:<20}BMC ID: {:<20}".format(ESX['host_name'],BMC['ip'],BMC['id']))
        else:
            logmsg.info("No compute BMC assets found. Please add BMC (hardware-node) assets \nhttps://docs.netapp.com/us-en/hci/docs/task_mnode_add_assets.html\nExiting...")
            exit(0)

        userinput = input("Enter the target BMC ID: ")
        repo.COMPUTE_UPGRADE = userinput

'''
SUST-1343
    def start_compute_firmware(repo):
        get_token(repo)
        forceoption = 'false'
        maintmode = 'true'
        url = ('{}/hardware/2/nodes/{}/upgrades'.format(repo.URL,repo.COMPUTE_UPGRADE))
        
        current_packages = list_packages(repo)
        logmsg.info('\nAvailable compute firmware packages;')
        if len(current_packages) > 0:
            for package in current_packages:
                if package['name'] == 'compute-firmware':
                    logmsg.info('name: {:<20} version: {:<20}'.format(package['name'],package['version']))
        else:
            logmsg.info("No compute-firmware packages found.\nPlease download from\nhttps://mysupport.netapp.com/site/products/all/details/netapp-hci/downloads-tab/download/62542/Compute_Firmware_Bundle")
        packagever = input("Enter the target package version: ")

        userinput = input("Use the Force option?(y/n): ")
        if userinput.lower == 'y': forceoption = 'true'

        userinput = input("Place the compute node in maintenance mode?(y/n): ")
        if userinput.lower == 'n': maintmode = 'false'
        
        #payload = {"config":{"force":forceoption,"maintenanceMode":maintmode},"controllerId":repo.CONTROLLER_ID,"packageName":"compute-firmware","packageVersion":packagever}
        payload = json.dumps({  "config": {"force": False,"maintenanceMode": True},"controllerId": repo.CONTROLLER_ID,"packageName": "compute-firmware","packageVersion": packagever})
        logmsg.info("Starting compute firmware update")
        try:
            get_token(repo)
            logmsg.debug("Sending POST {} {}".format(url,payload))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=payload, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 202:
                responsejson = json.loads(response.text)
                #if responsejson[0]['status'] == 'failed': logmsg.info('Failed. See log: {}'.format(responsejson[0]['upgradesDetails'][0]['_links']['logs']))
                if responsejson['resourceLink']: 
                  logmsg.info(responsejson)
                  

        except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug(response.text) 

        

'''
