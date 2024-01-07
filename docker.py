import subprocess
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
            cmd_output = subprocess.getoutput("/usr/bin/docker ps -q").splitlines()
            return cmd_output
        except OSError as exception:
            logmsg.info("ERROR running docker ps. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(exception)

    def docker_ps(repo):
        """ docker ps
        """
        try:
            logmsg.debug("Executing docker ps")
            cmd_output = subprocess.getoutput("/usr/bin/docker ps").splitlines()
            return cmd_output
        except OSError as error:
            logmsg.info("ERROR: docker ps Failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)

    def docker_container_inspect(repo, container_list):
        """ docker inspect 
        """
        cmd_output = []
        for container in container_list:
            try:
                #inspect = subprocess.run(['docker', 'inspect', container.strip("\n")], stdout=subprocess.PIPE)
                inspect = subprocess.getoutput(f'docker inspect {container}')
                output = inspect.replace("\n", "")
                cmd_output.append(output)
            except OSError as error:
                logmsg.info("ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details.")
                logmsg.debug(error)
        return cmd_output

    def docker_service(repo):
        """ docker service list
        """
        try:
            cmd_output = subprocess.getoutput("/usr/bin/docker service list").splitlines()
            return cmd_output
        except OSError as error: 
            logmsg.info("ERROR: docker service list failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)

    def docker_volume(repo):
        """ docker volume list
        """
        try:
            cmd_output = subprocess.getoutput("/usr/bin/docker volume list").splitlines()
            return cmd_output
        except OSError as error:
            logmsg.info("ERROR: docker volume list failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)

    def docker_stats(repo):
        """ docker stats
        """
        try:
            cmd_output = subprocess.getoutput("/usr/bin/docker stats --all --no-stream").splitlines()
            return cmd_output
        except OSError as error:
            logmsg.info("ERROR: docker volume list failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)
    
    def docker_network(repo):
        """ docker network list
        """
        try:
            cmd_output = subprocess.getoutput("/usr/bin/docker network ls").splitlines()
            return cmd_output
        except OSError as error:
            logmsg.info("ERROR: docker network ls failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)
    
    def docker_network_inspect(repo):
        """ docker network inspect
        """
        network_inspect = []
        try:
            cmd_output = subprocess.getoutput("/usr/bin/docker network ls -q").splitlines()
            for network in cmd_output:
                inspect = subprocess.getoutput(f'/usr/bin/docker network inspect {network}')
                network_inspect.append(f'{inspect}\n\n')
            return network_inspect
        except OSError as error:
            logmsg.info("ERROR: docker network ls failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)
        
    def docker_container_net(container):
        """ get dontainer IP's
        """
        #kb = "https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_mNode's_Docker_swarm_network_deploys_on_the_same_subnet_as_the_underlying_management_%2F%2F_infrastructure_network"
        cmd = ("docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' " + container)
        try: 
            cmd_output = subprocess.getoutput(cmd).read()
            return cmd_output.rstrip('\n')
        except OSError as error:
            logmsg.info("ERROR: docker inspect failed. See /var/log/mnode-support-util.log for details.")
            logmsg.debug(error)

