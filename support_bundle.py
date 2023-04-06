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
from system import System

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

    #============================================================
    # Get mnode about                
        filename = ("{}support-mnode-about.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode about")
                about(repo)
                json.dump(repo.ABOUT, outfile)
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))
    #============================================================
    # MNODE SETTINGS
        filename = ("{}support-mnode-settings.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode settings")
                Settings.get_settings(repo)
                json.dump(repo.SETTINGS, outfile)
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    ## GET AUTH TOKEN
        filename = ("{}support-auth-token".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Checking for valid auth token")
                get_token(repo)
                outfile.write("Auth token: ")
                outfile.write(repo.TOKEN)
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    ## GET CLUSTER AUTH CONFIG
        filename = ("{}support-auth-configuration".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:             
                logmsg.info("Get auth configuration")  
                Clusters.check_auth_config(repo)
                outfile.write("Auth client configuration")
                outfile.write(json.dumps(repo.AUTH_CONFIG))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    ## GET AUTH CLUSTER
        filename = ("{}support-auth-cluster".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get authorative cluster...")
                outfile.write("\nAuthorative Cluster: ")
                outfile.write(repo.INVENTORY_AUTHORATIVE_CLUSTER)
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get assets
        filename = ("{}support-get-assets.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get current assets...")
                AssetMgmt.get_current_assets(repo)
                outfile.write(json.dumps(repo.CURRENT_ASSET_JSON))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get inventory
        filename = ("{}support-get-inventory.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get inventory (This may take a while)...")
                Inventory.get_inventory(args, repo)
                outfile.write(json.dumps(repo.inventory_get))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get services    
        filename = ("{}support-get-services.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get services...")
                Services.get_services(repo)
                outfile.write(json.dumps(repo.SERVICE_LIST))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get clusters
        filename = ("{}support-get-clusters.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get clusters...")
                Clusters.get_clusters(repo)
                outfile.write(json.dumps(repo.CLUSTERS))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Check auth container
        '''
        remove - no longer functions in 12.3.1+
        filename = ("{}support-check-auth-container.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check auth container...")
                Clusters.check_auth_container(repo)
                outfile.write(json.dumps(repo.CHECK_AUTH))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))
        '''
    #============================================================
    # Check compute upgrade logs
        filename = ("{}support-check-compute-upgrade.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check compute firmware upgrade...")
                Inventory.get_compute_upgrades(args, repo)
                outfile.write(json.dumps(repo.COMPUTE_UPGRADE))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Check storage upgrade logs
        filename = ("{}support-check-storage-upgrade.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check storage upgrade...")
                Inventory.get_storage_upgrades(args, repo)
                outfile.write(json.dumps(repo.STORAGE_UPGRADE))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))
        Clusters.get_upgrade_log(repo)

    #============================================================
    # Get storage cluster details
        logmsg.info("Get storage cluster(s) details (This may take a while)...")
        Clusters.get_storage_info(repo)

    #============================================================
    # Storage healthcheck
        filename = ("{}support-health-check.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get health checks...")
                Clusters.get_health_check(repo)
                outfile.write(json.dumps(repo.HEALTH_CHECK))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get storage healthcheck logs
        logmsg.info("Get health check logs (This may take a while)...")
        Clusters.get_health_check_logs(repo)
        
    #============================================================
    # Get BMC info
        filename = ("{}support-hardware.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get hardware...")
                Hardware.get_hardware(args, repo)
                outfile.write(json.dumps(repo.HARDWARE))
                
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))    

        logmsg.info("Get hardware logs...")
        Hardware.get_hardware_logs(args, repo)

    #============================================================
    # Get docker ps
        filename = ("{}support-docker-ps".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker ps... ")
                docker_ps = DockerInfo.docker_ps()
                outfile.write("\nDocker ps: ")
                outfile.writelines(docker_ps)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get docker inspect
        filename = ("{}support-docker-inspect.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker inspect... ")
                containers = DockerInfo.get_containers()
                for container in containers:    
                    out = DockerInfo.docker_inspect(container.split(' ')[0])
                    outfile.write(json.dumps(out))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get docker services
        filename = ("{}support-docker-service".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker services... ")
                services = DockerInfo.docker_service()
                outfile.write("\nDocker services: ")
                outfile.writelines(services)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get docker stats
        filename = ("{}support-docker-stats".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker stats... ")
                docker_stats = DockerInfo.docker_stats()
                outfile.write("\nDocker stats: ")
                outfile.writelines(docker_stats)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get docker volumes
        filename = ("{}support-docker-vols".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker volumes...")
                volume_stats = DockerInfo.docker_volume()
                outfile.write("\nDocker volumes: ")
                outfile.writelines(volume_stats)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get docker logs
        services = Services.get_services(repo)
        for service in services:
            log = Services.get_service_log(repo, service['name'])
            filename = ("{}support-service-{}.log".format(repo.SUPPORT_DIR,service['name']))
            try:
                with open(filename, 'w') as outfile:
                    outfile.writelines(log)
            except FileNotFoundError:
                logmsg.info("Could not open {}".format(filename))

    #============================================================
    # Get docker network
        filename = ("{}support-docker-network".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker network...")
                docker_network = DockerInfo.docker_network()
                outfile.write("\nDocker network")
                outfile.writelines(docker_network)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        logmsg.info("Checking BMC ports...")
        System.bmc_ports(repo)
        
        logmsg.info("Get system info...")
        System.sys_info(repo)

        logmsg.info("Get config files...")
        System.local_files(repo)

        System.create_tar()