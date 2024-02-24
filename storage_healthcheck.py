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
class StorageHealthcheck():

    def run_storage_healthcheck(repo, storage_id):
        """ Start the healthcheck
        """
        url = f'{repo.base_url}/storage/1/health-checks'
        payload = {"config":{},"storageId":storage_id}
        json_return = PDApi.send_post_return_json(repo, url, payload)
        if json_return is not None:
            if json_return["state"] == "initializing":
                logmsg.info("Healthcheck running...")
                return json_return
            else:
                logmsg.info("Failed return. There may be a Healthcheck already running for this target. See /var/log/mnode-support-util.log for details")
                exit()

    def print_healthcheck_status(repo, healthcheck_start):
        """ Watch the healthcheck progress
            Write report to file
        """
        # prevent the log from filling up with debug messages in the while loop
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        json_return = healthcheck_start
        if json_return is not None:
            msg = "none"
            report_file_name = f'StorageHealthcheck-{json_return["storageId"]}.json'
            local_report = f'{repo.support_dir}{report_file_name}'
            url = f'{repo.base_url}/storage/1/health-checks/{json_return["healthCheckId"]}'
            while not json_return["dateCompleted"]:
                json_return = PDApi.send_get_return_json(repo, url, 'no')
                if json_return['status'] is not None:
                    if msg != json_return["status"]["message"]:
                        msg = json_return["status"]["message"]
                        if json_return['status']['message'] != 'Running checks.':
                            logmsg.info(json_return["status"]["message"])
            if "dateCompleted" in json_return.keys():
                with open(local_report, "w") as outfile:
                    print(json.dumps(json_return), file=outfile)
                    logmsg.info(f'Storage Healthcheck completed. Report written to {local_report}')
                Common.file_download(repo, json.dumps(json_return), report_file_name)
        # Set logging back to debug
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
