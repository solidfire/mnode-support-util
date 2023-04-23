import json
import os
import requests
import urllib3
from get_token import get_token
from log_setup import Logging
from program_data import PDApi
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

# =====================================================================
# Package service api calls
# https://[mnodeip]/package-repository/1
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

#============================================================
# disable ssl warnings so the log doesn't fill up
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Package:
    #============================================================
    # List available packages
    def list_packages(repo):
        get_token(repo)
        url = ('{}/package-repository/1/packages/'.format(repo.BASE_URL))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    #============================================================
    # Delete a package
    def delete_package(repo, package_id):
        get_token(repo)
        url = ('{}/package-repository/1/packages/{}'.format(repo.BASE_URL,package_id))
        logmsg.debug("Sending DELETE {}".format(url))
        json_return = PDApi.send_delete_return_status(repo, url)
        if json_return:
            logmsg.info("{}: {}".format(json_return['version'],json_return['message']))

    #============================================================
    # upload a package
    # requires some special treatment with the api call. So it does not use PDApi.send_put
    def upload_element_image(repo, updatefile):
        get_token(repo)
        logmsg.info('Add upgrade image to package repository')
        if os.path.exists(updatefile) != True:
            logmsg.info("{} not found".format(updatefile))
            exit(1)
        header = {"Accept": "application/json", "Prefer": "respond-async", "Content-Type": "application/octet-stream", "Authorization":"Bearer {}".format(repo.TOKEN)}
        url = ('{}/package-repository/1/packages'.format(repo.BASE_URL))
        session = requests.Session() 
        with open(updatefile, 'rb') as f:
            try:
                logmsg.debug('Sending PUT {} {}'.format(url,updatefile))
                logmsg.info('Loading {} into the package repository. This will take a few minutes'.format(updatefile))
                response = session.post(url, headers=header, data=f, verify=False) 
                if response.status_code == 200 or response.status_code == 202:
                    logmsg.info('Upload successful')
                    logmsg.info(response.text)
                    response_json = json.loads(response.text)
                else:
                    logmsg.info("Package upload fail with status {}\n\t{}".format(response.status_code),response.text)
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug("{}: {}".format(response.status_code, response.text)) 
                response_json = json.loads(response.text)
        session.close()
        return response_json

