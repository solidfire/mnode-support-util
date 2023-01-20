import json
import os
import requests
from docker import DockerInfo
from get_token import get_token
from hardware import Hardware
from inventory import Inventory
from log_setup import Logging
from mnode import AssetMgmt, get_logs, Services, Settings, about
from storage import Clusters
from system import SysInfo

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
class SupportBundle():
    def __init__(self, args, repo):

## MNODE ABOUT                
        filename = ("{}support-mnode-about.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode about")
                about(repo)
                json.dump(repo.ABOUT, outfile)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

## MNODE SETTINGS
        filename = ("{}support-mnode-settings.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode settings")
                Settings.get_settings(repo)
                json.dump(repo.SETTINGS, outfile)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

## GET AUTH TOKEN
        filename = ("{}support-auth-token".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Checking for valid auth token")
                get_token(repo)
                outfile.write("Auth token: ")
                outfile.write(repo.TOKEN)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

## GET CLUSTER AUTH CONFIG
        filename = ("{}support-auth-configuration".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:             
                logmsg.info("Get auth configuration...")  
                Clusters.check_auth_config(repo)
                outfile.write("Auth client configuration")
                outfile.write(json.dumps(repo.AUTH_CONFIG))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

## GET AUTH CLUSTER
        filename = ("{}support-auth-cluster".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get authorative cluster...")
                outfile.write("\nAuthorative Cluster: ")
                outfile.write(repo.INVENTORY_AUTHORATIVE_CLUSTER)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-get-assets.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get current assets...")
                AssetMgmt.get_current_assets(repo)
                outfile.write(json.dumps(repo.CURRENT_ASSET_JSON))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-get-inventory.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get inventory (This may take a while)...")
                Inventory.get_inventory(args, repo)
                outfile.write(json.dumps(repo.inventory_get))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-get-services.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get services...")
                Services.get_services(repo)
                outfile.write(json.dumps(repo.SERVICE_LIST))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-get-clusters.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get clusters...")
                Clusters.get_clusters(repo)
                outfile.write(json.dumps(repo.CLUSTERS))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        '''
        remove - no longer functions in 12.3.1+
        filename = ("{}support-check-auth-container.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check auth container...")
                Clusters.check_auth_container(repo)
                outfile.write(json.dumps(repo.CHECK_AUTH))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))
        '''

        filename = ("{}support-check-compute-upgrade.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check compute firmware upgrade...")
                Inventory.get_compute_upgrades(args, repo)
                outfile.write(json.dumps(repo.COMPUTE_UPGRADE))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-check-storage-upgrade.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check storage upgrade...")
                Inventory.get_storage_upgrades(args, repo)
                outfile.write(json.dumps(repo.STORAGE_UPGRADE))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        logmsg.info("Get storage cluster(s) details (This may take a while)...")
        Clusters.get_storage_info(repo)

        filename = ("{}support-health-check.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get health checks...")
                Clusters.get_health_check(repo)
                outfile.write(json.dumps(repo.HEALTH_CHECK))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        logmsg.info("Get health check logs (This may take a while)...")
        Clusters.get_health_check_logs(repo)
        
        filename = ("{}support-hardware.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get hardware...")
                Hardware.get_hardware(args, repo)
                outfile.write(json.dumps(repo.HARDWARE))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))    

        logmsg.info("Get hardware logs...")
        Hardware.get_hardware_logs(args, repo)

        filename = ("{}support-docker-ps".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker ps... ")
                DockerInfo.docker_ps(repo)
                out = "\n".join(repo.DOCKER_PS)
                outfile.write("\nDocker ps: ")
                outfile.write(out)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-docker-inspect.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker inspect... ")
                DockerInfo.docker_inspect(repo)
                outfile.write(json.dumps(repo.DOCKER_INSPECT))
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-docker-service".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker services... ")
                DockerInfo.docker_service(repo)
                out = "\n".join(repo.DOCKER_SERVICE)
                outfile.write("\nDocker service: ")
                outfile.write(out)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-docker-stats".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker stats... ")
                DockerInfo.docker_stats(repo)
                out = "\n".join(repo.DOCKER_STATS)
                outfile.write("\nDocker stats: ")
                outfile.write(out)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        filename = ("{}support-docker-vols".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker volumes...")
                DockerInfo.docker_volume(repo)
                out = "\n".join(repo.DOCKER_VOLUME)
                outfile.write("\nDocker volumes: ")
                outfile.write(out)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

###
        get_token(repo)
        url = ('{}/mnode/services?status=running&helper=false'.format(repo.URL))
        service_list = []
        try:
            logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if response.status_code == 200:
                service_list = json.loads(response.text)
                for service in service_list:
                    url = ('{}/mnode/logs?lines=1000&service-name={}&stopped=true'.format(repo.URL,service['name']))
                    try:
                        logmsg.info("Gathering {} logs".format(service['name']))
                        response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
                        if response.status_code == 200:
                            logmsg.debug("{} logs = {}".format(service, response.status_code))
                            filename = ("{}support-service-{}.log".format(repo.SUPPORT_DIR,service['name']))
                            try:
                                with open(filename, 'w') as outfile:
                                    outfile.write(response.text)
                                    outfile.close()
                            except FileNotFoundError:
                                logmsg.info("Could not open {}".format(filename))
                        else:
                            logmsg.debug("{} logs = {}".format(service, response.status_code))
                    except requests.exceptions.RequestException as exception:
                        logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                        logmsg.debug(exception)
                        logmsg.debug(response.text) 
            else:
                logmsg.debug("Failed to retrieve service list")
                logmsg.debug(response.status_code)
                logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 
###

        filename = ("{}support-docker-network".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker network...")
                DockerInfo.docker_network(repo)
                out = "\n".join(repo.DOCKER_NETWORK)
                outfile.write("\nDocker network")
                outfile.write(out)
                outfile.close()
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        logmsg.info("Checking BMC ports...")
        SysInfo.bmc_ports(repo)
        
        logmsg.info("Get system info...")
        SysInfo.sys_info(repo)

        logmsg.info("Get config files...")
        SysInfo.local_files(repo)

        SysInfo.create_tar()