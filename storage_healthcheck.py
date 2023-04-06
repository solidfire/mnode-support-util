import json
import logging
import requests
import time
from get_token import get_token
from log_setup import Logging
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

# =====================================================================
# Storage healthcheck
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

# Generate a list of clusters
# 
class StorageHealthcheck():
    #============================================================
    # Display a list a storage clusters
    # Select cluster for the healthcheck
    def generate_cluster_list(repo):
        logmsg.info("\nAvailable clusters:")
        clusterlist = {}
        for cluster in repo.ASSETS[0]["storage"]:
            if cluster["host_name"]:
                logmsg.info("+ {}".format(cluster["host_name"]))
                clusterlist[(cluster["host_name"])] = cluster["id"]
            else:
                logmsg.info("+ {}".format(cluster["ip"]))
                clusterlist[(cluster["ip"])] = cluster["id"]
        userinput = input("Enter the target cluster name: ")
        storage_id = clusterlist[userinput]
        return storage_id

    #============================================================
    # Start the healthcheck
    def run_storage_healthcheck(repo, storage_id):
        get_token(repo)
        url = ('{}/storage/1/health-checks'.format(repo.BASE_URL))
        payload = {"config":{},"storageId":storage_id}
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return:
            if json_return['state'] == "initializing":
                logmsg.info("Healthcheck running...")
                return json_return
            else:
                logmsg.info("Failed return. There may be a Healthcheck already running for this target. See /var/log/mnode-support-util.log for details")
                exit()

    #============================================================
    # Watch the healthcheck progress
    # Write report to file
    def print_healthcheck_status(repo, healthcheck_start):
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        json_return = healthcheck_start
        if json_return:
            msg = "none"
            report_file_name = ('{}StorageHealthcheck-{}.json'.format(repo.SUPPORT_DIR,json_return['storageId']))
            url = ('{}/storage/1/health-checks/{}'.format(repo.BASE_URL,json_return['healthCheckId']))
            while not json_return['dateCompleted']:
                get_token(repo)
                json_return = PDApi.send_get_return_json(repo, url, 'no')
                if json_return['status']:
                    if msg != json_return['status']['message']:
                        msg = json_return['status']['message']
                        logmsg.info(json_return['status']['message'])
            if json_return['dateCompleted']:
                with open(report_file_name, "w") as outfile:
                    print(json.dumps(json_return), file=outfile)
                    logmsg.info("Storage Healthcheck completed. Report written to {}".format(report_file_name))
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
