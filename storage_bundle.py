import datetime
import json
import logging
from urllib import response
import requests
import shutil
import time
from get_token import get_token
from log_setup import Logging
from storage import Clusters

logmsg = Logging.logmsg()
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
class StorageBundle():    
    def get_storage_cluster(repo):
        # List all storage clusters in inventory and select the target cluster
        logmsg.info("\nAvailable clusters:")
        clusterlist = {}
        for cluster in repo.CURRENT_ASSET_JSON[0]["storage"]:
            if cluster["host_name"]:
                logmsg.info("+ {}".format(cluster["host_name"]))
                clusterlist[(cluster["host_name"])] = cluster["id"]
            else:
                logmsg.info("+ {}".format(cluster["ip"]))
                clusterlist[(cluster["ip"])] = cluster["id"]
        while True:
            userinput = input("Enter the target cluster from the list: ")
            if userinput in clusterlist:
                break
        repo.STORAGE_ID = clusterlist[userinput]    
        
    def get_existing_bundle(repo):
        # check the mnode for an existing bundle and delete
        # iterate through the storage nodes and delete existing bundles
        logmsg.info("\nChecking mnode for exiting log bundles")
        url = ("{}/logs/1/bundle".format(repo.URL))
        get_token(repo)
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                response_json = json.loads(response.text)
                if response_json['downloadLink']:
                    logmsg.info("Found existing bundle {}\n".format(response_json['downloadLink'].replace("127.0.0.1", repo.MNODEIP)))
                    userinput = input("Delete Bundle? (y/n) ")
                    if userinput.lower() == 'y':
                        get_token(repo)
                        logmsg.info("Deleting bundle {}".format(response_json['downloadLink'].replace("127.0.0.1", repo.MNODEIP)))
                        logmsg.debug("Sending DELETE {}".format(url))
                        response = requests.delete(url, headers=repo.HEADER_WRITE, data={}, verify=False)
                        logmsg.debug(response.text)
                        if response.status_code == 204:
                            logmsg.info("Deleted successfully\n")
                        else:
                            logmsg.info("Error while deleting bundle. See /var/log/mnode-support-util.log for details.")
                else:
                    logmsg.info(response_json['summary'])
            else:
                logmsg.info("Error while checking for bundles. See /var/log/mnode-support-util.log for details")
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)        
            logmsg.info("Checking free space")
        
        userinput = input("Would you like to delete existing storage node log bundles? (y/n) ")
        if userinput.lower() == 'y':
            payload = "{\n\t\"method\": \"DeleteAllSupportBundles\",\n\"params\": {},\n\"id\": 1\n}" 
            for node in repo.CLUSTER_INFO['nodes']:
                if str(node['ListAllNodes']['nodeID']) in str(repo.SELECTED_NODES):
                    logmsg.info("Delete existing bundles from node ID {}".format(str(node['ListAllNodes']['nodeID'])))
                    node_ip = node['ListAllNodes']['mip']
                    creds = Clusters.check_cluster_creds(repo, node_ip, node['ListAllNodes']['name'])
                    url = ("https://{}:442/json-rpc/10.0/".format(node_ip))
                    try:
                        logmsg.debug("Sending POST {} {}".format(url,payload))
                        response = requests.post(url, auth=(creds[1], creds[2]), data=payload, verify=False)
                        logmsg.debug(response.text)
                        if response.status_code == 200:
                            response_json = json.loads(response.text)
                            logmsg.info("Node ID: {} = {}\n".format(str(node['ListAllNodes']['nodeID']),response_json['result']['details']['output']))
                        if response.status_code == 400:
                            logmsg.info("Received 400 BAD_REQUEST. See /var/log/mnode-support-util.log for details. Continuing...")
                            logmsg.debug(response.text)
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)    
                        
    def get_cluster_nodes(repo):
        # list available nodes in the cluster
        # select the nodes to gather bundles from 
        nodelist = {}
        crash_dumps = 'false'
        storage_node_ids = []
        userinput = "999"
        get_token(repo)
        url = ("{}/storage/1/{}/info".format(repo.URL,repo.STORAGE_ID))
        try:
            logmsg.info("Retrieving node list")
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            logmsg.debug(response.text)
            if response.status_code == 200:
                repo.CLUSTER_INFO = json.loads(response.text)
                logmsg.info("\nAvailable nodes: ")
                for node in repo.CLUSTER_INFO["nodes"]:
                    nodelist[node["ListAllNodes"]["nodeID"]] = node["ListAllNodes"]["uuid"]
                    logmsg.info("+ nodeID: {} nodeName: {}".format(str(node["ListAllNodes"]["nodeID"]),node["ListAllNodes"]["name"]))
                userinput = input("Enter the node IDs separated by space that you want a bundle from: ")
            else:
                logmsg.info("Failed status code {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                exit(1)
            for nodeid in userinput.split(sep=" "):
                try:
                    repo.SELECTED_NODES.append(nodelist[int(nodeid)])
                except:
                    logmsg.info("Not a valid nodeID: {}".format(nodeid))
                    exit(1)

            crash_dumps = input("Gather crash dumps? (y/n): ")
            if crash_dumps.lower() == 'y':
                crash_dumps = 'true'
            else: 
                crash_dumps = 'false'

            log_hours = input("Enter the number of hours of log history to gather: ")
            time_now = datetime.datetime.now()
            log_history = time_now - datetime.timedelta(hours=int(log_hours))
            storage_node_list = ','.join('"{}"'.format(value) for value in repo.SELECTED_NODES)
            payload = ('{' + "\"modifiedSince\": \"{}\", \"storageCrashDumps\": {}, \"storageLogs\":true,\"storageNodeIds\":[{value}]".format(log_history,crash_dumps,value=storage_node_list) + '}')
            repo.PAYLOAD = payload 
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
        
    def start_bundle(repo):
        # start the gather log bundle task
        url = ("{}/logs/1/bundle".format(repo.URL))
        get_token(repo)
        logmsg.info("Starting log collection")
        try:
            logmsg.debug("Sending POST {} {}".format(url,str(repo.PAYLOAD)))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=repo.PAYLOAD, verify=False)
            logmsg.debug(response.text)
            response_json = json.loads(response.text)
            if response.status_code == 201:
                logmsg.info('Recieved 201: Collection task id {}'.format(response_json['taskId']))
            elif response.status_code == 409:
                logmsg.info('Status {}: {}'.format(response_json['status'],response_json['detail']))
                exit(1)
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text)     
            
    def watch_bundle(repo):
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        # watch progress and display the download link when completed
        url = ("{}/logs/1/bundle".format(repo.URL))
        state = "inProgress"
        percent_complete = 1
        while state == "inProgress":
            try:
                get_token(repo)
                response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                if response.status_code == 200:
                    response_json = json.loads(response.text)
                    state = response_json["state"]
                    if response_json["taskMonitor"]["percentComplete"] != percent_complete:
                        percent_complete = response_json["taskMonitor"]["percentComplete"]
                        logmsg.info("Percent complete: {}".format(response_json["taskMonitor"]["percentComplete"]))
                    if response_json["state"] == "failed":
                        logmsg.info("Log Collection {} \n{}\n{}".format(response_json["state"],response_json["summary"],response_json['downloadLink'].replace("127.0.0.1", repo.MNODEIP)))
                        exit(0)
                    if response_json["downloadLink"]: 
                        logmsg.info("Log bundle creation complete: {}".format(response_json["downloadLink"].replace("127.0.0.1", repo.MNODEIP)))
                        exit(0)
                else:
                    logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                    logmsg.debug(response.text)
                    exit(1)
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug(response.text)
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    def check_running_bundle(repo):
        url = ("{}/logs/1/bundle".format(repo.URL))
        try:
            get_token(repo)
            logmsg.info("Checking for existing log collection task")
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if response.status_code == 200:
                if "inProgress" in response.text:
                    logmsg.info("A log collection is in progress. Cancel the collection or wait for it to complete before starting a new one.")
                    return "inProgress"
                else:
                    return "Completed"
        except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug(response.text)
                    

