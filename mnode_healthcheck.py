#!/usr/bin/env python
from datetime import datetime
import json
import os
import re
import requests
#from api_mnode import about
from api_inventory import Inventory
from docker import Docker
from get_token import GetToken
from log_setup import Logging
from program_data import Common
from requests.auth import HTTPBasicAuth
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

logmsg = Logging.logmsg()

class mNodeHealthCheck():
    def check_auth_token(repo, outfile):
        """ Check for valid auth token
        """
        print("\n===== Validating auth token =====", file=outfile)
        token = GetToken(repo, True)
        if token.token != "INVALID":
            print("\tRetrieving valid token succeeded.\n\tElement auth is healthy on the authorative cluster master.\n\tNo SSL issues between mnode and authorative cluster", file=outfile)
            repo.NEW_TOKEN = "False"
        else:
            print("\tRecived 200 but not a valid token. See /var/log/mnode-support-util.log for details", file=outfile)
        
    def check_auth_config(repo, outfile):
        """ Check for valid auth config
        """
        print("\n===== Auth client configuration =====", file=outfile)
        url = f'https://{repo.auth_mvip}/auth/api/1/configuration'
        json_return = requests.get(url, auth=HTTPBasicAuth(repo.mvip_user, repo.mvip_pw), verify=False)
        if json_return is not None:
            config_count = (len(json_return["apiClients"]) + len(json_return["apiResources"]))
            if config_count == 0:
                print("\tThere is problem with the auth configuration\n\tSee Solution in KB\nhttps://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/setup-mnode_script_or_Management_Services_update_fails_on_Element_mNode_12.2_with_configure_element_auth_error", file=outfile)
            else:
                print("\tapiClient and apiResources looks good. See /var/log/mnode-support-util.log to verify", file=outfile)
            return json_return
        
    def display_auth_mvip(repo, outfile):
        """ Display the authorative MVIP
        """
        print("\n===== Authorative storage cluster:  =====", file=outfile)
        print(repo.auth_mvip, file=outfile)
    
    def check_time_sync(repo, outfile):
        """ Check time sync between mNode and MVIP"""
        ntpservers = []
        time_doc = 'https://docs.netapp.com/us-en/hci/docs/task_mnode_install.html#configure-time-sync'
        print("\n===== Check time sync =====", file=outfile)
        with open("/etc/ntp.conf","r") as ntpconf:
            for line in ntpconf:
                if re.search("server",line) and not re.search("#",line):
                    ntpservers.append(line.strip())
        for server in ntpservers:
            splitline = server.split(" ")
            if "gentoo" in splitline[1]:
                print(f'\tFound default {splitline[1]}. Please edit /etc/ntp.conf and comment that out.', file=outfile)
            else:
                if repo.auth_mvip in splitline[1]:
                    print(f'\tServer {splitline[1]} is the authorative MVIP. EXCELLENT!!', file=outfile)
                else:
                    print(f'\tServer {splitline[1]} is not the authorative MVIP.', file=outfile)
                try:
                    cmd = f'/usr/sbin/ntpdate -q {splitline[1]}'
                    response = os.popen(cmd).read()
                    if response:
                        splitresponse = response.split(',')
                        offset = splitresponse[2].split(' ')
                    if "0." not in offset[2]:
                        print(f'\t\tTime sync offset is greater than 1: {offset}\n\tTROUBLESHOOTING TIP(s): See document: {time_doc}', file=outfile)
                    else:
                        print(f'\t\tSync offset is less than 1: {offset}', file=outfile)
                except OSError as exception:
                    logmsg.debug(exception)
                    logmsg.debug(f'{response.status_code}: {response.text}')
                    response = (f'ERROR: {cmd} Failed')
        
    def mnode_about(repo, outfile):
        """ Pring mnode about
        """
        print(f'\n===== mNode about: =====\n {repo.about}', file=outfile)

    def display_swarm_net(outfile):
        """ Print the container swarm IP's
        """
        print("\n===== Container swarm network. Ensure IP's do not overlapp with existing network\nhttps://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_mNode's_Docker_swarm_network_deploys_on_the_same_subnet_as_the_underlying_management_%2F%2F_infrastructure_network", file=outfile)
        containers = Docker.get_containers()
        for container in containers:
            container_ip = Docker.docker_container_net(container.split(' ')[0])
            print("\tContainer {:<33}: {:<20}".format(container.split(' ')[1].rstrip('\n'), container_ip), file=outfile)

    def service_uptime(repo, outfile):
        """ Check service uptimes and watch for suspect restarts
        """
        print("\n===== Checking service uptimes =====", file=outfile)
        minsec = 0
        hrday = 0
        ps = Docker.docker_ps(repo)
        for line in ps:
            if 'minute' in line or 'seconds' in line:
                minsec += 1
            if 'hour' in line or 'day' in line:
                hrday += 1
        if minsec > 0 and hrday > 0:
            print(f'\t{str(minsec)} services have short Uptimes. Services may be restarting.\n\tTROUBLESHOOTING TIP(s): Check sudo docker ps. Container service log, /var/log/docker.info and /var/log/syslog', file=outfile)
        else:
            print("\tAll services show about the same uptime. No signs of unexpected container restarts", file=outfile)

    def docker_log(outfile):
        """ Get the docker log
        """
        print("\n===== Parsing /var/log/docker.info =====", file=outfile)
        docker_errors = ParseLogs.parse_docker_log()
        if len(docker_errors) > 0:
            for line in docker_errors:
                print(f'{line}', file=outfile)


    def trident_log(outfile):
        """ Get the trident file if it exists
        """
        print("\n===== Parsing /var/log/trident/netapp.log =====", file=outfile)
        trident_errors = ParseLogs.parse_trident_log()
        if trident_errors > 0:
            print(f'\t{trident_errors} Errors found for persistent volume(s) in trident log', file=outfile)
            print("\tTROUBLESHOOTING TIP(s): Check the volume access and status. Ensure mnode has connectivty to the cluster SVIP.", file=outfile)

    def sf_prefrence(repo, outfile):
        """ Display the bound mNode
        """
        url = f'https://{repo.auth_mvip}/json-rpc/11.3?method=ListClusterInterfacePreferences'
        print("\n===== Checking cluster ListClusterInterfacePreferences =====", file=outfile)
        try:
            response = requests.get(url,auth=(repo.mvip_user, repo.mvip_pw), data={}, verify=False)
            if response.status_code == 200:
                try:
                    json_return = json.loads(response.text)
                except ValueError as error:
                    logmsg.debug(f'Bad return: {error}\n\t{response.status_code}\n\t{response.text}')
                    return None
                if json_return is not None:
                    print(f'\t{json_return}', file=outfile)
                    print("\tTROUBLESHOOTING TIP: ClusterInterfacePreference must match the mnode_ip and if present, the FQDN must resolve mnode_ip ", file=outfile)
                else:
                    print("\tNo mnode Interface Preference found. It may have been removed.\n\t", file=outfile)
                    print("\tCreate with: https://<MVIP>/json-rpc/11.3?method=CreateClusterInterfacePreference&name=mnode_ip&value=[mnodeip]", file=outfile)
            else:
                print(f'Failed return {response.status_code} See /var/log/mnode-support-util.log for details', file=outfile)
                logmsg.debug(f'{response.status_code}: {response.text}')
        except requests.exceptions.RequestException as exception:
            print("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(f'{response.status_code}: {response.text}') 

    def sf_const(repo, outfile):
        """ Displays constants that can affect element-auth
        """
        constants_reccomended = {
            "cAuthContainerMaxNotReadyTime":"00:00:20.000000", 
            "cAuthContainerMaxUnknownTime":"00:00:20.000000",
            "cAuthFailureEventFrequencyThreshold":"60",
            "cEnableAuthContainerMonitor":"true",
            "cElementAuthPort":"5555",
            "cEnableAuthContainerMonitor":"true",
            "cMaxAuthConfigurationDBSize":"1048576",
            "laAuthContainer":"5",
            "lcAuthContainer": "0"
        }
        url = f'https://{repo.auth_mvip}/json-rpc/11.3?method=GetConstants'
        print("\n===== Checking cluster Constants =====", file=outfile)
        try:
            response = requests.get(url,auth=(repo.mvip_user, repo.mvip_pw), data={}, verify=False)
            if response.status_code == 200:
                try:
                    json_return = json.loads(response.text)
                except ValueError as error:
                    logmsg.debug(f'Bad return: {error}\n\t{response.status_code}\n\t{response.text}')
                    return None
                if json_return is not None:
                    for line in json_return["result"]:
                        for constant in constants_reccomended:
                            if line == constant:
                                print(f'\t{constant:<40} Current: {json_return["result"][line]:<20} Recomended: {constants_reccomended[constant]:<20}', file=outfile)
            else:
                print(f'Failed return {response.status_code} See /var/log/mnode-support-util.log for details', file=outfile)
                logmsg.debug(f'{response.status_code}: {response.text}')
        except requests.exceptions.RequestException as exception:
            print("An exception occured. See /var/log/mnode-support-util.log for details", file=outfile)
            logmsg.debug(exception)
            logmsg.debug(f'{response.status_code}: {response.text}')

    def get_auth_about(repo, outfile):
        """ Get storage nodes auth about
        """
        print("\n===== Getting cluster nodes auth about =====", file=outfile)
        print("\tTROUBLESHOOTING TIP(s): If any values do not match other nodes, stop and start the auth container. Recheck https://[mip]/auth/about", file=outfile)
        print("\tssh to the node.\n\tdocker stop element_auth\n\tdocker start element_auth\n\tNOTE docker ps STATUS of Healthy does not mean element_auth is healthy.\n", file=outfile)
        url = (f'https://{repo.auth_mvip}/json-rpc/11.3?method=GetNetworkConfig&force=true')
        try:
            response = requests.get(url,auth=(repo.mvip_user, repo.mvip_pw), data={}, verify=False)
            if response.status_code == 200:
                try:
                    json_return = json.loads(response.text)
                except ValueError as error:
                    logmsg.debug(f'Bad return: {error}\n\t{response.status_code}\n\t{response.text}')
                    return None
                if json_return["result"]["nodes"]:
                    for node in json_return["result"]["nodes"]:
                        mip = (node['result']['network']['Bond1G']['address'])
                        try:
                            response = requests.get(f'https://{mip}/auth/about', data={}, verify=False)
                            if response.status_code == 200:
                                print(f'\tNode: {node["nodeID"]:<5} auth about: {response.text:<} ', file=outfile)
                        except requests.exceptions.RequestException as exception:
                            print("An exception occured. See /var/log/mnode-support-util.log for details", file=outfile)
                            logmsg.debug(exception)
                            logmsg.debug(f'{response.status_code}: {response.text}')
            else:
                print(f'Failed return {response.status_code} See /var/log/mnode-support-util.log for details', file=outfile)
                logmsg.debug(f'{response.status_code}: {response.text}')
        except requests.exceptions.RequestException as exception:
            print("An exception occured. See /var/log/mnode-support-util.log for details", file=outfile)
            logmsg.debug(exception)
            logmsg.debug(f'{response.status_code}: {response.text}')

    def inventory_error(repo):
        """ Print inventory and errors
        """
        json_return = Inventory.refresh_inventory(repo)
        if json_return is not None:
            return json_return
        
class ParseLogs():
    def parse_service_log(repo, log):
        """ Check service logs for common errors
        """
        messages = []
        found_error = []
        errors = {
            "vim.fault.NoPermission": "The vCenter or ESXi host asset was added with less than administrator credentials",
            "Exception HTTP 424": "Failed dependancy (Check engine light)\n\tExamine log for other errors\n\tFast Fix: Use mnode-support-util to backup current config. Run the mnode cleanup and setup. Then restore assets.",
            "incorrect user name or password": "The password on the system has changed since the asset was added. Update the asset password",
            "Invalid login": "The password on the system has changed since the asset was added. Update the asset password",
            "Error getting compute inventory": "The password on the ESXi host has changed. Update the asset password. ESXi host may be down.",
            "Compute node asset details are not available for compute node": "The password on the ESXi host has changed. Update the asset password. ESXi host may be down.",
            "token has expired": "Check time skew between mnode and storage cluster. Add authorative MVIP as server in /etc/ntp.conf",
            "Proxy Authentication Required": "The mnode settings proxy_username needs to be blanked out or proxy_password set",
            "Client Error: UNAUTHORIZED": "The credentials used when adding the asset are not administrator credentials",
            "FAILED to fetch ListAPIMethodsToFetch": "Check log to see if this is persistent.\n\tCheck mnode setting noVerifyCert:true.\n\tCheck proxy settings to the internet\n\tCheck network security to the internet",
            "SSL_ERROR_SSL": "Check log to see if this is persistent.\n\tCheck mnode setting noVerifyCert:true.\n\tIf custom cert is in place, revert to self signed and check custom cert requirments\n\thttps://kb.netapp.com/Special:Search?qid=&fpid=230&fpth=&query=Element+ssl+cert+requirments&type=wiki",
            "connection timeout": "Check log to see if this is persistent.\n\tVerify docker network does not overlap internal network\n\tVerify target ip/service is available",
            "Error parsing result": "An api call failed. Check upstream in the log for additional errors",
            "Failed to post data to AIQ": "Check mnode proxy seetings\n\tCheck mnode setting noVerifyCert:true.\n\tCheck nc -v monitoring.solidfire.com 443",
            "Max retries exceeded": "Check nc -v [IP] [PORT] from mnode ssh and container (docker exec -it <containerID> /bin/sh). Check AIQ for element-auth alerts",
            "InvalidClientError": "Client configuration may be empty or corrupt.\n\tCheck https://MVIP/auth/ui/swagger GET /api/1/configuration\n\tMax the auth DB size https://MVIP/json-rpc/12.0?method=SetConstants&cMaxAuthConfigurationDBSize=1048576"
        }
        for error in errors:
            for line in log:
                if error in line: 
                    if error not in found_error:
                        found_error.append(error)
                        messages.append(f'\n{line}:\n\tTROUBLESHOOTING TIP(s): {errors[error]}')
        return messages

    def parse_docker_log():
        """ Check docker logs for volume errors
        """
        dockerlog = "/var/log/docker.info"
        messages = []
        found_error = []
        loglines = []
        
        errors = [
            "VolumeDriver.Mount: error attaching volume",
            "starting container failed",
            "failed to deactivate service binding for container",
        ]

        try:
            with open(dockerlog,"r") as logfile:
                loglines = logfile.readlines()
                for error in errors:
                    for line in loglines:
                        if error in line:
                            if error not in found_error:
                                found_error.append(error)
                                messages.append(line)
        except FileNotFoundError:
            print(f'Cannot open {dockerlog}')
        return messages

    def parse_trident_log():
        """ Check the trident log for errors
        """
        tridentlog = "/var/log/trident/netapp.log"
        count = 0
        loglines = []
        try:
            with open(tridentlog,"r") as logfile:
                loglines = logfile.readlines()
            for line in loglines:
                if "ERRO" in line:
                    count += 1
        except FileNotFoundError:
            print(f'Cannot open {tridentlog}')
        return(count)

def healthcheck_run_all(repo):
        date_time = datetime.now()
        time_stamp = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        filename = f'mNodeHealthCheck-{time_stamp}.log'
        output_file = f'{repo.log_dir}{filename}'
        logmsg.info(f'Writing healthcheck to {filename}')
        try:
            with open(output_file, 'w') as outfile:
                for line in repo.about:
                    print(f'{line:<25}: {repo.about[line]:<25}', file=outfile)
                logmsg.info("+ Executing check_auth_token")
                mNodeHealthCheck.check_auth_token(repo, outfile)
                logmsg.info("+ Executing checkauth_config")
                mNodeHealthCheck.check_auth_config(repo, outfile)
                logmsg.info("+ Executing get_auth_about")
                mNodeHealthCheck.get_auth_about(repo, outfile)
                logmsg.info("+ Executing sf_prefrence")
                mNodeHealthCheck.sf_prefrence(repo, outfile)
                logmsg.info("+ Executing sf_const")
                mNodeHealthCheck.sf_const(repo, outfile)
                logmsg.info("+ Executing check_time_sync")
                mNodeHealthCheck.check_time_sync(repo, outfile)
                logmsg.info("+ Executing service_uptime")
                mNodeHealthCheck.service_uptime(repo, outfile)
                logmsg.info("+ Executing docker_log")
                mNodeHealthCheck.docker_log(outfile)
                logmsg.info("+ Executing trident_log")
                mNodeHealthCheck.trident_log(outfile)
                #logmsg.info("+ Executing service_logs")
                #mNodeHealthCheck.service_logs(repo, outfile)
            with open(output_file, "r") as outfile:
                content = outfile.read()
                Common.cleanup_download_dir("mNodeHealthCheck")
                Common.file_download(repo, content, filename)
        except FileNotFoundError:
            logmsg.info(f'Could not open {output_file}')

'''
Save this 
                    print("\tStep 1 - Cleanup: https://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/Management_Node_Docker_environement_cleanup", file=outfile)
                    print("\tStep 2 - Setup: https://docs.netapp.com/us-en/element-software/mnode/task_mnode_install.html#set-up-the-management-node", file=outfile)
                    print("\tStep 3. Update MS: https://docs.netapp.com/us-en/element-software/upgrade/task_hcc_update_management_services.html")



'''