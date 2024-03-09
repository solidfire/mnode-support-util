import json
import logging
from datetime import datetime, timedelta
from log_setup import Logging
from program_data import PDApi
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

# gather a storage support bundle



# set up logging
logmsg = Logging.logmsg()

class StorageBundle():

    def __init__(self, storage_id):
        self.storage_id = storage_id
        self.cluster_info = []
        self.nodelist = []
        self.selected_nodes = []

    def _get_cluster_nodes(self, repo):
        url = f'{repo.base_url}/storage/1/{self.storage_id}/info'
        self.cluster_info = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        
    def _select_cluster_nodes(self, repo):
        """ list available nodes in the cluster
            select the nodes to gather bundles from 
        """
        userinput = "999"
        
        self._get_cluster_nodes(repo)
        logmsg.info("\nAvailable nodes: ")
        for node in self.cluster_info["nodes"]:
            tmp_dict = {
                "nodeID": node['ListAllNodes']['nodeID'],
                "mip": node['ListAllNodes']['mip'],
                "sip": node['ListAllNodes']['sip'],
                "version": node['ListAllNodes']['softwareVersion'],
                "uuid": node['ListAllNodes']['uuid'],
                "name": node['ListAllNodes']['name']
            }
            self.nodelist.append(tmp_dict)
            logmsg.info(f'+ nodeID: {str(node["ListAllNodes"]["nodeID"])}\tMIP: {node["ListAllNodes"]["mip"]}')
        userinput = input("Enter the target node IDs separated by space: ")
        
        for id in userinput.split(sep=" "):
            for node in self.nodelist:
                if int(id) == node['nodeID']:
                    try:
                        self.selected_nodes.append(node)
                    except:
                        logmsg.info(f'Not a valid nodeID: {id}')
                        exit(1)
    
    def _make_bundle_payload(self, repo):
        self._select_cluster_nodes(repo)
        storage_node_list = []
        crash_dumps = input("Gather crash dumps? (y/n): ")
        if crash_dumps.lower() == 'y':
            crash_dumps = True
        else:
            crash_dumps = False

        log_hours = input("Enter the number of hours of log history to gather: ")
        time_now = datetime.now()
        log_history = str(time_now - timedelta(hours=int(log_hours)))

        for value in self.selected_nodes:
            storage_node_list.append(f'{value["uuid"]}')
        payload = {"storageLogs":True, "modifiedSince": log_history, "storageCrashDumps": crash_dumps, "storageNodeIds":storage_node_list}
        #payload = {"storageLogs":True, "modifiedSince": log_history, "storageCrashDumps": crash_dumps, "extraArgs": "--exclude zk_data_dump", "storageNodeIds":storage_node_list}
        # '{\n  "detail": "An error occurred preventing the requested log collection.  "message": "{\'extraArgs\': [\'Unknown field.\']}" "status": 400,\n  "title": "Bad Request",
        return payload 

    def _start_bundle(self, repo, payload):
        """ start the gather log bundle task
        """
        url = f'{repo.base_url}/logs/1/bundle'
        logmsg.info("Starting log collection")
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return is not None:
            logmsg.info(f'Recieved 201: Collection task id {json_return["taskId"]}')
        else:
            logmsg.info(f'Status {json_return["status"]}: {json_return["detail"]}')
            exit(1)

    def _watch_bundle(self, repo):
        """ watch progress and display the download link when completed
        """
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        url = f'{repo.base_url}/logs/1/bundle'
        state = "inProgress"
        percent_complete = 1
        while state == "inProgress":
            json_return = PDApi.send_get_return_json(repo, url, 'no')
            if json_return is not None:
                state = json_return["state"]
                if json_return["taskMonitor"]["percentComplete"] != percent_complete:
                    percent_complete = json_return["taskMonitor"]["percentComplete"]
                    logmsg.info(f'Percent complete: {json_return["taskMonitor"]["percentComplete"]}')
                if json_return["state"] == "failed":
                    download_url = json_return["downloadLink"].replace("127.0.0.1", repo.about["mnode_host_ip"])
                    return download_url
                if json_return['downloadLink'] is not None: 
                    download_url = json_return["downloadLink"].replace("127.0.0.1", repo.about["mnode_host_ip"])
                    return download_url
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)

    def _check_running_bundle(self, repo):
        """ Check for a bundle already in progress
        """
        url = f'{repo.base_url}/logs/1/bundle'
        logmsg.info("Checking for existing log collection task")
        text_return = PDApi.send_get_return_text(repo, url, debug=repo.debug)
        if "inProgress" in text_return:
            logmsg.info("A log collection is in progress. Cancel the collection or wait for it to complete before starting a new one.")
            return "inProgress"
        else:
            return "Completed"

    def collect_bundle(self, repo)                :
        if self._check_running_bundle(repo) == 'inProgress':
                self._watch_bundle(repo)
        else:
            payload = self._make_bundle_payload(repo)
            self.delete_existing_bundle(repo)
            self._start_bundle(repo, payload)
            download_url = self._watch_bundle(repo)
            if download_url is False:
                exit(1)
            else:
                return download_url

    def delete_existing_bundle(self, repo):
        """ iterate through the storage nodes and delete existing bundles
        """
        #self._select_cluster_nodes(repo)
        userinput = input("Would you like to delete existing storage node log bundles? (y/n) ")
        if userinput.lower() == 'y':
            payload = "{\n\t\"method\": \"DeleteAllSupportBundles\",\n\"params\": {},\n\"id\": 1\n}" 
            for node in self.selected_nodes:
                creds = PDApi.check_cluster_creds(repo, node['mip'], node['name'])
                url = f'https://{node["mip"]}:442/json-rpc/10.0/'
                json_return = PDApi.mip_send_post_return_status(url, payload, creds)
                if json_return is not None:
                    logmsg.info(f'\tNode ID: {node["nodeID"]} = {json_return["result"]["details"]["output"]}')
