import json
import requests
import time
from get_token import get_token
from log_setup import Logging

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

logmsg = Logging.logmsg()

# Generate a list of clusters
# 
class StorageHealthcheck():

    def generate_cluster_list(repo):
        logmsg.debug("ENTER: generate_cluster_list")
        logmsg.info("\nAvailable clusters:")
        clusterlist = {}
        for cluster in repo.CURRENT_ASSET_JSON[0]["storage"]:
            if cluster["host_name"]:
                logmsg.info("+ {}".format(cluster["host_name"]))
                clusterlist[(cluster["host_name"])] = cluster["id"]
            else:
                logmsg.info("+ {}".format(cluster["ip"]))
                clusterlist[(cluster["ip"])] = cluster["id"]
        userinput = input("Enter the target cluster name: ")
        repo.STORAGE_ID = clusterlist[userinput]

    def run_storage_healthcheck(repo):
        get_token(repo)
        url = ('{}/storage/1/health-checks'.format(repo.URL))
        payload = {"config":{},"storageId":repo.STORAGE_ID}
        try:
            logmsg.debug("Sending POST {} {}".format(url,json.dumps(payload)))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 202:
                repo.STORAGE_HEALTHCHECK_TASK = json.loads(response.text)
                logmsg.info("Healthcheck running...")
                logmsg.debug(json.dumps(response.text))
            elif response.status_code == 400:
                logmsg.info("Healthcheck already running for this target. See /var/log/mnode-support-util.log for details")
                logmsg.info(response.status_code)
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
            else:
                logmsg.info("Failed to start healthcheck. See /var/log/mnode-support-util.log for details")
                logmsg.info(response.status_code)
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 

    def print_healthcheck_status(repo):
        healthcheck_report = []
        status_message = "nothing"
        report_file_name = ('{}healthcheck-{}.json'.format(repo.SUPPORT_DIR,repo.STORAGE_ID))
        with open(report_file_name, 'w') as report_file:
            url = ('{}/storage/1/health-checks/{}'.format(repo.URL,repo.STORAGE_HEALTHCHECK_TASK['healthCheckId']))
            payload = {}
            try:
                get_token(repo)
                logmsg.debug("Sending GET {}".format(url))
                response = requests.get(url, headers=repo.HEADER_READ, data=payload, verify=False)
                logmsg.debug("{}: {}".format(response.status_code, response.text))
                if response.status_code == 200:
                    healthcheck_report = (json.loads(response.text))
                    while healthcheck_report['state'] != 'finished':
                        time.sleep(10)
                        if healthcheck_report['state'] == 'failed': # ADD error
                            break
                        get_token(repo)
                        try:
                            logmsg.debug("Sending GET {}".format(url))
                            response = requests.get(url, headers=repo.HEADER_READ, data=payload, verify=False)
                            if response.status_code == 200:
                                healthcheck_report = (json.loads(response.text))
                                if 'Internal Error' in healthcheck_report['status']['message']:
                                    logmsg.info(healthcheck_report['status']['message'])
                                    logmsg.debug(healthcheck_report)
                                    exit(0)
                                if healthcheck_report['status']['message'] != status_message and healthcheck_report['status']['message'] != 'Running checks.':
                                    status_message = healthcheck_report['status']['message']
                                    logmsg.info("Percent complete {}".format(str(healthcheck_report['status']['percent'])))
                                    logmsg.debug(healthcheck_report)
                            else:
                                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                                logmsg.debug("{}: {}".format(response.status_code, response.text))
                                exit(1)
                        except:
                            logmsg.info("Unsuccessful return. See /var/log/mnode-support-util.log for details.")
                    report_file.write(json.dumps(healthcheck_report))
                    logmsg.info('HealthCheck completed. See report file ' + report_file_name)
                else:
                    logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                    logmsg.debug("{}: {}".format(response.status_code, response.text))
                    exit(1)
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug("{}: {}".format(response.status_code, response.text)) 