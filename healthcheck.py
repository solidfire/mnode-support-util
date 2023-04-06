#!/usr/bin/env python
import json
import os
import re
import requests
from mnode import about
from docker import DockerInfo
from get_token import get_token
from log_setup import Logging
from mnode import Services
from storage import Clusters
from system import System

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

logmsg = Logging.logmsg()

class HealthCheck():
    def check_auth_token(repo):
        logmsg.info("\nValidating auth token...")
        repo.NEW_TOKEN == True
        get_token(repo)
        if repo.TOKEN_LIFE > 1668982984:
            logmsg.info("\tRetrieving valid token succeeded")
        else:
            logmsg.info("\tFailed to retrieve token. See KB\nhttps://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/MissingTokenError_when_%22Attempting_to_retrieve_auth_token%22")            

    def checkauth_container(repo):
        troubleshooting = [
            "If the EOS version is NOT 12.5 or higher, increase cMaxAuthConfigurationDBSize\n\thttps://MVIP/json-rpc/12.0?method=SetConstants&cMaxAuthConfigurationDBSize=1048576\n",
            "Increase container polling time\n\thttps://MVIP/json-rpc/12.0?method=SetConstants&cAuthContainerMaxNotReadyTime=00:00:15.000000",
            "Use GetNetworkConfig api output to Verify if VLAN tagging for 1G is consistent. The VLAN has to be identical for all nodes on 1G",
            "Gather auth about returns from MVIP and all node mip's for api version info\n\thttps://<mvip>/auth/about https://<mip>/auth/about",
            "Gather auth configuration for mNode services if services are failing. Such as no AIQ reporting or unable to use HCC\n\thttps://<mvip>/auth/ui/swagger/ GET configuration",
            "NOTE: MVIP discovery will fail during CM election. Some errors are expected during CM election"
        ]
        logmsg.info("\nChecking auth container status")
        status = Clusters.check_auth_container(repo) 
        if status['authCheckIssueFound'] == False:
            logmsg.info("\tNo issues found in auth container status")
        else:
            logmsg.info("\tIssues found with auth container status.")
            for step in troubleshooting:
                logmsg.info(step)

    def checkauth_config(repo):
        logmsg.info("\nAuth client configuration")
        Clusters.check_auth_config(repo)
        
    def display_auth_mvip(repo):
        logmsg.info("\nAuthorative storage cluster: ")
        logmsg.info(repo.INVENTORY_AUTHORATIVE_CLUSTER)
    
    def check_time_sync(repo):
        ntpservers = []
        time_doc = 'https://docs.netapp.com/us-en/hci/docs/task_mnode_install.html#configure-time-sync'
        logmsg.info("\nCheck time sync")
        with open("/etc/ntp.conf","r") as ntpconf:
            for line in ntpconf:
                if re.search("server",line) and not re.search("#",line):
                    ntpservers.append(line.strip())
        for server in ntpservers:
            splitline = server.split(" ")
            if "gentoo" in splitline[1]:
                logmsg.info("\tFound default {}. Please edit /etc/ntp.conf and comment that out.".format(splitline[1]))
            else:
                if repo.INVENTORY_AUTHORATIVE_CLUSTER in splitline[1]:
                    logmsg.info("\tServer {} is the authorative MVIP. EXCELLENT!!".format(splitline[1]))
                else:
                    logmsg.info("\tServer {} is not the authorative MVIP.".format(splitline[1]))
                cmd = ("/usr/sbin/ntpdate -q {}".format(splitline[1]))
                try:
                    response = os.popen(cmd).read()
                    splitresponse = response.split(',')
                    offset = splitresponse[2].split(' ')
                    if "0." not in offset[2]:
                        logmsg.info("\t\tTime sync offset is greater than 1: {}\n\tSee document: {}".format(offset,time_doc))
                    else:
                        logmsg.info("\t\tSync offset is less than 1: {}".format(offset))
                except OSError as exception:
                    logmsg.debug(exception)
                    logmsg.debug(response.text)
                    response = ("ERROR: {} Failed".format(cmd))
        
    def mnode_about(repo):
        about(repo)
        logmsg.info("\nmNode about:\n {}".format(repo.ABOUT))

    def display_swarm_net():
        logmsg.info("\nContainer swarm network. Ensure IP's do not overlapp with existing network\nhttps://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_mNode's_Docker_swarm_network_deploys_on_the_same_subnet_as_the_underlying_management_%2F%2F_infrastructure_network")
        containers = DockerInfo.get_containers()
        for container in containers:
            container_ip = DockerInfo.docker_container_net(container.split(' ')[0])
            logmsg.info("\tContainer {:<33}: {:<20}".format(container.split(' ')[1].rstrip('\n'), container_ip))

    def docker_log():
        logmsg.info("\nParsing /var/log/docker.info")
        docker_errors = DockerInfo.parse_docker_log()
        if docker_errors[0] > 0:
            print("\t{} docker errors".format(str(docker_errors[0])))
        if docker_errors[1] > 0:
            print("\t{} Persistent volume fatal errors".format(str(docker_errors[1])))
            print("\tCheck the volume access and status. Ensure mnode has connectivty to the cluster SVIP.")
        if len(docker_errors[2]) > 0:
            for pvfatalmsg in docker_errors[2]:
                print("\t{}".format(pvfatalmsg))
    
    def trident_log():
        logmsg.info("\nParsing /var/log/trident/netapp.log")
        trident_errors = DockerInfo.parse_trident_log()
        if trident_errors > 0:
            logmsg.info("{} Errors found for persistent volumes in trident log".format(trident_errors))

    def service_logs(repo):
        services = Services.get_services(repo)
        logmsg.info("\nParsing logs for {} services.".format(str(len(services))))
        for service in services:
            log = Services.get_service_log(repo, service['name'])
            errors = Services.parse_service_log(repo, log)
            if len(errors) > 0:
                logmsg.info("Errors found in {} log".format(service['name']))
                for error in errors:
                    logmsg.info(error)

    def sf_prefrence(repo):
        url = ("https://{}/json-rpc/12.0?method=ListClusterInterfacePreferences".format(repo.INVENTORY_AUTHORATIVE_CLUSTER))
        logmsg.info("\nChecking cluster ListClusterInterfacePreferences")
        try:
            response = requests.get(url,auth=(repo.STORAGE_USER, repo.STORAGE_PASSWD), data={}, verify=False)
            if response.status_code == 200:
                outputjson = json.loads(response.text)
                if outputjson['result']['preferences'][0]['name']:
                    logmsg.info("\t{}: {}".format(outputjson['result']['preferences'][0]['name'], outputjson['result']['preferences'][0]['value']))
                else:
                    logmsg.info('No mnode Interface Preference found')
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

    def sf_const(repo):
        constants = {
            "cAuthContainerMaxNotReadyTime":"00:00:10.000000", 
            "cAuthContainerMaxUnknownTime":"00:00:10.000000",
            "cAuthFailureEventFrequencyThreshold":"60",
            "cEnableAuthContainerMonitor":"true",
            "cElementAuthPort":"5555",
            "cEnableAuthContainerMonitor":"true",
            "cMaxAuthConfigurationDBSize":"1048576",
            "laAuthContainer":"5",
            "lcAuthContainer": "0"
        }

        url = ("https://{}/json-rpc/12.0?method=GetConstants".format(repo.INVENTORY_AUTHORATIVE_CLUSTER))
        logmsg.info("\nChecking cluster Constants")
        try:
            response = requests.get(url,auth=(repo.STORAGE_USER, repo.STORAGE_PASSWD), data={}, verify=False)
            if response.status_code == 200:
                outputjson = json.loads(response.text)
                for line in outputjson['result']:
                    for constant in constants:
                        if line == constant:
                            logmsg.info("\t{:<40} default: {:<20} Current: {:<20}".format(constant, constants[constant],outputjson['result'][line]))
            else:
                logmsg.info("Failed return {} See /var/log/mnode-support-util.log for details".format(response.status_code))
                logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text)