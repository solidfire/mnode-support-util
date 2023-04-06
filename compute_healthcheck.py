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
# Compute healthcheck
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

# Generate a list of clusters
# 
class ComputeHealthcheck():
    #============================================================
    # Display a list of vCenters.
    # Select target vCenter. Auto select if only one.
    def generate_cluster_list(repo):
        logmsg.info("Generating Controller List....")
        controllerlist = {}
        userinput = ""
        for controller in repo.ASSETS[0]['controller']:
            logmsg.info("Controller name: {} ".format(controller['host_name']))
            controllerlist[(controller["host_name"])] = controller["id"]
        if len(repo.ASSETS[0]['controller']) > 1:
            while userinput not in controllerlist:
                userinput = input("\nEnter the controller name: ")            
            controller_id = controllerlist[userinput]
        else:
            controller_id = repo.ASSETS[0]['controller'][0]['id']
        return controller_id

    #============================================================
    # Display a list of Host Clusters
    # Select target host cluster. Auto select if only one
    def generate_domain_list(repo, controller_id):
        userinput = "none"
        get_token(repo)
        url = ('{}/vcenter/1/compute/{}/clusters?includeUnmanaged=true'.format(repo.BASE_URL,controller_id))
        domainlist = {}
        logmsg.info("\nGenerating Domain list (Host clusters)...")
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            for result in json_return["result"]:
                try:
                    logmsg.info("{}".format(result["clusterName"]))
                    domainlist[(result["clusterName"])] = result["clusterId"]
                except:
                    logmsg.info("No valid result for controller {}".format(userinput))
        else:
            logmsg.info("No valid result for controller {}".format(userinput))
            exit(1)
        if len(domainlist) > 1:
            while userinput not in domainlist:
                    userinput = input("\nEnter the domain name: ")
                    cluster_id = domainlist[userinput]
        else:
            cluster_id = domainlist['NetApp-HCI-Cluster-01']
        return cluster_id

    #============================================================
    # Start the healthcheck
    def run_compute_healthcheck(repo, controller_id, cluster_id):
        get_token(repo)
        url = ("{}/vcenter/1/compute/{}/health-checks".format(repo.BASE_URL,controller_id))
        payload = {"cluster": cluster_id,"nodes":[]}
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return:
            logmsg.info("Healthcheck running...")
            return json_return
        else:
            logmsg.info("Failed return. There may be a Healthcheck already running for this target. See /var/log/mnode-support-util.log for details")
            exit(1)

    #============================================================
    # Watch the progress
    # Write report to file
    def print_healthcheck_status(repo, healthcheck_start):
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        report_file_name = ('{}ComputeHealthcheck-{}.json'.format(repo.SUPPORT_DIR,healthcheck_start['taskId']))
        step = "none"
        url = ('{}/task-monitor/1/tasks/{}'.format(repo.BASE_URL,healthcheck_start['taskId']))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            while json_return['state'] == "inProgress":
                get_token(repo)
                json_return = PDApi.send_get_return_json(repo, url, 'no')
                if json_return:
                    if step != json_return['step']:
                        step = json_return['step']
                        logmsg.info(step)
            if json_return['state'] == 'completed':
                resource_link = json_return['resourceLink']
                url = (resource_link.replace("127.0.0.1", repo.ABOUT['mnode_host_ip']))
                resource_json = PDApi.send_get_return_json(repo, url)
                with open(report_file_name, "w") as outfile:
                    print(json.dumps(resource_json), file=outfile)
                if resource_json['result']['errors']:
                    logmsg.info("Error(s) encountered")
                    for error in resource_json['result']['errors']:
                        logmsg.info("\t{}".format(error))
                    logmsg.info("Healthcheck completed with error(s). See report {}".format(report_file_name))
                else:
                    logmsg.info("Healthcheck completed without error(s). See report {}".format(report_file_name))
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)