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
        #    logmsg.info("Cleaning up {}".format(repo.SUPPORT_DIR))
        #    for f in os.listdir(repo.SUPPORT_DIR):
        #        os.remove(os.path.join(repo.SUPPORT_DIR, f))
        #except OSError as exception:
        #    logmsg.debug(exception)

        # =====================================================================
        # mnode about
        filename = ("{}support-mnode-about.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode about")
                about(repo)
                outfile.write(json.dumps(repo.ABOUT))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # mnode settings
        filename = ("{}support-mnode-settings.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Get mnode settings")
                json_return = Settings.get_settings(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get auth token
        filename = ("{}support-auth-token".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:               
                logmsg.info("Checking for valid auth token")
                get_token(repo)
                outfile.write("Auth token: {}".format(repo.TOKEN))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get cluster auth config
        filename = ("{}support-auth-configuration".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:             
                logmsg.info("Get auth configuration")  
                json_return = mNodeHealthCheck.check_auth_config(repo, outfile)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get auth cluster
        filename = ("{}support-auth-cluster".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get authorative cluster...")
                outfile.write("\nAuthorative Cluster: {}".format(repo.AUTH_MVIP))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get assets
        filename = ("{}support-get-assets.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get current assets...")
                outfile.write(json.dumps(repo.ASSETS))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get inventory
        filename = ("{}support-get-inventory.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get inventory. This may take a while...")
                json_return = Inventory.refresh_inventory(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get services
        filename = ("{}support-get-services.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get services...")
                json_return = Services.get_services(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get clusters
        filename = ("{}support-get-clusters.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get clusters...")
                json_return = Clusters.get_clusters(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # check for previous compute fw upgrade
        filename = ("{}support-check-compute-upgrade.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Check compute firmware upgrade...")
                json_return = Inventory.get_compute_upgrades(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # check for previous storage upgrade
        checkfile = ("{}support-check-storage-upgrade.json".format(repo.SUPPORT_DIR))
        cutlog = []
        try:
            with open(checkfile, 'w') as outfile:
                logmsg.info("Check storage upgrades... This may take a while.")
                json_return = Upgrades.get_upgrade(repo, active='true')
                if json_return:
                    logmsg.info("\tUpgrade(s) found...")
                    outfile.write(json.dumps(json_return))
                    for upgrade in json_return:
                        logmsg.info("\tWriting log file for upgrade {}".format(upgrade["upgradeId"]))
                        logfile = ("{}support-storage-upgrade-{}.log".format(repo.SUPPORT_DIR, upgrade["upgradeId"]))
                        with open(logfile, 'a') as logf:
                            url = ("{}/storage/1/upgrades/{}/log".format(repo.BASE_URL,upgrade['upgradeId']))
                            json_return = PDApi.send_get_return_json(repo, url, debug=False) ## Often fails with RangeError: Maximum call stack exceeded
                            if json_return:
                                for line in json_return['mnode_storage']['docker_logs']:
                                    # strip out the over verbosity
                                    if "vars in" not in line:
                                        print(line, file = logf)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get previous storage healthcheck
        filename = ("{}support-storagehealth-check.json".format(repo.SUPPORT_DIR))
        log = []
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get health checks...")
                json_return = Healthcheck.get_healthcheck(repo)
                if json_return:
                    for health_check in json_return:
                        log.append(Healthcheck.get_healthcheck_by_id(repo, health_check['healthCheckId']))
                outfile.writelines(log)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get bmc info
        filename = ("{}support-hardware.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get hardware...")
                json_return = Hardware.get_hardware(repo)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))    

        # =====================================================================
        # get bmc logs
        filename = ("{}support-hardware-logs.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'a') as outfile:
                for hardware in repo.ASSETS[0]['hardware']:
                    hardware_id = hardware['id']
                    url = ('{}/hardware/2/nodes/{}/bmc-logs'.format(repo.BASE_URL,hardware_id))
                    text = PDApi.send_get_return_text(repo, url)
                    if text:
                        outfile.write(text)
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))   

        # =====================================================================
        # get docker ps
        filename = ("{}support-docker-ps".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker ps... ")
                cmd_return = Docker.docker_ps(repo)
                out = "\n".join(cmd_return)
                outfile.write("\nDocker ps: \n{}".format(out))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get docker inspect
        filename = ("{}support-docker-inspect.json".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker inspect... ")
                container_list = Docker.get_containers()
                json_return = Docker.docker_inspect(repo, container_list)
                if json_return:
                    outfile.write(json.dumps(json_return))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get docker service list
        filename = ("{}support-docker-service".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker services... ")
                cmd_return = Docker.docker_service(repo)
                out = "\n".join(cmd_return)
                outfile.write("\nDocker service:\n{}".format(out))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get docker stats
        filename = ("{}support-docker-stats".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker stats... ")
                cmd_return = Docker.docker_stats(repo)
                out = "\n".join(cmd_return)
                outfile.write("\nDocker stats:\n{}".format(out))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get docker volume list
        filename = ("{}support-docker-vols".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker volumes...")
                cmd_return = Docker.docker_volume(repo)
                out = "\n".join(cmd_return)
                outfile.write("\nDocker volumes:\n{}".format(out))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        #============================================================
        # Get docker logs
        logmsg.info("Get service logs...")
        services = Services.get_services(repo)
        for service in services:
            log = Services.get_service_log(repo, service['name'], False)
            filename = ("{}support-service-{}.log".format(repo.SUPPORT_DIR,service['name']))
            try:
                with open(filename, 'a') as outfile:
                    for line in log:
                        outfile.write("{}\n".format(line))
            except FileNotFoundError:
                logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        # get docker network
        filename = ("{}support-docker-network".format(repo.SUPPORT_DIR))
        try:
            with open(filename, 'w') as outfile:
                logmsg.info("Get docker network...")
                cmd_return = Docker.docker_network(repo)
                out = "\n".join(cmd_return)
                outfile.write("\nDocker network\n{}".format(out))
        except FileNotFoundError:
            logmsg.info("Could not open {}".format(filename))

        # =====================================================================
        #system_cmds(repo):
        commands = ["/usr/bin/free -h", "/bin/df -h", "/bin/cat /etc/lsb-release", "/bin/ifconfig", "/bin/netstat -an", "/usr/bin/ntpq -p", ("/usr/sbin/ntpdate -q " + repo.AUTH_MVIP), "/bin/lsblk"]
        servers = ["monitoring.solidfire.com", "repo.solidfire.com", "sfsupport.solidfire.com"]
        filename = ("{}support-system-commands".format(repo.SUPPORT_DIR))
        with open(filename, "a") as outfile:
            for cmd in commands:
                logmsg.info("Running {}".format(cmd))
                try:
                    response = os.popen(cmd).read()
                except OSError as exception:
                    logmsg.debug(exception)
                    response = ("ERROR: {} Failed".format(cmd))
                outfile.write("\n#------ {}\n".format(cmd))
                outfile.write(response)

            for server in servers:
                print("nslookup {}".format(server), file=outfile)
                try:
                    response = socket.gethostbyname(server)
                except:
                    response = ("ERROR: nslookup {}".format(server))
                outfile.write("\n{} {} ".format(server, str(response)))

        # =====================================================================
        #bmc_ports(repo):
        filename = ("{}support-portscan".format(repo.SUPPORT_DIR))
        with open(filename, "a") as outfile:
            for bmc in repo.ASSETS[0]['hardware']:
                port_check_139 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_check_139.settimeout(5.0)
                port_139 = (bmc['ip'],139)
                port_443 = (bmc['ip'],443)
                
                outfile.write('Checking {}'.format(str(port_139)))
                response_139 = port_check_139.connect_ex(port_139)
                port_check_139.close()
                
                if response_139 == 0:
                    outfile.write("\nPort 139 scan succeeded for {}".format(bmc['ip']))
                elif response_139 == 111:
                    outfile.write("\nPort 139 scan failed for {}".format(bmc['ip']))
                    outfile.write("\nReturn code {} Connection refused".format(str(response_139)))
                else:
                    outfile.write("\nPort 139 scan failed for {}".format(bmc['ip']))
                    outfile.write("\nReturn code {}".format(str(response_139)))

                port_check_443 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_check_443.settimeout(5.0)
                outfile.write('Checking {}'.format(str(port_443)))
                response_443 = port_check_443.connect_ex(port_443)
                port_check_443.close()

                if response_443 == 0:
                    outfile.write("\nPort 443 scan succeeded for {}".format(bmc['ip']))
                elif response_443 == 111:
                    outfile.write("\nPort 443 scan failed for {}".format(bmc['ip']))
                    outfile.write("\nReturn code {} Connection refused".format(str(response_139)))
                else:
                    outfile.write("\nPort 443 scan failed for {}".format(bmc['ip']))
                    outfile.write("\nReturn code {}".format(str(response_139)))

        # =====================================================================
        #local_files
        filename = ("{}support-localfiles".format(repo.SUPPORT_DIR))
        files = ["/etc/solidfire.json", "/etc/hosts", "/etc/resolv.conf", "/etc/lsb-release", "/etc/ntp.conf"]
        with open(filename, "a") as outfile:
            for file in files:
                if os.path.isfile(file):
                    with open(file, "r") as read_file:
                        outfile.write("\n#----- {}\n".format(file))
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
                    #logmsg.info("Adding {} to bundle.".format(file))  <<<----- TOO CHATTY
                    bundle.add(os.path.join(root, file))
            logmsg.info("\nDone. Bundle name: {}".format(tar_file))
            bundle.close()
            logmsg.info("Please send {} to NetApp support".format(tar_file))
        except:
            logmsg.info("Failed to create tar bundle.")