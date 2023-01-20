import os
import requests
import tarfile
from get_token import get_token
from mnode import about
from log_setup import Logging

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

class UpdateMS():
    def __init__(self, repo):
        if not repo.ABOUT:
            about(repo)
        current_version = repo.ABOUT['mnode_bundle_version']
        logmsg.info("Current mnode version: {}".format(current_version))
     
    def sideload(repo):
        bundle_dir = "/sf/etc/mnode/bundle/"
        copy_cmd = ("cp {} {}".format(repo.UPDATEFILE,bundle_dir))
        new_bundle = (bundle_dir + os.path.basename(repo.UPDATEFILE))
        services_deploy = ("{}services_deploy_bundle.tar.gz".format(bundle_dir))
        if not os.path.isdir(bundle_dir): 
            os.makedirs(bundle_dir)
        logmsg.info("Copying {} to /sf/etc/mnode/bundle/".format(repo.UPDATEFILE))
        if os.path.isfile(repo.UPDATEFILE):
            os.popen(copy_cmd).read()
            logmsg.info("Extracting {}".format(new_bundle))
            try:
                bundle = tarfile.open(new_bundle) 
                bundle.extractall(path="/sf/etc/mnode/bundle/")
                bundle.close()
            except EOFError:
                logmsg.info("Could not extract archive. Possble corrupt file")
            logmsg.info("Extracting {}".format(services_deploy))
            bundle = tarfile.open(services_deploy)
            bundle.extractall(path="/sf/etc/mnode/bundle/")
            bundle.close()
        else:
            logmsg.debug("File not found: {}".format(repo.UPDATEFILE))
            logmsg.info("{} File not found. Try specifying full path".format(repo.UPDATEFILE))
            exit(1)
 
    def deploy(repo):
        get_token(repo)
        url = ('{}/mnode/1/services/deploy'.format(repo.URL))
        try:
            logmsg.info("Deploying new MS packages and services. Please wait....")
            logmsg.debug("Sending PUT {}".format(url))
            response = requests.put(url, headers=repo.HEADER_WRITE, verify=False)
            logmsg.debug(response.text)
        except requests.exceptions.RequestException as exception:
            logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug(response.text) 

