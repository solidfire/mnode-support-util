import os
import socket
import tarfile
from datetime import datetime
from log_setup import Logging
from mnode import AssetMgmt

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE
# mnode support utility
#
# =====================================================================
#============================================================
# Gather mnode system info
#============================================================

class SysInfo():
    def __init__(self, repo):
        try:
            logmsg.info("Cleaning up {}".format(repo.SUPPORT_DIR))
            for f in os.listdir(repo.SUPPORT_DIR):
                os.remove(os.path.join(repo.SUPPORT_DIR, f))
        except OSError as exception:
            logmsg.debug(exception)

    def sys_info(repo):
        commands = ["/usr/bin/free -h", "/bin/df -h", "/bin/cat /etc/lsb-release", "/bin/ifconfig", "/bin/netstat -an", "/usr/bin/ntpq -p", ("/usr/sbin/ntpdate -q " + repo.INVENTORY_AUTHORATIVE_CLUSTER), "/bin/lsblk"]
        servers = ["monitoring.solidfire.com", "repo.solidfire.com", "sfsupport.solidfire.com"]
        filename = ("{}support-system-commands".format(repo.SUPPORT_DIR))
        with open(filename, "w") as output_file:
            for cmd in commands:
                logmsg.info("Running {}".format(cmd))
                try:
                    response = os.popen(cmd).read()
                except OSError as exception:
                    logmsg.debug(exception)
                    response = ("ERROR: {} Failed".format(cmd))
                output_file.write("\n#------ {}\n".format(cmd))
                output_file.write(response)

            for server in servers:
                logmsg.info("nslookup {}".format(server))
                try:
                    response = socket.gethostbyname(server)
                except:
                    response = ("ERROR: nslookup {}".format(server))
                output_file.write("\n{} {} ".format(server, str(response)))

    def bmc_ports(repo):
        filename = ("{}support-portscan".format(repo.SUPPORT_DIR))
        with open(filename, "w") as output_file:
            if not repo.CURRENT_ASSET_JSON:
                AssetMgmt.get_current_assets(repo)

            for bmc in repo.CURRENT_ASSET_JSON[0]['hardware']:
                port_check_139 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_check_139.settimeout(5.0)
                port_139 = (bmc['ip'],139)
                port_443 = (bmc['ip'],443)
                
                logmsg.info('Checking {}'.format(str(port_139)))
                response_139 = port_check_139.connect_ex(port_139)
                port_check_139.close()
                
                if response_139 == 0:
                    output_file.write("\nPort 139 scan succeeded for {}".format(bmc['ip']))
                elif response_139 == 111:
                    output_file.write("\nPort 139 scan failed for {}".format(bmc['ip']))
                    output_file.write("\nReturn code {} Connection refused".format(str(response_139)))
                else:
                    output_file.write("\nPort 139 scan failed for {}".format(bmc['ip']))
                    output_file.write("\nReturn code {}".format(str(response_139)))

                port_check_443 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_check_443.settimeout(5.0)
                logmsg.info('Checking {}'.format(str(port_443)))
                response_443 = port_check_443.connect_ex(port_443)
                port_check_443.close()

                if response_443 == 0:
                    output_file.write("\nPort 443 scan succeeded for {}".format(bmc['ip']))
                elif response_443 == 111:
                    output_file.write("\nPort 443 scan failed for {}".format(bmc['ip']))
                    output_file.write("\nReturn code {} Connection refused".format(str(response_139)))
                else:
                    output_file.write("\nPort 443 scan failed for {}".format(bmc['ip']))
                    output_file.write("\nReturn code {}".format(str(response_139)))

    def local_files(repo):
        files = ["/etc/solidfire.json", "/etc/hosts", "/etc/resolv.conf", "/etc/lsb-release", "/etc/ntp.conf"]
        with open("{}support-system-files".format(str(repo.SUPPORT_DIR)), "w") as output_file:
            for file in files:
                if os.path.isfile(file):
                    with open(file, "r") as read_file:
                        output_file.write("\n#----- {}\n".format(file))
                        output_file.write(read_file.read())
                    
    def create_tar():
        #============================================================
        # NOT needed when intigrated with HCC or :442 log collection
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
