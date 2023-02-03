from gettext import translation
import json
import logging
import requests
from time import sleep
from get_token import get_token
from log_setup import Logging
from mnode import AssetMgmt
from package import list_packages
from storage import Clusters
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

logmsg = Logging.logmsg()

class ElemUpgrade():
    
    #============================================================
    # Choose upgrade option
    #============================================================
    def upgrade_option(repo):
        userinput = ""
        options = ['s','v','p','r','a','q']
        while userinput not in options:
            userinput = input("\nUpgrade options: Start, View, Pause, Resume, Abort, Quit: s/v/p/r/a/q: ")
        repo.UPGRADE_OPTION = userinput

    #============================================================
    # Select target cluster for upgrade
    #============================================================
    def discovery(repo):
        logmsg.debug("Enter Element upgrade discovery")
        if not repo.CURRENT_ASSET_JSON:
            try:
                AssetMgmt.get_current_assets(repo)
            except:
                logmsg.info("Could not get current assets")
                exit(1)
        clusterlist = {}
        userinput = ""
        targetcluster = ""
        logmsg.info("\nList of available clusters.")
        for cluster in repo.CURRENT_ASSET_JSON[0]["storage"]:
            cluster_data = Clusters.get_cluster_by_id(cluster["id"], repo)
            if(cluster["host_name"]):
                clusterlist[(cluster["host_name"])] = cluster["id"]
                logmsg.info("+ {:<15}{:<15}".format(cluster["host_name"], cluster_data['cluster']['GetClusterVersionInfo']['clusterVersion']))
                targetcluster = cluster["host_name"]
                repo.STORAGE_ELEMENT_UPGRADE_TARGET = clusterlist[(cluster["host_name"])]
            else:
                clusterlist[(cluster["ip"])] = cluster["id"]
                logmsg.info("+ {:<15}{:<15}".format(cluster["ip"], cluster_data['cluster']['GetClusterVersionInfo']['clusterVersion']))
                targetcluster = str(cluster["ip"])
                repo.STORAGE_ELEMENT_UPGRADE_TARGET = clusterlist[(cluster["ip"])]
        if len(clusterlist) > 1:
            while userinput not in clusterlist:
                userinput = input("\nEnter the target cluster from the list: ")
                targetcluster = userinput
                repo.STORAGE_ELEMENT_UPGRADE_TARGET = clusterlist[userinput]
        logmsg.info("Upgrade target cluster = {}".format(targetcluster))

    #============================================================
    # Select Element version
    #============================================================
    def select_version(repo):
        logmsg.info("\nAvailable upgrade packages")
        availablepackages = list_packages(repo)
        if availablepackages[0]['name']:
            for package in availablepackages:
                logmsg.info("+ {:<15}{:<15}".format(package['name'],package['version']))

        userinput = "none"
        targetpkg = ""
        pkglist = {}
        logmsg.info("\nLooking for a valid upgrade image...")
        get_token(repo)
        url = ("{}/storage/1/clusters/{}/valid-packages".format(repo.URL,repo.STORAGE_ELEMENT_UPGRADE_TARGET))
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                if response.text.find("solidfire"):
                    packages = json.loads(response.text)
                    if not packages:
                        logmsg.info("\nNo valid upgrade packages found.\n\tThe selected cluster is at or above available upgrade packages.\n\tUpload a package with the -a elementupload option")
                        exit(0)
                    for package in packages:
                        pkglist[(package["filename"])] = package["packageId"]
                        logmsg.info("+ {}".format(package["filename"]))
                        targetpkg = package["filename"]
                        repo.STORAGE_ELEMENT_UPGRADE_PACKAGE = pkglist[package["filename"]]
                if len(pkglist) > 1:
                    while userinput not in pkglist:
                        userinput = input("Enter the target package from the list: ")
                        repo.STORAGE_ELEMENT_UPGRADE_PACKAGE = pkglist[userinput]
                        targetpkg = userinput
                logmsg.info("Selected package {}".format(targetpkg))
            else:
                logmsg.info("Failed to retrieve package list. Check internet connectivity.")
                logmsg.debug(response.status_code)
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)

    #============================================================
    # Start Upgrade
    #============================================================
    def start_upgrade(repo):
        logmsg.info("\nStarting Element upgrade")
        get_token(repo)
        url = (repo.URL + "/storage/1/upgrades")
        userinput = ""
        while userinput != 'y' and userinput != 'n':
            userinput = input("Do you have any config options to add? (y/n) ")
        if userinput == 'y':
            logmsg.info("\nSee the following KB for config samples.")
            logmsg.info("https://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/Potential_issues_and_workarounds_when_running_storage_upgrades_using_NetApp_Hybrid_Cloud_Control")
            configinput = input("\nEnter exact json or press enter to be prompted: ")
            if configinput == "":
                configjson = ElemUpgrade.config_options()
            else:
                configjson = json.loads(configinput)
            payload = { "config": configjson, "packageId":repo.STORAGE_ELEMENT_UPGRADE_PACKAGE,"storageId":repo.STORAGE_ELEMENT_UPGRADE_TARGET }
        else:
            payload = { "config": {}, "packageId":repo.STORAGE_ELEMENT_UPGRADE_PACKAGE,"storageId":repo.STORAGE_ELEMENT_UPGRADE_TARGET }
        try:
            logmsg.debug("Sending POST {} {}".format(url,json.dumps(payload)))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug(response.text)
            if response.status_code == 202:
                logmsg.info("Received successful 202")
                upgrade_json = json.loads(response.text)
                repo.UPGRADE_ID = upgrade_json["upgradeId"]
                repo.UPGRADE_TASK_ID = upgrade_json["taskId"]
                logmsg.info("Upgrade ID: {}".format(repo.UPGRADE_ID))
                logmsg.info("Upgrade task ID: {}".format(repo.UPGRADE_TASK_ID))
                logmsg.info("Waiting 10 seconds to pass initializing state")
                repo.STORAGE_UPGRADE_LOG = ("/var/log/ElementUpgrade-{}.log".format(repo.STORAGE_ELEMENT_UPGRADE_TARGET))
                logmsg.info("Writing upgrade details to {}".format(repo.STORAGE_UPGRADE_LOG))
                try:
                    with open(repo.STORAGE_UPGRADE_LOG, 'a') as outfile:               
                        outfile.write(response.text)
                        outfile.close()
                except FileNotFoundError:
                    logmsg.info("Could not open {}".format(repo.STORAGE_UPGRADE_LOG))
                sleep(10)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)


    #============================================================
    # Find Upgrade
    #============================================================
    def find_upgrade(repo):
        logmsg.info("\nFind element upgrade")
        get_token(repo)
        url = ('{}/storage/1/upgrades?includeCompleted=false'.format(repo.URL))
        payload={}
        try:
            logmsg.debug("Sending {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data = payload, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                response_json = json.loads(response.text)
                if len(response_json) != 0:
                    repo.UPGRADE_ID = response_json[0]["upgradeId"]
                    logmsg.info("Found upgrade ID {}".format(repo.UPGRADE_ID))
                    if response_json[0]["status"]["availableActions"]:
                        logmsg.info('Available actions: {}'.format(response_json[0]["status"]["availableActions"]))
                        if 'abort' not in response_json[0]["status"]["availableActions"] and repo.UPGRADE_ACTION == 'abort':
                            logmsg.info('Upgrade cannot be aborted.')
                            exit(0)
                        if 'resume' not in response_json[0]["status"]["availableActions"] and repo.UPGRADE_ACTION == 'resume':
                            logmsg.info('Upgrade cannot be resumed.')
                            exit(0)
                        if 'pause' not in response_json[0]["status"]["availableActions"] and repo.UPGRADE_ACTION == 'pause':
                            logmsg.info('Upgrade cannot be paused.')
                            exit(0)
                else:
                    repo.UPGRADE_STATUS_MESSAGE = "No running upgrades detected"
                    logmsg.info(repo.UPGRADE_STATUS_MESSAGE)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
        
    #============================================================
    # Check Upgrade
    #=========================================================== =
    def check_upgrade(repo):
        url = ("{}/storage/1/upgrades/{}".format(repo.URL,repo.UPGRADE_ID))
        payload = {}
        percent_complete = 0
        repo.UPGRADE_STATUS_MESSAGE = "checkupgrade"

        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        try:
            while percent_complete != 100: 
                try:
                    get_token(repo)
                    response = requests.get(url, headers=repo.HEADER_READ, data = payload, verify=False)
                    if response.status_code == 200:
                        response_json = json.loads(response.text)
                        if not response_json["status"]["message"] and not response_json['state']:
                            logmsg.info("Unable to parse json return. See /var/log/mnode-support-util.log for details")
                            logmsg.debug(response.text)
                            exit(1)
                        if response_json['state'] == 'error':
                            logmsg.info(response_json['state'])
                            logmsg.info(response_json['status']['message'])
                            exit(1)
                        if repo.UPGRADE_STATUS_MESSAGE not in response_json["status"]["message"]:
                            try:
                                with open(repo.STORAGE_UPGRADE_LOG, 'a') as outfile:               
                                    outfile.write(response.text)
                                    outfile.close()
                            except FileNotFoundError:
                                logmsg.info("Could not open {}".format(repo.STORAGE_UPGRADE_LOG))        
                            repo.UPGRADE_STATUS_MESSAGE = response_json["status"]["message"]
                            logmsg.info("\nUpgrade status: {}".format(response_json["status"]["message"]))
                            if response_json["state"]: 
                                logmsg.info("Upgrade state: {}".format(response_json["state"]))
                            if response_json["status"]["percent"]: 
                                logmsg.info("Upgrade Percentage: {}".format(str(response_json["status"]["percent"])))
                                percent_complete = response_json["status"]["percent"]
                            if response_json["status"]["step"]: 
                                logmsg.info("Upgrade step: {}".format(response_json["status"]["step"]))
                            if response_json["status"]["availableActions"]:
                                for action in response_json["status"]["availableActions"]:
                                    logmsg.info("Available action: {}".format(action))
                            if response_json["status"]["nodeDetails"]:
                                for node in response_json["status"]["nodeDetails"]:
                                    logmsg.info(node)
                            if response_json["status"]["failedHealthChecks"]:
                                for check in response_json["status"]["failedHealthChecks"]:
                                    logmsg.info(check)
                    else:
                        logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                        logmsg.debug(response.text)
                        exit(1)
                except requests.exceptions.RequestException as exception:
                    logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(exception)
        except KeyboardInterrupt:
            logmsg.info("Received Ctrl-C")
    # Set logging back to debug
    logging.getLogger("urllib3").setLevel(logging.DEBUG)

    #============================================================
    # Pause , resume, abort Upgrade
    #============================================================
    def upgrade_action(repo):
        logmsg.info("{} upgrade {}".format(repo.UPGRADE_ACTION,repo.UPGRADE_ID))
        get_token(repo)
        url = ("{}/storage/1/upgrades/{}".format(repo.URL,repo.UPGRADE_ID))
        payload = { "config": {},"action":repo.UPGRADE_ACTION }
        if repo.UPGRADE_ACTION == 'resume':
            userinput = str.lower(input("Do you have any config options to add? (y/n) "))
            if userinput == 'y':
                logmsg.info("See the following KB's for config samples.")
                logmsg.info("https://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/Potential_issues_and_workarounds_when_running_storage_upgrades_using_NetApp_Hybrid_Cloud_Control")
                configinput = input("Enter exact json or press enter to be prompted: ")
                if configinput == "":
                    configjson = ElemUpgrade.config_options()
                else:
                    configjson = json.loads(configinput)
                payload = { "config": configjson, "action":repo.UPGRADE_ACTION }
            else:
                pass
        try:
            logmsg.debug("Sending: PUT {} {}".format(url,json.dumps(payload)))
            response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                response_json = json.loads(response.text)
                if len(response_json) != 0:
                    logmsg.info("Upgrade state: {}".format(response_json["state"]))
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)

    #============================================================
    # Config options
    #============================================================
    def config_options():
        option = "string"
        value = []
        configoptions = {}
        logmsg.info("Enter option names and values. Enter q when done")
        while option != "":
            userinput = input("Enter the option name: ")
            if userinput.lower() == 'q':
                break
            else:
                option = userinput
            value = input("Enter the option value: ")
            if ',' in value:
                configoptions[option] = value.split(',')
            else:
                configoptions[option] = value
        
        return(configoptions)