import json
import logging
from log_setup import Logging
from program_data import PDApi, Common
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

# set up logging
logmsg = Logging.logmsg()

# Generate a list of clusters
# 
class ComputeHealthcheck():
    def generate_cluster_list(repo):
        """ Display a list of vCenters.
            Select target vCenter. Auto select if only one.
        """
        logmsg.info("Generating Controller List....")
        controllerlist = {}
        userinput = ""

        for controller in repo.assets[0]["controller"]:
            logmsg.info(f'Controller name: {controller["host_name"]} ')
            controllerlist[(controller["host_name"])] = controller["id"]

        if len(repo.assets[0]["controller"]) > 1:
            while userinput not in controllerlist:
                userinput = input("\nEnter the controller name: ")            
            controller_id = controllerlist[userinput]
        else:
            controller_id = repo.assets[0]["controller"][0]["id"]

        return controller_id

    def generate_domain_list(repo, controller_id):
        """  Display a list of Host Clusters
        Select target host cluster. Auto select if only one
        """
        userinput = "none"
        url = f'{repo.base_url}/vcenter/1/compute/{controller_id}/clusters?includeUnmanaged=true'
        domainlist = {}
        logmsg.info("\nGenerating Domain list (Host clusters)...")
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)

        if json_return is not None: #or json_return['status'] != 400: #424 bad login
            if 'result' in json_return:
                for result in json_return["result"]:
                    try:
                        logmsg.info(f'{result["clusterName"]}')
                        domainlist[(result["clusterName"])] = result["clusterId"]
                    except:
                        logmsg.info(f'No valid result for controller {userinput}')
            else:
                logmsg.info(f'No valid result for controller {userinput} or login credentials failed')
                exit(1)

        while userinput not in domainlist:
                userinput = input("\nEnter the domain name: ")
                cluster_id = domainlist[userinput]

        return cluster_id

    def run_compute_healthcheck(repo, controller_id, cluster_id):
        """ Start the healthcheck """
        url = f'{repo.base_url}/vcenter/1/compute/{controller_id}/health-checks'
        payload = {"cluster": cluster_id,"nodes":[]}
        json_return = PDApi.send_post_return_json(repo, url, payload)

        if json_return is not None:
            logmsg.info("Healthcheck running...")
            return json_return
        else:
            logmsg.info("Failed return. There may be a Healthcheck already running for this target. See /var/log/mnode-support-util.log for details")
            exit(1)

    def print_healthcheck_status(repo, healthcheck_start):
        """ Watch the progress
            Write report to file
        """
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        
        report_file_name = f'ComputeHealthcheck-{healthcheck_start["taskId"]}.json'
        output_file = f'{repo.support_dir}{report_file_name}'
        step = "none"
        url = f'{repo.base_url}/task-monitor/1/tasks/{healthcheck_start["taskId"]}'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        
        if json_return is not None:
            while json_return["state"] == "inProgress":
                json_return = PDApi.send_get_return_json(repo, url, 'no')
                if json_return is not None:
                    if step != json_return["step"]:
                        step = json_return["step"]
                        logmsg.info(step)
        
            if json_return["state"] == 'completed':
                resource_link = json_return["resourceLink"]
                url = (resource_link.replace("127.0.0.1", repo.about["mnode_host_ip"]))
                resource_json = PDApi.send_get_return_json(repo, url, debug=repo.debug)
                with open(output_file, "w") as outfile:
                    print(json.dumps(resource_json), file=outfile)
                    logmsg.info(f'Healthcheck completed. See report {output_file}')
                Common.cleanup_download_dir("ComputeHealthcheck")
                Common.file_download(repo, json.dumps(resource_json), report_file_name)
        
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)