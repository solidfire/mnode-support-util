#!/usr/bin/env python
import os
from mnode import about
from docker import DockerInfo
from get_token import get_token
from log_setup import Logging
from storage import Clusters

logmsg = Logging.logmsg()

class HealthCheck():
    def check_auth_token(repo):
        auth_kbs = ["https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/How_to_re-sync_auth_secrets_between_mNode_and_storage_cluster_running_element_auth",
            "https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/setup-mnode_script_or_Management_Services_update_fails_on_Element_mNode_12.2_with_configure_element_auth_error",
            "https://kb.netapp.com/Advice_and_Troubleshooting/Hybrid_Cloud_Infrastructure/NetApp_HCI/MissingTokenError_when_%22Attempting_to_retrieve_auth_token%22"]
        get_token(repo)
        logmsg.info("\nElement auth token:")
        logmsg.info(repo.TOKEN)
        #print(*auth_kbs, sep = '\n')

    # remove - no longer functions in 12.3.1+
    def checkauth_container(repo):
        container_kbs = ['https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_auth_container_alert_for_the_recently_added_node',
        'https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/The_SolidFire_Application_cannot_communicate_with_node_ID_X_due_to_element_auth_service_container_hung',
        'https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/authenticationServiceFault_alert_occurs_and_becomes_resolved_in_a_minute']
        #Clusters.check_auth_container(repo)
        logmsg.info("\nCluster auth container status:")
        logmsg.info(repo.CHECK_AUTH)
        #print(*container_kbs, sep = '\n')

    def checkauth_config(repo):
        logmsg.info("\nAuth client configuration")
        Clusters.check_auth_config(repo)
        
    def display_auth_mvip(repo):
        logmsg.info("\nAuthorative storage cluster: ")
        logmsg.info(repo.INVENTORY_AUTHORATIVE_CLUSTER)
    
    def check_time_sync(repo):
        time_kbs = ['https://docs.netapp.com/us-en/hci/docs/task_mnode_install.html#configure-time-sync',
            'https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/setup-mnode_script_on_mNode_failing_with_HTTP_500%3A_Error_adding_storage_asset']
        logmsg.info("\nCheck time sync")
        cmd = ("/usr/sbin/ntpdate -q {}".format(repo.INVENTORY_AUTHORATIVE_CLUSTER))
        try:
            response = os.popen(cmd).read()
            logmsg.info(response)
            #print(*time_kbs, sep = '\n')
        except OSError as exception:
            logmsg.debug(exception)
            logmsg.debug(response.text)
            response = ("ERROR: {} Failed".format(cmd))
        
    def mnode_about(repo):
        about(repo)
        logmsg.info("\nmNode about:\n {}".format(repo.ABOUT))

    def display_swarm_net(repo):
        swarm_net_kbs = ["https://kb.netapp.com/Advice_and_Troubleshooting/Data_Storage_Software/Element_Software/Element_mNode's_Docker_swarm_network_deploys_on_the_same_subnet_as_the_underlying_management_%2F%2F_infrastructure_network"]
        DockerInfo(repo)
        DockerInfo.docker_inspect(repo)
        DockerInfo.docker_container_net(repo)
        #print(*swarm_net_kbs, sep = '\n')

