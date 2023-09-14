import json
import os
import socket
import tarfile
from api_hardware import Hardware
from api_inventory import Inventory
from api_mnode import Assets, Services, Settings, about
from api_storage import Clusters, Healthcheck, Upgrades
from datetime import datetime
from docker import Docker
from get_token import get_token
from log_setup import Logging
from mnode_healthcheck import mNodeHealthCheck
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
# =====================================================================
# Gather mnode support bundle
# =====================================================================
logmsg = Logging.logmsg()

class SupportBundle():
    def __init__(self, repo):
        # =====================================================================
        # clean up any old logs
        #try:
        #    logmsg.info(f'Cleaning up {repo.SUPPORT_DIR}')
        #    for f in os.listdir(repo.SUPPORT_DIR):
        #        os.remove(os.path.join(repo.SUPPORT_DIR, f))
        #except OSError as exception:
        #    logmsg.debug(exception)

        # =====================================================================
        # mnode about
        filename = f'{repo.SUPPORT_DIR}support-mnode-about.json'
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode about")
                about(repo)
                outfile.write(json.dumps(repo.ABOUT))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # mnode settings
        filename = f'{repo.SUPPORT_DIR}support-mnode-settings.json'
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode settings")
                json_return = Settings.get_settings(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get auth token
        filename = f'{repo.SUPPORT_DIR}support-auth-token'
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Checking for valid auth token")
                get_token(repo)
                outfile.write(f'Auth token: {repo.TOKEN}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get cluster auth config
        filename = f'{repo.SUPPORT_DIR}support-auth-configuration'
        try:
            with open(filename, 'w') as outfile:             
                logmsg.info("Get auth configuration")  
                json_return = mNodeHealthCheck.check_auth_config(repo, outfile)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get auth cluster
        filename = f'{repo.SUPPORT_DIR}support-auth-cluster'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get authorative cluster...")
                outfile.write(f'\nAuthorative Cluster: {repo.AUTH_MVIP}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get assets
        filename = f'{repo.SUPPORT_DIR}support-get-assets.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get current assets...")
                outfile.write(json.dumps(repo.ASSETS))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get inventory
        filename = f'{repo.SUPPORT_DIR}support-get-inventory.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get inventory. This may take a while...")
                json_return = Inventory.refresh_inventory(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get services
        filename = f'{repo.SUPPORT_DIR}support-get-services.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get services...")
                json_return = Services.get_services(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get clusters
        filename = f'{repo.SUPPORT_DIR}support-get-clusters.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get clusters...")
                json_return = Clusters.get_clusters(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # check for previous compute fw upgrade
        filename = f'{repo.SUPPORT_DIR}support-check-compute-upgrade.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check compute firmware upgrade...")
                json_return = Inventory.get_compute_upgrades(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # check for previous storage upgrade
        checkfile = f'{repo.SUPPORT_DIR}support-check-storage-upgrade.json'
        cutlog = []
        try:
            with open(checkfile, 'w') as outfile:
                logmsg.info("Check storage upgrades... This may take a while.")
                json_return = Upgrades.get_upgrade(repo, active='true')
                if json_return:
                    logmsg.info("\tUpgrade(s) found...")
                    outfile.write(json.dumps(json_return))
                    for upgrade in json_return:
                        logmsg.info(f'\tWriting log file for upgrade {upgrade["upgradeId"]}')
                        logfile = (f'{repo.SUPPORT_DIR}support-storage-upgrade-{upgrade["upgradeId"]}.log')
                        with open(logfile, 'a') as logf:
                            url = f'{repo.BASE_URL}/storage/1/upgrades/{upgrade["upgradeId"]}/log'
                            json_return = PDApi.send_get_return_json(repo, url, debug=False) ## Often fails with RangeError: Maximum call stack exceeded
                            if json_return:
                                for line in json_return["mnode_storage"]["docker_logs"]:
                                    # strip out the over verbosity
                                    if "vars in" not in line:
                                        print(line, file = logf)
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get previous storage healthcheck
        filename = f'{repo.SUPPORT_DIR}support-storagehealth-check.json'
        log = []
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get health checks...")
                json_return = Healthcheck.get_healthcheck(repo)
                if json_return:
                    for health_check in json_return:
                        log.append(Healthcheck.get_healthcheck_by_id(repo, health_check["healthCheckId"]))
                outfile.writelines(log)
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get bmc info
        filename = f'{repo.SUPPORT_DIR}support-hardware.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get hardware...")
                json_return = Hardware.get_hardware(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')    

        # =====================================================================
        # get bmc logs
        filename = f'{repo.SUPPORT_DIR}support-hardware-logs.json'
        try:
            with open(filename, 'a') as outfile:
                for hardware in repo.ASSETS[0]["hardware"]:
                    hardware_id = hardware["id"]
                    url = f'{repo.BASE_URL}/hardware/2/nodes/{hardware_id}/bmc-logs'
                    text = PDApi.send_get_return_text(repo, url)
                    if text:
                        outfile.write(text)
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')   

        # =====================================================================
        # get docker ps
        filename = f'{repo.SUPPORT_DIR}support-docker-ps'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker ps... ")
                cmd_return = Docker.docker_ps(repo)
                out = "\n".join(cmd_return)
                outfile.write(f'\nDocker ps: \n{out}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get docker inspect
        filename = f'{repo.SUPPORT_DIR}support-docker-inspect.json'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker inspect... ")
                container_list = Docker.get_containers()
                json_return = Docker.docker_inspect(repo, container_list)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get docker service list
        filename = f'{repo.SUPPORT_DIR}support-docker-service'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker services... ")
                cmd_return = Docker.docker_service(repo)
                out = "\n".join(cmd_return)
                outfile.write(f'\nDocker service:\n{out}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get docker stats
        filename = f'{repo.SUPPORT_DIR}support-docker-stats'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker stats... ")
                cmd_return = Docker.docker_stats(repo)
                out = "\n".join(cmd_return)
                outfile.write(f'\nDocker stats:\n{out}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get docker volume list
        filename = f'{repo.SUPPORT_DIR}support-docker-vols'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker volumes...")
                cmd_return = Docker.docker_volume(repo)
                out = "\n".join(cmd_return)
                outfile.write(f'\nDocker volumes:\n{out}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        #============================================================
        # Get docker logs
        logmsg.info("Get service logs...")
        services = Services.get_services(repo)
        for service in services:
            log = Services.get_service_log(repo, service["name"], False)
            filename = f'{repo.SUPPORT_DIR}support-service-{service["name"]}.log'
            try:
                with open(filename, 'a') as outfile:
                    for line in log:
                        outfile.write(f'{line}\n')
            except FileNotFoundError:
                logmsg.info(f'Could not open {filename}')

        # =====================================================================
        # get docker network
        filename = f'{repo.SUPPORT_DIR}support-docker-network'
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker network...")
                cmd_return = Docker.docker_network(repo)
                out = "\n".join(cmd_return)
                outfile.write(f'\nDocker network\n{out}')
        except FileNotFoundError:
            logmsg.info(f'Could not open {filename}')

        # =====================================================================
        #system_cmds(repo):
        commands = ["/usr/bin/free -h", "/bin/df -h", "/bin/cat /etc/lsb-release", "/bin/ifconfig", "/bin/netstat -an", "/usr/bin/ntpq -p", ("/usr/sbin/ntpdate -q " + repo.AUTH_MVIP), "/bin/lsblk"]
        servers = ["monitoring.solidfire.com", "repo.solidfire.com", "sfsupport.solidfire.com"]
        filename = f'{repo.SUPPORT_DIR}support-system-commands'
        with open(filename, "a") as outfile:
            for cmd in commands:
                logmsg.info(f'Running {cmd}')
                try:
                    response = os.popen(cmd).read()
                except OSError as exception:
                    logmsg.debug(exception)
                    response = (f'ERROR: {cmd} Failed')
                outfile.write(f'\n#------ {cmd}\n')
                outfile.write(response)

            for server in servers:
                print(f'nslookup {server}', file=outfile)
                try:
                    response = socket.gethostbyname(server)
                except:
                    response = f'ERROR: nslookup {server}'
                outfile.write(f'\n{server} {str(response)} ')

        # =====================================================================
        #bmc_ports(repo):
        filename = f'{repo.SUPPORT_DIR}support-portscan'
        with open(filename, "a") as outfile:
            for bmc in repo.ASSETS[0]["hardware"]:
                port_check_139 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_check_139.settimeout(5.0)
                port_139 = (bmc["ip"],139)
                port_443 = (bmc["ip"],443)
                
                outfile.write(f'Checking {str(port_139)}')
                response_139 = port_check_139.connect_ex(port_139)
                port_check_139.close()
                
                if response_139 == 0:
                    outfile.write(f'\nPort 139 scan succeeded for {bmc["ip"]}')
                elif response_139 == 111:
                    outfile.write(f'\nPort 139 scan failed for {bmc["ip"]}')
                    outfile.write(f'\nReturn code {str(response_139)} Connection refused')
                else:
                    outfile.write(f'\nPort 139 scan failed for {bmc["ip"]}')
                    outfile.write(f'\nReturn code {str(response_139)}')

                port_check_443 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_check_443.settimeout(5.0)
                outfile.write(f'Checking {str(port_443)}')
                response_443 = port_check_443.connect_ex(port_443)
                port_check_443.close()

                if response_443 == 0:
                    outfile.write(f'\nPort 443 scan succeeded for {bmc["ip"]}')
                elif response_443 == 111:
                    outfile.write(f'\nPort 443 scan failed for {bmc["ip"]}')
                    outfile.write(f'\nReturn code {str(response_139)} Connection refused')
                else:
                    outfile.write(f'\nPort 443 scan failed for {bmc["ip"]}')
                    outfile.write(f'\nReturn code {str(response_139)}')

        # =====================================================================
        #local_files
        filename = f'{repo.SUPPORT_DIR}support-localfiles'
        files = ["/etc/solidfire.json", "/etc/hosts", "/etc/resolv.conf", "/etc/lsb-release", "/etc/ntp.conf"]
        with open(filename, "a") as outfile:
            for file in files:
                if os.path.isfile(file):
                    with open(file, "r") as read_file:
                        outfile.write(f'\n#----- {file}\n')
                        outfile.write(read_file.read())
                    
        # =====================================================================
        #create tar
        logmsg.info("Creating support tar bundle. Please wait....")
        date_time = datetime.now()
        time_stamp = date_time.strftime("%d-%b-%Y-%H.%M.%S")
        tar_file = ("/tmp/mnode-support-bundle-%s.tar" % time_stamp)
        try:
            bundle = tarfile.open(tar_file, "w:gz")
            for root, dirs, files in os.walk("/var/log"):
                for file in files:
                    bundle.add(os.path.join(root, file))
            logmsg.info(f'\nDone. Bundle name: {tar_file}')
            bundle.close()
            logmsg.info(f'Please send {tar_file} to NetApp support')
        except:
            logmsg.info("Failed to create tar bundle.")