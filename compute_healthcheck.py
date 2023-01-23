import json
import logging
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
class ComputeHealthcheck():

    def generate_cluster_list(repo):
        logmsg.info("Generating Controller List....")
        controllerlist = {}
        userinput = ""
        for controller in repo.CURRENT_ASSET_JSON[0]['controller']:
            logmsg.info("Controller name: {} ".format(controller['host_name']))
            controllerlist[(controller["host_name"])] = controller["id"]
            repo.CONTROLLERS.append(controller['id'])
        while userinput not in controllerlist:
            userinput = input("\nEnter the controller name: ")
            
        repo.CONTROLLER_ID = controllerlist[userinput]

    def generate_domain_list(repo):
        get_token(repo)
        url = ('{}/vcenter/1/compute/{}/clusters?includeUnmanaged=true'.format(repo.URL,repo.CONTROLLER_ID))
        payload = {}
        domainlist = {}
        logmsg.info("\nGenerating Domain list for controller {}".format(userinput))
        try:
            logmsg.debug("Sending GET {} {}".format(url,json.dumps(payload)))
            response = requests.get(url, headers=repo.HEADER_READ, data=json.dumps(payload), verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                response_json = json.loads(response.text)
                if(len(response_json["result"]) != 0):
                    for result in response_json["result"]:
                        try:
                            logmsg.info("{}".format(result["clusterName"]))
                            domainlist[(result["clusterName"])] = result["clusterId"]
                        except:
                            logmsg.info("No valid result for controller {}".format(userinput))
                else:
                    logmsg.info("No valid result for controller {}".format(userinput))
                    exit(1)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
            while userinput not in domainlist:
                userinput = input("\nEnter the domain name: ")
                
            repo.CLUSTER_ID = domainlist[userinput]
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
        
    def run_compute_healthcheck(repo):
        get_token(repo)
        url = ("{}/vcenter/1/compute/{}/health-checks".format(repo.URL,repo.CONTROLLER_ID))
        payload = {"cluster": repo.CLUSTER_ID,"nodes":[]}
        try:
            logmsg.debug("Sending GET {} {}".format(url,json.dumps(payload)))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug(response.text)
            if response.status_code == 202:
                repo.COMPUTE_HEALTHCHECK_TASK = json.loads(response.text)
                logmsg.info("Healthcheck running...")
                logmsg.info(json.dumps(response.text))
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def print_healthcheck_status(repo):
        healthcheck_report = []
        task = []
        percent_complete = 0
        url = ('{}/task-monitor/1/tasks/{}'.format(repo.URL,repo.COMPUTE_HEALTHCHECK_TASK['taskId']))
        payload = {}
        try:
            logmsg.debug("Sending GET {} {}".format(url,payload))
            get_token(repo)
            response = requests.get(url, headers=repo.HEADER_READ, data=payload, verify=False)
            task = (json.loads(response.text))
            logmsg.info(task['step'])
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 
        
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        while percent_complete != 100:
            get_token(repo)
            step = task['step']
            try:
                response = requests.get(url, headers=repo.HEADER_READ, data=payload, verify=False)
                if response.status_code == 200:
                    task = (json.loads(response.text))
                    if percent_complete != task['percentComplete']:
                        logmsg.debug(task)
                        logmsg.info("Percent complete: {}".format(str(task['percentComplete'])))
                        percent_complete = task['percentComplete']
                    if step != task['step']:
                        step = task['step']
                        logmsg.info(step)
                else:
                    logmsg.info("Received an unsuccessful return. See /var/log/mnode-support-util.log for details")
                    logmsg.debug(response.status_code)
                    logmsg.debug(response.text)
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug(response.text) 

        url = task['resourceLink'].split('/')
        url[2] = "127.0.0.1"
        rl = '/'.join(url)
        try:
            logmsg.debug("Sending GET {} {}".format(url,payload))
            get_token(repo)
            response = requests.get( rl, headers=repo.HEADER_READ, data=payload, verify=False)
            healthcheck_report = (json.loads(response.text))
            filename = (repo.SUPPORT_DIR + repo.CLUSTER_ID + "-compute_healthcheck.json")
            try:
                with open(filename, 'w') as outfile:  
                    if healthcheck_report['result']['errors']:
                        logmsg.info("\nErrors occured")
                    logmsg.info("Report file: {}".format(filename))
                    json.dump(healthcheck_report, outfile)
                    outfile.close()
            except FileNotFoundError:
                logmsg.info("Could not open {}".format(filename))
            logmsg.debug(healthcheck_report)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)