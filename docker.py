import os
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
    def __init__(self, repo):
        repo.CONTAINER_LIST = os.popen("/usr/bin/docker ps | /bin/grep -v CONTAINER | /usr/bin/awk '{print $1}'").readlines()

    def docker_ps(repo):
        try:
            logmsg.debug("Executing docker ps")
            repo.DOCKER_PS = os.popen("/usr/bin/docker ps").readlines()
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
    
    def docker_container_net(repo):
        logmsg.info("\nContainer IP's. Ensure they do not overlap with an existing network")
        containers = len(repo.DOCKER_INSPECT)
        ip_addr = []
        num = 0
        while num < containers:
            # In this case .format will produce literal output rather than the desired docker formatted output
            #cmd = ("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' {}".format(repo.CONTAINER_LIST[num]))
            cmd = ("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + repo.CONTAINER_LIST[num])
            try: 
                response = os.popen(cmd).read()
                ip_addr.append(response.rstrip('\n'))
                num += 1
            except OSError as error:
                logmsg.info("ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details.")
                logmsg.debug(error)
        logmsg.info(ip_addr)
