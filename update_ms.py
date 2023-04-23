import os
import requests
import tarfile
from get_token import get_token
from api_mnode import about
from log_setup import Logging, MLog
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

# =====================================================================
# Update management services
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

class UpdateMS():
    def __init__(self, repo):
        current_version = repo.ABOUT['mnode_bundle_version']
        logmsg.info("Current mnode version: {}".format(current_version))
    
    #============================================================
    # Copy the bundle into place and extract
    def sideload(repo, updatefile):
        bundle_dir = "/sf/etc/mnode/bundle/"
        copy_cmd = ("cp {} {}".format(updatefile,bundle_dir))
        new_bundle = (bundle_dir + os.path.basename(updatefile))
        services_tar = ("{}services_deploy_bundle.tar.gz".format(bundle_dir))
        if not os.path.isdir(bundle_dir): 
            os.makedirs(bundle_dir)
        logmsg.info("Copying {} to /sf/etc/mnode/bundle/".format(updatefile))
        if os.path.isfile(updatefile):
            os.popen(copy_cmd).read()
            logmsg.info("Extracting {}".format(new_bundle))
            try:
                bundle = tarfile.open(new_bundle) 
                bundle.extractall(path="/sf/etc/mnode/bundle/")
                bundle.close()
            except EOFError as error:
                MLog.log_exception(error)
            try:
                bundle = tarfile.open(services_tar)
                bundle.extractall(path="/sf/etc/mnode/bundle/")
                bundle.close()
            except OSError as error:
                MLog.log_exception(error)
        else:
            logmsg.info("{} File not found. Try specifying full path".format(updatefile))
            exit(1)

    #============================================================
    # deploy the package
    def deploy(repo):
        get_token(repo)
        url = ('{}/mnode/1/services/deploy'.format(repo.BASE_URL)) 
        logmsg.info("Deploying new MS packages and services. Please wait....")
        json_return = PDApi.send_put_return_json_nopayload(repo, url)
        if json_return:
            logmsg.debug("{}".format(json_return['message'])) 
        

