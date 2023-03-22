import os
import re
from log_setup import Logging

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
# no docker module on the mnode :(
#import docker

class DockerInfo():
    def get_containers():
        try:
            container_list = os.popen("/usr/bin/docker ps | /bin/grep -v CONTAINER | /usr/bin/awk '{print $1,$2}'").readlines()
            return container_list
        except OSError as exception:
            logmsg.info("Error running docker ps. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(exception)

    def docker_ps(repo):
        try:
            logmsg.debug("Executing docker ps")
            repo.DOCKER_PS = os.popen("/usr/bin/docker ps").readlines()
            return repo.DOCKER_PS
        except OSError as error:
            repo.DOCKER_PS = "ERROR: docker ps Failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)

    def docker_inspect(repo):
        for container in repo.CONTAINER_LIST:
            try:
                response = os.popen("/usr/bin/docker inspect {}".format(container)).readlines()
                repo.DOCKER_INSPECT.append(response)
            except OSError as error:
                repo.DOCKER_INSPECT = "ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details."
                logmsg.debug(error)

    def docker_service(repo):
        try:
            repo.DOCKER_SERVICE = os.popen("/usr/bin/docker service list").readlines()
        except OSError as error: 
            repo.DOCKER_SERVICE = "ERROR: docker service list failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)

    def docker_volume(repo):
        try:
            repo.DOCKER_VOLUME = os.popen("/usr/bin/docker volume list").readlines()
        except OSError as error: 
            repo.DOCKER_VOLUME = "ERROR: docker volume list failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)

    def docker_stats(repo):
        try:
            repo.DOCKER_STATS = os.popen("/usr/bin/docker stats --all --no-stream").readlines()
        except OSError as error: 
            repo.DOCKER_STATS = "ERROR: docker volume list failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
    
    def docker_network(repo):
        try:
            repo.DOCKER_NETWORK = os.popen("/usr/bin/docker network ls").readlines()
        except OSError as error: 
            repo.DOCKER_STATS = "ERROR: docker network ls failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
    
    def docker_container_net(container):
        #kb = "https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_mNode's_Docker_swarm_network_deploys_on_the_same_subnet_as_the_underlying_management_%2F%2F_infrastructure_network"
        cmd = ("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + container)
        try: 
            response = os.popen(cmd).read()
        except OSError as error:
            logmsg.info("ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)
        return response.rstrip('\n')

    #============================================================
    # parse the docker log for errors
    def parse_docker_log():
        dockerlog = "/var/log/docker.info"
        count = 0
        fatalcount = 0
        fatalmsg = []
        loglines = []
        ignoreerrors = [
            "error reading the kernel parameter",
            "pulling image failed",
            "failed to remove node",
            "failed to delete container from containerd",
            "task: non-zero exit",
            "failed to remove node",
            "remove task failed",
            "No such container"
        ]
        pvfatal = 'error="VolumeDriver.Mount: error attaching volume'
        try:
            with open(dockerlog,"r") as logfile:
                loglines = logfile.readlines()
                for line in loglines:
                    if "level=error" in line:
                        x = 0
                        for ignore in ignoreerrors:
                            if ignore not in line:
                                x += 1
                        if x == len(ignoreerrors):
                            if pvfatal in line:
                                splitline = re.split('=|,',line)
                                fatalcount += 1
                                if splitline[4] not in fatalmsg:
                                    fatalmsg.append(splitline[4])
                            count += 1
        except FileNotFoundError:
            print("Cannot open {}".format(dockerlog))
        return(count, fatalcount, fatalmsg)

    #============================================================
    # parse the trident log for errors
    def parse_trident_log():
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
            print("Cannot open {}".format(tridentlog))
        return(count)
