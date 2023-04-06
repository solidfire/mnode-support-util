from gettext import translation
import json
import logging
import time
import requests
from time import sleep
from api_storage import Clusters
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

# =====================================================================
# Element upgrade
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

class ElemUpgrade():
    upgrade_id = ""
    upgrade_target = ""
    #============================================================
    # Choose upgrade option
    #============================================================
    def upgrade_option():
        userinput = ""
        options = ['s','v','p','r','a','q']
        while userinput not in options:
            userinput = input("\nUpgrade options: Start, View, Pause, Resume, Abort, Quit: s/v/p/r/a/q: ")
        return userinput

    #============================================================
    # Select target cluster for upgrade
    #============================================================
    def select_target_cluster(repo):
        clusterlist = {}
        userinput = ""
        logmsg.info("\nList of available clusters.")
        for cluster in repo.ASSETS[0]["storage"]:
            if(cluster["host_name"]):
                clusterlist[(cluster["host_name"])] = cluster["id"]
                logmsg.info("\t{}".format(cluster["host_name"]))
            else:
                clusterlist[(cluster["ip"])] = cluster["id"]
                logmsg.info("\t{}".format(cluster["ip"]))
        while userinput not in clusterlist:
            userinput = input("\nEnter the target cluster from the list: ")
            ElemUpgrade.upgrade_target = clusterlist[userinput]

    #============================================================
    # Select Element version
    #============================================================
    def select_version(repo):
        userinput = "none"
        pkglist = {}
        logmsg.info("\nLooking for a valid upgrade image...")
        get_token(repo)
        url = ("{}/storage/1/clusters/{}/valid-packages".format(repo.BASE_URL,ElemUpgrade.upgrade_target))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            for package in json_return:
                    pkglist[(package["filename"])] = package["packageId"]
                    logmsg.info("\t{}".format(package["filename"]))
                    targetpkg = package["filename"]
            while userinput not in pkglist:
                userinput = input("\nEnter the target package from the list: ")
                upgrade_package = pkglist[userinput]
            logmsg.info("Selected package {}".format(upgrade_package))
            return upgrade_package
        else:
            logmsg.info("\nNo valid upgrade packages found.\n\tThe selected cluster is at or above available upgrade packages.\n\tUpload a package with the -a elementupload option")
            exit(0)
                

    #============================================================
    # Start Upgrade
    #============================================================
    def start_upgrade(repo, upgrade_package):
        logmsg.info("\nStarting Element upgrade")
        get_token(repo)
        url = (repo.BASE_URL + "/storage/1/upgrades")
        userinput = ""
        while userinput != 'y' and userinput != 'n':
            userinput = input("Do you have any config options to add? (y/n) ")
        if userinput == 'y':
            configjson = ElemUpgrade.config_options()
            payload = { "config": configjson, "packageId":upgrade_package,"storageId":ElemUpgrade.upgrade_target }
        else:
            payload = { "config": {}, "packageId":upgrade_package,"storageId":ElemUpgrade.upgrade_target }
        logmsg.debug("Sending POST {} {}".format(url,json.dumps(payload)))
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return:
            logmsg.info("\nUpgrade ID: {}".format(json_return["upgradeId"]))
            logmsg.info("Upgrade task ID: {}".format(json_return["taskId"]))
            ElemUpgrade.upgrade_id = json_return["upgradeId"]

    #============================================================
    # Find Upgrade
    #============================================================
    def find_upgrade(repo):
        logmsg.info("\nFind element upgrade")
        get_token(repo)
        url = ('{}/storage/1/upgrades?includeCompleted=false'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            logmsg.info("Found upgrade ID {}".format(json_return[0]["upgradeId"]))
            ElemUpgrade.upgrade_id = json_return[0]["upgradeId"]
            if json_return[0]["status"]["availableActions"]:
                logmsg.info('Available actions: {}'.format(json_return[0]["status"]["availableActions"]))
        else:
            logmsg.info("No running upgrades detected")
        
    #============================================================
    # Check Upgrade
    #=========================================================== =
    def check_upgrade(repo):
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        percent_complete = 0
        status_message = "checkupgrade"
        url = ("{}/storage/1/upgrades/{}".format(repo.BASE_URL,ElemUpgrade.upgrade_id))
        logmsg.info("\nWatch upgrade progress. CTRL-C to exit.")
        try:
            while percent_complete != 100:
                json_return = PDApi.send_get_return_json(repo, url, 'no')
                if json_return:
                    if json_return['state'] == 'initializing':
                        logmsg.info("Upgrade is initializing. Waiting 15 seconds to start")
                        time.sleep(15)
                    elif json_return['state'] == 'error':
                        logmsg.info("\n{}: {}\nSee /var/log/mnode-support-util.log for details".format(json_return['state'],json_return['status']['message']))
                        logmsg.debug(json_return)
                        if json_return['status']['failedHealthChecks']:
                            for fail in json_return['status']['failedHealthChecks']:
                                logmsg.info("\tPassed: {}\t{}".format(fail['passed'], fail['description']))
                        exit(1)
                    elif status_message not in json_return["status"]["message"]:   
                        status_message = json_return["status"]["message"]
                        logmsg.info("\nUpgrade status: {}\nUpgrade Percentage: {}\nUpgrade step: {}".format(json_return["status"]["message"], str(json_return["status"]["percent"]), json_return["status"]["step"]))
                        percent_complete = json_return["status"]["percent"]
                        if json_return["status"]["availableActions"]:
                            for action in json_return["status"]["availableActions"]:
                                logmsg.info("Available action: {}".format(action))
                        if json_return["status"]["nodeDetails"]:
                            for node in json_return["status"]["nodeDetails"]:
                                logmsg.info(node)
                        if json_return["status"]["failedHealthChecks"]:
                            for check in json_return["status"]["failedHealthChecks"]:
                                logmsg.info(check)
        except KeyboardInterrupt:
            logmsg.info("Received Ctrl-C")
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    #============================================================
    # Pause , resume, abort Upgrade
    #============================================================
    def upgrade_action(repo, action):
        logmsg.info("{} upgrade {}".format(action,ElemUpgrade.upgrade_id))
        get_token(repo)
        url = ("{}/storage/1/upgrades/{}".format(repo.BASE_URL,ElemUpgrade.upgrade_id))
        payload = { "config": {},"action":action }
        if action == 'resume':
            userinput = str.lower(input("Do you have any config options to add? (y/n) "))
            if userinput == 'y':
                configjson = ElemUpgrade.config_options()
                payload = { "config": configjson, "action":action }
            else:
                pass
        logmsg.debug("Sending: PUT {} {}".format(url,json.dumps(payload)))
        json_return = PDApi.send_put_return_json(repo, url, payload)
        if json_return:
            logmsg.info("Upgrade state: {}".format(json_return["state"]))
        

    #============================================================
    # Config options
    #============================================================
    def config_options():
        option = "string"
        value = []
        configoptions = {}
        logmsg.info("\nSee the following KB for config samples.")
        logmsg.info("https://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/Potential_issues_and_workarounds_when_running_storage_upgrades_using_NetApp_Hybrid_Cloud_Control")
        configinput = input("\nEnter exact json or press enter to be prompted: ")
        if configinput == "":
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
            configjson = configoptions
        else:
            configjson = json.loads(configinput)
        return configjson