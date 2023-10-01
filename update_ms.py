import os
import tarfile
from get_token import GetToken
#from api_mnode import about
from log_setup import Logging, MLog
from program_data import PDApi
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

# set up logging
logmsg = Logging.logmsg()

class UpdateMS():
    def __init__(self, repo):
        current_version = repo.about["mnode_bundle_version"]
        logmsg.info(f'Current mnode version: {current_version}')

    def sideload(repo, updatefile):
        """ Copy the bundle into place and extract
        """
        bundle_dir = "/sf/etc/mnode/bundle/"
        copy_cmd = f'cp {updatefile} {bundle_dir}'
        new_bundle = (bundle_dir + os.path.basename(updatefile))
        services_tar = f'{bundle_dir}services_deploy_bundle.tar.gz'
        if not os.path.isdir(bundle_dir): 
            os.makedirs(bundle_dir)
        logmsg.info(f'Copying {updatefile} to /sf/etc/mnode/bundle/')
        if os.path.isfile(updatefile):
            os.popen(copy_cmd).read()
            logmsg.info(f'Extracting {new_bundle}')
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
            logmsg.info(f'{updatefile} File not found. Try specifying full path')
            exit(1)

    def deploy(repo):
        """ deploy the package
        """
        ##token = GetToken(repo)
        url = f'{repo.base_url}/mnode/1/services/deploy'
        logmsg.info("Deploying new MS packages and services. Please wait....")
        json_return = PDApi.send_put_return_json_nopayload(repo, url)
        if json_return:
            logmsg.debug(f'{json_return["message"]}')
        else:
            logmsg.info("Monitor progress with docker ps.")
        

