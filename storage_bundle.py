import json
import logging
from urllib import response
import requests
from datetime import datetime, timedelta
from get_token import get_token
from log_setup import Logging
from api_storage import Clusters
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# gather a storage support bundle
#============================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

class StorageBundle():
    cluster_info = []
    selected_nodes = []
    def __init__(self):
        pass

    # =====================================================================
    # List all storage clusters in inventory and select the target cluster
    def list_storage_clusters(repo):
        logmsg.info("\nAvailable clusters:")
        clusterlist = {}
        for cluster in repo.ASSETS[0]["storage"]:
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
        return clusterlist[userinput]    

    # =====================================================================
    # list available nodes in the cluster
    # select the nodes to gather bundles from 
    def get_cluster_nodes(repo, storage_id):
        nodelist = {}
        userinput = "999"
        get_token(repo)
        url = ("{}/storage/1/{}/info".format(repo.BASE_URL,storage_id))
        StorageBundle.cluster_info = PDApi.send_get_return_json(repo, url)
        logmsg.info("\nAvailable nodes: ")
        for node in StorageBundle.cluster_info["nodes"]:
            nodelist[node["ListAllNodes"]["nodeID"]] = node["ListAllNodes"]["uuid"]
            logmsg.info("+ nodeID: {} nodeName: {}".format(str(node["ListAllNodes"]["nodeID"]),node["ListAllNodes"]["name"]))
        userinput = input("Enter the node IDs separated by space that you want a bundle from: ")
        for nodeid in userinput.split(sep=" "):
            try:
                StorageBundle.selected_nodes.append(nodelist[int(nodeid)])
            except:
                logmsg.info("Not a valid nodeID: {}".format(nodeid))
                exit(1)
        crash_dumps = input("Gather crash dumps? (y/n): ")
        if crash_dumps.lower() == 'y':
            crash_dumps = 'true'
        else:
            crash_dumps = 'false'
        log_hours = input("Enter the number of hours of log history to gather: ")
        time_now = datetime.now()
        log_history = (time_now - timedelta(hours=int(log_hours)))
        storage_node_list = ','.join('"{}"'.format(value) for value in StorageBundle.selected_nodes)
        payload = ('{' + "\"storageLogs\":true, \"modifiedSince\": \"{}\", \"storageCrashDumps\": {}, \"storageNodeIds\":[{value}]".format(log_history,crash_dumps,value=storage_node_list) + '}')
        return payload 

    # =====================================================================
    # iterate through the storage nodes and delete existing bundles
    def delete_existing_bundle(repo):
        userinput = input("Would you like to delete existing storage node log bundles? (y/n) ")
        if userinput.lower() == 'y':
            payload = "{\n\t\"method\": \"DeleteAllSupportBundles\",\n\"params\": {},\n\"id\": 1\n}" 
            for node in StorageBundle.cluster_info['nodes']:
                if str(node['ListAllNodes']['uuid']) in str(StorageBundle.selected_nodes):
                    logmsg.info("Delete existing bundles from node ID {}".format(str(node['ListAllNodes']['nodeID'])))
                    node_ip = node['ListAllNodes']['mip']
                    creds = PDApi.check_cluster_creds(repo, node_ip, node['ListAllNodes']['name'])
                    url = ("https://{}:442/json-rpc/10.0/".format(node_ip))
                    json_return = PDApi.mip_send_post_return_status(repo, url, payload, creds)
                    if json_return:
                        logmsg.info("\tNode ID: {} = {}".format(str(node['ListAllNodes']['nodeID']),json_return['result']['details']['output']))

    # =====================================================================
    # start the gather log bundle task
    def start_bundle(repo, payload):
        url = ("{}/logs/1/bundle".format(repo.BASE_URL))
        get_token(repo)
        logmsg.info("Starting log collection")
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return:
            logmsg.info('Recieved 201: Collection task id {}'.format(json_return['taskId']))
        else:
            logmsg.info('Status {}: {}'.format(json_return['status'],json_return['detail']))
            exit(1)

    # =====================================================================
    # watch progress and display the download link when completed
    def watch_bundle(repo):
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        url = ("{}/logs/1/bundle".format(repo.BASE_URL))
        state = "inProgress"
        percent_complete = 1
        while state == "inProgress":
            get_token(repo)
            json_return = PDApi.send_get_return_json(repo, url, 'no')
            if json_return:
                state = json_return["state"]
                if json_return["taskMonitor"]["percentComplete"] != percent_complete:
                    percent_complete = json_return["taskMonitor"]["percentComplete"]
                    logmsg.info("Percent complete: {}".format(json_return["taskMonitor"]["percentComplete"]))
                if json_return["state"] == "failed":
                    logmsg.info("Log Collection {} \n{}\n{}".format(json_return["state"],json_return["summary"],json_return['downloadLink'].replace("127.0.0.1", repo.ABOUT['mnode_host_ip'])))
                    exit(0)
                if json_return['downloadLink']: 
                    logmsg.info("Log bundle creation complete: {}".format(json_return["downloadLink"].replace("127.0.0.1", repo.ABOUT['mnode_host_ip'])))
                    exit(0)
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    def check_running_bundle(repo):
        url = ("{}/logs/1/bundle".format(repo.BASE_URL))
        get_token(repo)
        logmsg.info("Checking for existing log collection task")
        text_return = PDApi.send_get_return_text(repo, url)
        if "inProgress" in text_return:
            logmsg.info("A log collection is in progress. Cancel the collection or wait for it to complete before starting a new one.")
            return "inProgress"
        else:
            return "Completed"
                    

