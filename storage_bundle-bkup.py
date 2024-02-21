import logging
from datetime import datetime, timedelta
from get_token import get_token
from log_setup import Logging
from program_data import PDApi, Common
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

# gather a storage support bundle



# set up logging
logmsg = Logging.logmsg()

class StorageBundle():
    cluster_info = []
    selected_nodes = []

    def __init__(self):
        pass

    def get_cluster_nodes(repo, storage_id):
        get_token(repo)
        url = f'{repo.BASE_URL}/storage/1/{storage_id}/info'
        StorageBundle.cluster_info = PDApi.send_get_return_json(repo, url, debug=False)
        
    def select_cluster_nodes(repo, storage_id):
        """ list available nodes in the cluster
            select the nodes to gather bundles from 
        """
        nodelist = {}
        userinput = "999"
        
        StorageBundle.get_cluster_nodes(repo, storage_id)
        logmsg.info("\nAvailable nodes: ")
        for node in StorageBundle.cluster_info["nodes"]:
            nodelist[node["ListAllNodes"]["nodeID"]] = node["ListAllNodes"]["uuid"]
            logmsg.info(f'+ nodeID: {str(node["ListAllNodes"]["nodeID"])}\tMIP: {node["ListAllNodes"]["mip"]}')
        userinput = input("Enter the target node IDs separated by space: ")
        
        for nodeid in userinput.split(sep=" "):
            try:
                StorageBundle.selected_nodes.append(nodelist[int(nodeid)])
            except:
                logmsg.info(f'Not a valid nodeID: {nodeid}')
                exit(1)
    
    def make_bundle_payload(repo, storage_id):
        StorageBundle.select_cluster_nodes(repo, storage_id)    
        crash_dumps = input("Gather crash dumps? (y/n): ")
        if crash_dumps.lower() == 'y':
            crash_dumps = 'true'
        else:
            crash_dumps = 'false'

        log_hours = input("Enter the number of hours of log history to gather: ")
        time_now = datetime.now()
        log_history = (time_now - timedelta(hours=int(log_hours)))
        ### WATCH FOR A BUG
        storage_node_list = ','.join(f'"{value}"' for value in StorageBundle.selected_nodes)
        payload = {f' + "\"storageLogs\":true, \"modifiedSince\": \"{log_history}\", \"storageCrashDumps\": {crash_dumps}, \"storageNodeIds\":[{storage_node_list}]"'}
        return payload 

    def delete_existing_bundle(repo):
        """ iterate through the storage nodes and delete existing bundles
        """
        userinput = input("Would you like to delete existing storage node log bundles? (y/n) ")
        if userinput.lower() == 'y':
            payload = "{\n\t\"method\": \"DeleteAllSupportBundles\",\n\"params\": {},\n\"id\": 1\n}" 
            for node in StorageBundle.cluster_info["nodes"]:
                if str(node["ListAllNodes"]["uuid"]) in str(StorageBundle.selected_nodes):
                    logmsg.info(f'Delete existing bundles from node ID {str(node["ListAllNodes"]["nodeID"])}')
                    node_ip = node["ListAllNodes"]["mip"]
                    creds = PDApi.check_cluster_creds(repo, node_ip, node["ListAllNodes"]["name"])
                    url = f'https://{node_ip}:442/json-rpc/10.0/'
                    json_return = PDApi.mip_send_post_return_status(repo, url, payload, creds)
                    if json_return is not None:
                        logmsg.info(f'\tNode ID: {str(node["ListAllNodes"]["nodeID"])} = {json_return["result"]["details"]["output"]}')

    def start_bundle(repo, payload):
        """ start the gather log bundle task
        """
        url = f'{repo.BASE_URL}/logs/1/bundle'
        get_token(repo)
        logmsg.info("Starting log collection")
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return is not None:
            logmsg.info(f'Recieved 201: Collection task id {json_return["taskId"]}')
        else:
            logmsg.info(f'Status {json_return["status"]}: {json_return["detail"]}')
            exit(1)

    def watch_bundle(repo):
        """ watch progress and display the download link when completed
        """
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        url = f'{repo.BASE_URL}/logs/1/bundle'
        state = "inProgress"
        percent_complete = 1
        while state == "inProgress":
            get_token(repo)
            json_return = PDApi.send_get_return_json(repo, url, 'no')
            if json_return is not None:
                state = json_return["state"]
                if json_return["taskMonitor"]["percentComplete"] != percent_complete:
                    percent_complete = json_return["taskMonitor"]["percentComplete"]
                    logmsg.info(f'Percent complete: {json_return["taskMonitor"]}')
                if json_return["state"] == "failed":
                    logmsg.info(f'Log Collection {json_return["state"]} \n{json_return["summary"]}\n{json_return["downloadLink"].replace("127.0.0.1", repo.ABOUT["mnode_host_ip"])}')
                    exit(0)
                if json_return["downloadLink"]: 
                    logmsg.info(f'Log bundle creation complete: {json_return["downloadLink"].replace("127.0.0.1", repo.ABOUT["mnode_host_ip"])}')
                    exit(0)
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    def check_running_bundle(repo):
        """ Check for a bundle already in progress
        """
        url = f'{repo.BASE_URL}/logs/1/bundle'
        get_token(repo)
        logmsg.info("Checking for existing log collection task")
        text_return = PDApi.send_get_return_text(repo, url, debug=False)
        if "inProgress" in text_return:
            logmsg.info("A log collection is in progress. Cancel the collection or wait for it to complete before starting a new one.")
            return "inProgress"
        else:
            return "Completed"
                    

