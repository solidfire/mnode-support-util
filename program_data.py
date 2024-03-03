import datetime
import getpass
import json
import os
import requests
import shutil
import subprocess
import tarfile
from get_token import GetToken
from log_setup import Logging, MLog
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""
"""
 global vaiarbles and functions
"""

# set up logging
logmsg = Logging.logmsg()

class ProgramData():
    def __init__(self, args):
        """ Very frequently used values """
        self.util_version = "3.5.1485"
        self.base_url = "https://127.0.0.1"
        self.debug = False
        self.download_dir = "/data/bundle/share"
        self.header_read = {}
        self.header_write = {}
        self.log_dir = "/var/log/"
        self.logs_svc_container = ""
        self.support_dir = "/var/log/mnode-support/"
        self.mvip_user = args.stuser
        self.mvip_pw = args.stpw
        self.parent_id = ""
        self.token_life = 0
        self.timeout = args.timeout
        self.about = self._about()
        self.auth_mvip = self._auth_mvip()
        self.download_url = f'https://{self.about["mnode_host_ip"]}/logs/1/bundle'
        
        
    def _about(self):
        """ Get assets /mnode/#/about/routes.v1.about.get
            Populate the instance ABOUT
        """
        header = {"Accept":"*/*"}
        url = (f'{self.base_url}/mnode/1/about')
        response = requests.get(url, headers=header, data={}, verify=False, timeout=self.timeout)
        if response is not None:
            response_json = Common.test_json_loads(response.text)
            return response_json
        
    def _auth_mvip(self):
        authmvip = self.about["token_url"].split('/')
        return authmvip[2]
        
class Common():
    def test_json_loads(json_string):
        try:
            json_return = json.loads(json_string)
            return json_return
        except ValueError as error:
            logmsg.debug(json_string)
            logmsg.info(f'{error}\nSee /var/log/mnode-support-util.log for details')
            
    def select_target_cluster(repo):
        """ List all storage clusters in inventory and select the target cluster
        """
        logmsg.info("\nAvailable clusters:")
        clusterlist = {}
        for cluster in repo.assets[0]["storage"]:
            if cluster["host_name"]:
                logmsg.info(f'+ {cluster["host_name"]}')
                clusterlist[(cluster["host_name"])] = cluster["id"]
            else:
                logmsg.info(f'+ {cluster["ip"]}')
                clusterlist[(cluster["ip"])] = cluster["id"]
        while True:
            userinput = input("Enter the target cluster from the list: ")
            if userinput in clusterlist:
                break
        return clusterlist[userinput]
    
    def file_download(repo, content, filename):
        download_file = f'{repo.download_dir}/{filename}'
        download_url = f'{repo.download_url}/{filename}'
        try:
            with open(download_file, "w") as outfile:
                print(content, file=outfile)
                logmsg.info(f'Download link: {download_url}')
        except FileNotFoundError as error:
            logmsg.debug(error) 

    def copy_file_to_download(repo, filename):
        try:
            output = subprocess.getoutput(f'docker cp {filename} {repo.logs_svc_container}:{repo.download_dir}')
            logmsg.debug(f'copy_file_to_download: docker cp {output}')
        except subprocess.CalledProcessError as error:
            logmsg.info(f'subprocess error: {error}')

    def copy_file_from_download(repo, filename):
        base_filename = os.path.basename(filename)
        try:
            output = subprocess.getoutput(f'docker cp {repo.logs_svc_container}:{repo.download_dir}/{base_filename} /tmp')
            logmsg.debug(f'copy_file_from_download: docker cp {output}')
        except subprocess.CalledProcessError as error:
            logmsg.info(f'subprocess error: {error}')
        
    def cleanup_download_dir(repo):
        try:
            output = subprocess.getoutput(f'docker exec {repo.logs_svc_container} rm -rf {repo.download_dir}/*')
            logmsg.debug(f'cleanup_download_dir: docker exec rm {output}')
        except subprocess.CalledProcessError as error:
            logmsg.info(f'subprocess error: {error}')

    def make_download_tar(repo, bundle_type, file_list):
        date_time = datetime.datetime.now()
        time_stamp = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        tar_file_name = f'{bundle_type}-{time_stamp}.tar'
        dest_tar_file = f'{repo.download_dir}/{tar_file_name}'
        try:
            output = subprocess.getoutput(f'docker exec {repo.logs_svc_container} tar cf {dest_tar_file} {repo.download_dir}/{file_list[0]} {repo.download_dir}/{file_list[1]}')
            if 'tar: removing leading' in output:
                return tar_file_name
            else:
                logmsg.info(f'tar failed: {output}')
        except subprocess.CalledProcessError as error:
            logmsg.info(f'subprocess error: {error}')

class PDApi():
    """ routine api calls 
    """ 
    # disable ssl warnings so the log doesn't fill up
    requests.packages.urllib3.disable_warnings()
        
    def _send_get(repo, url,  debug):
        """ generic requests.get 
        """
        GetToken(repo)
        try:
            if debug == True: 
                logmsg.debug(f'Sending GET {url}')
            response = requests.get(url, headers=repo.header_read, data={}, verify=False)
            if response.status_code < 299:
                if debug == True: 
                    logmsg.debug(f'{response.status_code}:') # {response.text}')
                return response
            else:
                logmsg.info(f'Failed return {response.status_code} See See /var/log/mnode-support-util.log for details.')
                logmsg.debug(str(response.content))
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)
    
    def _send_put(repo, url,  payload):
        """ generic requests.put 
        """
        GetToken(repo)
        try:
            logmsg.debug(f'Sending PUT {url}')
            response = requests.put(url, headers=repo.header_write, data=json.dumps(payload), verify=False)
            if response.status_code < 299:
                logmsg.debug(f'{response.status_code}: {response.text}')
                return response
            else:
                logmsg.info(f'Failed return {response.status_code} See See /var/log/mnode-support-util.log for details.')
                logmsg.debug(str(response.content))
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)
            
    def _send_post(repo, url,  payload):
        """ generic requests.post 
        """
        GetToken(repo)
        try:
            logmsg.debug(f'Sending POST {url}')
            response = requests.post(url, headers=repo.header_write, data=json.dumps(payload), verify=False)
            logmsg.debug(response)
            return response
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    def _send_delete(repo, url):
        """ generic requests.delete 
        """
        GetToken(repo)
        try:
            logmsg.debug(f'Sending DELETE {url}')
            response = requests.delete(url, headers=repo.header_write, data={}, verify=False)
            if response.status_code < 299:
                logmsg.debug(f'{response.status_code}: {response.text}')
                return response
            else:
                logmsg.info(f'Failed return {response.status_code} See See /var/log/mnode-support-util.log for details.')
                logmsg.debug(str(response.content))
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)
            
    def send_get_return_text(repo, url,  debug):
        """ send a GET return the text 
        """
        response = PDApi._send_get(repo, url,  debug)
        if response is not None:
            return response.text

    def send_get_return_json(repo, url,  debug):
        """ send a GET return the json 
        """
        response = PDApi._send_get(repo, url,  debug)
        if response is not None:
            response_json = Common.test_json_loads(response.text)
            return response_json

    def send_get_return_status(repo, url,  debug):
        """ send a GET return the status code 
        """
        response = PDApi._send_get(repo, url,  debug)
        if response is not None:
            return response.status_code

    def send_put_return_json(repo, url,  payload):
        """ send a PUT return the json 
        """
        response = PDApi._send_put(repo, url,  payload)
        if response is not None:
            response_json = Common.test_json_loads(response.text)
            return response_json

    def send_put_return_status(repo, url,  payload):
        """ send a PUT return the status code 
        """
        response = PDApi._send_put(repo, url,  payload)
        if response is not None:
            return response.status_code

    def send_put_return_json_nopayload(repo, url):
        """ send a PUT return the json. No payload 
        """
        response = PDApi._send_put(repo, url,  payload={})
        if response is not None:
            response_json = Common.test_json_loads(response.text)
            return response_json

    def send_post_return_json(repo, url,  payload):
        """ send a POST return the json 
        """
        response = PDApi._send_post(repo, url,  payload)
        if response is not None:
            response_json = Common.test_json_loads(response.text)
            return response_json

    def send_post_return_status(repo, url,  payload):
        """ send a POST return the status code 
        """
        response = PDApi._send_post(repo, url,  payload)
        if response is not None:
            return response.status_code

    def send_delete_return_status(repo, url):
        """ send a DELETE return the status code 
        """
        response = PDApi._send_delete(repo, url)
        if response is not None:
            return response.status_code

    def send_delete_return_json(repo, url):
        """ send a DELETE return the json 
        """
        response = PDApi._send_delete(repo, url)
        if response is not None:
            response_json = Common.test_json_loads(response.text)
            return response_json

    def check_cluster_creds(repo, mvip, host_name):
        """ Ensure the creds specified with ('-su', '--stuser') ('-sp', '--stpw') work on the current cluster
            Prompt for creds if the given creds fail
        """
        url = f'https://{mvip}/json-rpc/10.0'
        payload = "{\n\t\"method\": \"GetClusterInfo\",\n    \"params\": {},\n    \"id\": 1\n}"
        try:
            response = requests.post(url, auth=(repo.mvip_user, repo.mvip_pw), data=payload, verify=False)
            stuser = repo.mvip_user
            stpw = repo.mvip_pw
            if response.status_code == 401:
                while response.status_code == 401:
                    logmsg.info(f'The provided credentials failed on cluster {host_name}')
                    stuser = input(f'Enter admin userid for cluster {host_name} : ')
                    stpw = getpass.getpass(prompt="Enter admin password: ")
                    response = requests.post(url, auth=(stuser, stpw), data=payload, verify=False)
            return response.status_code, stuser, stpw
        except requests.exceptions.RequestException as exception:
                MLog.log_exception(exception)

    def mip_send_get_return_json(creds, url, node_ip, payload):
        """ MIP send GET return json 
        """
        url = f'https://{node_ip}:442/json-rpc/10.0/'
        try:
            logmsg.debug(f'Sending POST {url} {payload}')
            response = requests.post(url, auth=(creds[1], creds[2]), data=payload, verify=False)
            logmsg.debug(f'{response.status_code}: {response.text}')
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = Common.test_json_loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)   

    def mip_send_post_return_status(url, payload, creds):
        """ MIP send POST return json 
        """
        try:
            logmsg.debug(f'Sending POST {url} {payload}')
            response = requests.post(url, auth=(creds[1], creds[2]), data=payload, verify=False)
            logmsg.debug(f'{response.status_code}: {response.text}')
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = Common.test_json_loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)