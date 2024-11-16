import datetime
import fnmatch
import gzip
import json
import os
import tarfile
import threading
import time
import requests
import urllib3
from datetime import datetime
from log_setup import Logging
from program_data import Common, PDApi
from requests.auth import HTTPBasicAuth 
from storage_bundle import StorageBundle

# get the logging started up
logmsg = Logging.logmsg()

class ApiCall():            
    def send_get(repo, url, payload):
        header = {
        'Content-Type': 'application/json',
        }
        # disable ssl warnings so the log doesn't fill up
        urllib3.disable_warnings()
        print(f'api call: {url}')
        try:
            response = requests.get(url, headers=header, data=payload, verify=False, timeout=30)
            if response.status_code == 200:
                return response
            else:
                print(f'{url}\n\t{response.status_code}: {response.content}\n')
        except requests.exceptions.RequestException as exception:
            print(f'{url}\n\t{exception}\n')

    def send_post(repo, url, payload):
        header = {
        'Content-Type': 'application/json',
        }
        urllib3.disable_warnings()
        try:
            response = requests.post(url, headers=header, data=payload, verify=False, auth=HTTPBasicAuth(repo.target_cluster_admin, repo.target_cluster_passwd))
            if response.status_code == 200:
                return response
            else:
                print(f'{url}\n\t{response.status_code}: {response.content}\n')
        except requests.exceptions.RequestException as exception:
            print(exception)

class BlockRecovery():
    def build_hash_line(line_array):
        '''
        Build a recovery line and check_data list
        '''
        blockid = ''
        blockdata = ''
        for line in line_array:
            if 'blockIDRead=' in line:
                blockid = line.split('=')[1].rstrip()
            if 'Contents=' in line:
                blockdata = line.split('=')[1].rstrip()
            if len(blockid) > 0 and len(blockdata) > 0:
                recover_line = f'hash={blockid}&hashData={blockdata}\n'
                return recover_line

    def build_recovery(directory):
        Helper.unpack_data(directory)
        # Read the bs_disk_data_log and build the recovery file
        logmsg.info(f'Locating bs_disk_data_log in {directory}')
        bs_logs = Helper.find_files(directory, 'bs_disk_data_log*')
        recovery_data = set()
        for log in bs_logs:
            contents = Helper.open_file_return_list(log)
            for line in contents:
                if 'blockIDRead=' in line:
                    line_array = line.split()
                    recovery_line = BlockRecovery.build_hash_line(line_array)
                    recovery_data.add(recovery_line)
            if len(recovery_data) == 0:
                logmsg.info(f'\tNo block recovery data found in {log}')
        if len(recovery_data) == 0:
            logmsg.info('No block recovery data found in any log files\n')
        else:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
            recovery_file = f'{directory}/recovery-{timestamp}.blocks'
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(recovery_file, 'w') as file:
                recovery_data_sorted = sorted(recovery_data)
                del(recovery_data)
                for line in recovery_data_sorted:
                    file.write(line)
            logmsg.info(f'\nOutput written to {recovery_file}')
        return recovery_file

    def parse_missing_blocks(directory):
        missing_blocks = set()
        # find all the slice info files
        logmsg.info("Locating all sf-slice.info* logs...")
        slice_logs = Helper.find_files(directory, "sf-slice.info*")
        # open 1 at a time and search for 'GenerateXunknownBlockIDLog\|BSCheck xUnknownBlockID'
        for log in slice_logs:
            contents = Helper.open_file_return_list(log)
            for line in contents:
                if 'GenerateXunknownBlockIDLog|BSCheck xUnknownBlockID' in line:
                    block = line.split()[9]
                    blockid = block.split('=')[1]
                    missing_blocks.add(blockid)
        sorted_missing_blocks = sorted(missing_blocks)
        del(missing_blocks)
        del(slice_logs)
        logmsg.info(f'Found {len(sorted_missing_blocks)} missing blocks')
        return sorted_missing_blocks

    def recover(repo, blocks_file):
        url = f'https://{repo.target_cluster}/json-rpc/12.0?method=AddBlockToBS&'
        logmsg.info('Start block recovery...')
        with open(blocks_file, 'r') as file:
            blocks = file.readlines()
        for block in blocks:
            if 'hash' in block and 'hashData' in block:
                try:
                    logmsg.info(f'Executing {url}{block}')
                    addblock = f'{url}{block}'
                    response = requests.post(addblock, auth = HTTPBasicAuth(repo.target_cluster_admin, repo.target_cluster_passwd), verify=False)
                    json_response = Helper.check_json(response.text)
                    logmsg.info(json.dumps(json_response, indent=4))
                except requests.exceptions.RequestException as error:
                    logmsg.debug(error)
                    logmsg.debug(response.text)
            else:
                logmsg.info(f'Not valid hash=[blockid]&hashData=[content]\n\tSee /var/log/mnode-support-util.log for details')
                logmsg.debug(block)

    def start_bscheck(repo):
        url = f'https://{repo.target_cluster}/json-rpc/12.0?method=ResetConstants&constants=[\"cClusterBSCheckMode\",\"cBSCheckPauseMSec\"]'
        payload = {}
        headers = {}
        try:
            logmsg.info(f'Executing {url}')
            response = requests.get(url, headers=headers, data=payload, auth = HTTPBasicAuth(repo.target_cluster_admin, repo.target_cluster_passwd), verify=False)
            json_response = Helper.check_json(response.text)
            logmsg.info(json.dumps(json_response, indent=4))
        except requests.exceptions.RequestException as error:
            logmsg.debug(error)
            logmsg.debug(response.text)

        url = f'https://{repo.target_cluster}/json-rpc/12.0?method=StartClusterBSCheck'
        payload = {}
        headers = {}
        try:
            logmsg.info(f'Executing {url}')
            response = requests.get(url, headers=headers, data=payload, auth = HTTPBasicAuth(repo.target_cluster_admin, repo.target_cluster_passwd), verify=False)
            json_response = Helper.check_json(response.text)
            logmsg.info(json.dumps(json_response, indent=4))
        except requests.exceptions.RequestException as error:
            logmsg.debug(error)
            logmsg.debug(response.text)
        
class Bundle():
    def __init__(self):
        self.bundles = list()
        self.threads = list()

    def delete_existing_bundle(repo, mip):
        payload = json.dumps({"method": "DeleteAllSupportBundles","params": {},"id": 1})
        url = f'https://{mip}:442/json-rpc/12.0'
        response = ApiCall.send_post(repo, url, payload)
        return response

    def make_bundle(self, repo, mip):
        date_time = datetime.now()
        time_stamp = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        extra_args = "-i logs -e config_files -e crash -e drives -e ipmi_analyzer -e nvram -e power_supply -e procfs -e rtfi -e sysinfo -e zk_config -e zk_data_dump --compress gz"
        url = f'https://{mip}:442/json-rpc/12.0'
        payload = json.dumps({
            "method": "CreateSupportBundle",
            "params": {
                "bundleName": f'block_recovery-{time_stamp}',
                "extraArgs": extra_args
            },
            "id": 1
        })
        response = ApiCall.send_post(repo, url, payload)
        json_response = Helper.check_json(response.text)
        if 'error' in json_response:
            logmsg.info(json_response['error']['message'])
        else:
            self.bundles.append(json_response['result']['details']['url'][0])
            logmsg.debug(json_response['result']['details']['url'][0])

    def download(self, directory, url):
        local_filename = f'{directory}/{url.split("/")[-1]}'
        logmsg.info(f'Downloading {url} to {local_filename}')
        with requests.get(url, stream=True, verify=False) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        logmsg.info(f'\tDownload complete: ')

class Helper():
    def check_json(text):
        try:
            json_return = json.loads(text)
            return json_return
        except ValueError as error:
            print(f'An error occured: {error}')

    def find_files(directory, match_pattern):
        '''
        Recursively find all required log files
        '''
        if os.path.exists(directory): 
            matches = []
            for root, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    if fnmatch.fnmatch(filename, match_pattern):
                        matches.append(os.path.join(root, filename))
            if len(matches) > 0:
                return matches
            else:
                logmsg.info(f'No {match_pattern} files found in {directory}')
                exit(1)
        else:
            logmsg.info(f'{directory}: Not found')
            exit(1)

    def get_cluster_nodes(storage_id, repo):
        url = f'{repo.base_url}/storage/1/{storage_id}/info'
        cluster_info = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        nodes_info = []
        node_info = {}
        for node in cluster_info['nodes']:
            node_info[node['ListAllNodes']['nodeID']] = {}
            node_info[node['ListAllNodes']['nodeID']]['id'] = node['ListAllNodes']['nodeID']
            node_info[node['ListAllNodes']['nodeID']]['name'] = node['ListAllNodes']['name']
            node_info[node['ListAllNodes']['nodeID']]['ip'] = node['ListAllNodes']['mip']
            nodes_info.append(node_info)
        return node_info

    def open_file_return_list(filename):
        '''
        Open a file and return contents as a list
        '''
        contents = []
        logmsg.info(f'Opening {filename}')
        if os.path.isfile(filename):
            if 'gz' in filename:
                f = gzip.open(filename, "r")
                c = f.readlines()
                f.close()
                for line in c:
                    contents.append(line.decode("utf-8"))
                del(c)
            elif 'gz' not in filename:
                f = open(filename, "r")
                contents = f.readlines()
                f.close()
            return contents
        else:
            logmsg.info(f'Cannot open {filename}\n')

    def unpack(extract_path, filename):
        # need to un tar the bundles
        logmsg.info(f'\tUnpacking {filename} to {extract_path}')
        tar = tarfile.open(filename)
        tar.extractall(extract_path)
        tar.close
        os.chmod(extract_path, 0o755)
        time.sleep(5) # It needs a few seconds to finish untar-ing before the next step

    def unpack_data(directory):
        bs_logs = Helper.find_files(directory, '*bs*data*tar.gz')
        for bs_log in bs_logs:
            basename = os.path.basename(bs_log)
            extract_path = directory + '/' + basename.split('.tar.gz')[0]
            if not os.path.exists(extract_path):
                os.makedirs(extract_path)
            Helper.unpack(extract_path, bs_log)
            os.chmod(directory, 0o755)
