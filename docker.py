import os
from log_setup import Logging

"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

# set up logging
logmsg = Logging.logmsg()

class Docker():
    def get_containers():
        """ get docker container id's from docker ps 
        """
        try:
            cmd_output = os.popen("/usr/bin/docker ps | /bin/grep -v CONTAINER | /usr/bin/awk '{print $1,$2}'").readlines()
        except OSError as exception:
            cmd_output = "Error running docker ps. See /var/log/mnode-support-util.log for details."
            logmsg.debug(exception)
        return cmd_output

    def docker_ps(repo):
        """ docker ps
        """
        try:
            logmsg.debug("Executing docker ps")
            cmd_output = os.popen("/usr/bin/docker ps").readlines()
        except OSError as error:
            cmd_output = "ERROR: docker ps Failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
        return cmd_output

    def docker_inspect(repo, container_list):
        """ docker inspect 
        """
        cmd_output = []
        for container in container_list:
            try:
                inspect = os.popen(f'/usr/bin/docker inspect {container}').readlines()
                cmd_output.append(inspect)
            except OSError as error:
                cmd_output = "ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details."
                logmsg.debug(error)
        return cmd_output

    def docker_service(repo):
        """ docker service list
        """
        try:
            cmd_output = os.popen("/usr/bin/docker service list").readlines()
        except OSError as error: 
            cmd_output = "ERROR: docker service list failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
        return cmd_output

    def docker_volume(repo):
        """ docker volume list
        """
        try:
            cmd_output = os.popen("/usr/bin/docker volume list").readlines()
        except OSError as error:
            cmd_output = "ERROR: docker volume list failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
        return cmd_output

    def docker_stats(repo):
        """ docker stats
        """
        try:
            cmd_output = os.popen("/usr/bin/docker stats --all --no-stream").readlines()
        except OSError as error:
            cmd_output = "ERROR: docker volume list failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
        return cmd_output
    
    def docker_network(repo):
        """ docker network list
        """
        try:
            cmd_output = os.popen("/usr/bin/docker network ls").readlines()
        except OSError as error:
            cmd_output = "ERROR: docker network ls failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
        return cmd_output
    
    def docker_container_net(container):
        """ get dontainer IP's
        """
        #kb = "https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_mNode's_Docker_swarm_network_deploys_on_the_same_subnet_as_the_underlying_management_%2F%2F_infrastructure_network"
        cmd = ("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + container)
        try: 
            cmd_output = os.popen(cmd).read()
        except OSError as error:
            cmd_output = "ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details."
            logmsg.debug(error)
        return cmd_output.rstrip('\n')

