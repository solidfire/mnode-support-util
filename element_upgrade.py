from gettext import translation
import json
import logging
import time
from time import sleep
from get_token import GetToken
from log_setup import Logging
from program_data import PDApi, Common
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

"""
 Element upgrade
"""

# set up logging
logmsg = Logging.logmsg()

class ElemUpgrade():
    def __init__(self):
        upgrade_id = ""
        upgrade_target = ""

    def _config_options(self):
        """ Config options
        """
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
    
    def upgrade_option(self):
        """ Choose upgrade option
        """
        userinput = ""
        options = ['s','v','p','r','a','q']
        while userinput not in options:
            userinput = input("\nUpgrade options: Start, View, Pause, Resume, Abort, Quit: s/v/p/r/a/q: ")
        return userinput

    def select_target_cluster(self, repo):
        """ Select target cluster for upgrade
        """
        self.upgrade_target = Common.select_target_cluster(repo)

    def select_version(self, repo):
        """ Select Element version
        """
        userinput = "none"
        pkglist = {}
        logmsg.info("\nLooking for a valid upgrade image...")
        url = f'{repo.base_url}/storage/1/clusters/{self.upgrade_target}/valid-packages'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            for package in json_return:
                    pkglist[package["filename"]] = package["packageId"]
                    logmsg.info(f'\t{package["filename"]}')
            while userinput not in pkglist:
                userinput = input("\nEnter the target package from the list: ")
                upgrade_package = pkglist[userinput]
            logmsg.info(f'Selected package {upgrade_package}')
            return upgrade_package
        else:
            logmsg.info("\nNo valid upgrade packages found.\n\tThe selected cluster is at or above available upgrade packages.\n\tUpload a package with the -a elementupload option")
            exit(0)
                
    def start_upgrade(self, repo, upgrade_package):
        """ Start Upgrade
        """
        logmsg.info("\nStarting Element upgrade")
        url = (repo.base_url + "/storage/1/upgrades")
        userinput = ""
        while userinput != 'y' and userinput != 'n':
            userinput = input("Do you have any config options to add? (y/n) ")
        
        if userinput == 'y':
            configjson = self._config_options()
            payload = { "config": configjson, "packageId":upgrade_package,"storageId":self.upgrade_target }
        else:
            payload = { "config": {}, "packageId":upgrade_package,"storageId":self.upgrade_target }
        logmsg.debug(f'Sending POST {url} {json.dumps(payload)}')
        json_return = PDApi.send_post_return_json(repo, url, payload)
        
        if json_return is not None:
            logmsg.info(f'\nUpgrade ID: {json_return["upgradeId"]}')
            logmsg.info(f'Upgrade task ID: {json_return["taskId"]}')
            self.upgrade_id = json_return["upgradeId"]

    def find_upgrade(self, repo):
        """ Find Upgrade
        """
        logmsg.info("Find active element upgrade(s)")
        url = f'{repo.base_url}/storage/1/upgrades?includeCompleted=false'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if len(json_return) == 1:
            logmsg.info(f'Running upgrade\nUpgrade ID {json_return[0]["upgradeId"]}\n\tState: {json_return[0]["state"]}\n\tStarted: {json_return[0]["dateCreated"]}\n\tStatus: {json_return[0]["status"]["message"]}\n\tAvailable actions: {json_return[0]["status"]["availableActions"]}\n')
            self.upgrade_id = json_return[0]["upgradeId"]
        elif len(json_return) > 1:
            logmsg.info('Running upgrades\n')
            for upgrade in json_return:
                logmsg.info(f'Upgrade ID: {upgrade["upgradeId"]}\n\tState: {upgrade["state"]}\n\tStarted: {upgrade["dateCreated"]}\n\tStatus: {upgrade["status"]["message"]}\n\tAvailable actions: {upgrade["status"]["availableActions"]}\n')
            userinput = input("Enter the upgrade ID to work with or press Enter for new upgrade: ")
            self.upgrade_id = userinput
        else:
            logmsg.info("No running upgrades detected")

    def check_upgrade(self, repo):
        """ Check Upgrade log
        """
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        percent_complete = 0
        status_message = "checkupgrade"
        url = f'{repo.base_url}/storage/1/upgrades/{self.upgrade_id}'
        logmsg.info("\nWatch upgrade progress. CTRL-C to exit.")
        try:
            while percent_complete != 100:
                GetToken(repo)
                json_return = PDApi.send_get_return_json(repo, url, 'no')
                if json_return is not None:
                    if json_return["state"] == 'initializing':
                        logmsg.info("Upgrade is initializing. Waiting 15 seconds to start")
                        time.sleep(15)
                    elif json_return["state"] == 'error':
                        logmsg.info(f'\n{json_return["state"]}: {json_return["status"]["message"]}\nSee /var/log/mnode-support-util.log for details')
                        logmsg.debug(json_return)
                        if json_return["status"]["failedHealthChecks"]:
                            for fail in json_return["status"]["failedHealthChecks"]:
                                logmsg.info(f'\tPassed: {fail["passed"]}\t{fail["description"]}')
                        exit(1)
                    elif status_message not in json_return["status"]["message"]:   
                        status_message = json_return["status"]["message"]
                        logmsg.info(f'\nUpgrade status: {json_return["status"]["message"]}\nUpgrade Percentage: {str(json_return["status"]["percent"])}\nUpgrade step: {json_return["status"]["step"]}')
                        percent_complete = json_return["status"]["percent"]
                        if json_return["status"]["availableActions"]:
                            for action in json_return["status"]["availableActions"]:
                                logmsg.info(f'Available action: {action}')
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

    def upgrade_action(self, repo, action):
        """ Pause , resume, abort Upgrade
        """
        logmsg.info(f'{action} upgrade {self.upgrade_id}')
        url = f'{repo.base_url}/storage/1/upgrades/{self.upgrade_id}'
        payload = { "config": {},"action":action }
        if action == 'resume':
            userinput = str.lower(input("Do you have any config options to add? (y/n) "))
            if userinput == 'y':
                configjson = self._config_options()
                payload = { "config": configjson, "action":action }
            else:
                pass
        logmsg.debug(f'Sending: PUT {url} {json.dumps(payload)}')
        json_return = PDApi.send_put_return_json(repo, url, payload)
        
        if 'state' in json_return:
            logmsg.info(f'Upgrade state: {json_return["state"]}')
        elif 'detail' in json_return:
            logmsg.info(json_return['detail'])
        else:
            logmsg.info("Unknown return: See /var/log/mnode-support-util.log for details")
            logmsg.debug(json.dumps(json_return))
            exit(1)
