import json
import os
import requests
from get_token import GetToken
from log_setup import Logging
from program_data import PDApi, Common
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

"""
 Package service api calls
 https://[mnodeip]/package-repository/1
"""


# set up logging
logmsg = Logging.logmsg()


# disable ssl warnings so the log doesn't fill up
requests.packages.urllib3.disable_warnings()

class Package:
    def list_packages(repo):
        """ List available packages """
        url = f'{repo.base_url}/package-repository/1/packages/'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return is not None:
            return json_return

    def delete_package(repo, package_id):
        """  Delete a package """
        url = f'{repo.base_url}/package-repository/1/packages/{package_id}'
        logmsg.debug(f'Sending DELETE {url}')
        json_return = PDApi.send_delete_return_status(repo, url)
        if json_return is not None:
            logmsg.info(f'{json_return["version"]}: {json_return["message"]}')

    def upload_element_image(repo, updatefile):
        """ upload a package
        requires some special treatment with the api call. So it does not use PDApi.send_put
        """
        token = GetToken(repo, True)
        logmsg.info('Add upgrade image to package repository')
        if os.path.exists(updatefile) != True:
            logmsg.info(f'{updatefile} not found')
            exit(1)
        header = {"Accept": "application/json", "Prefer": "respond-async", "Content-Type": "application/octet-stream", "Authorization":f'Bearer {token.token}'}
        url = f'{repo.base_url}/package-repository/1/packages'
        session = requests.Session() 
        with open(updatefile, 'rb') as f:
            try:
                logmsg.debug(f'Sending PUT {url} {updatefile}')
                logmsg.info(f'Loading {updatefile} into the package repository. This will take a few minutes')
                response = session.post(url, headers=header, data=f, verify=False, timeout=repo.timeout) 
                if response.status_code == 200 or response.status_code == 202:
                    logmsg.info(response.text)
                    response_json = Common.test_json_loads(response.text)
                else:
                    logmsg.info(f'Package upload fail with status {response.status_code}\n\t{response.text}')
            except requests.exceptions.RequestException as exception:
                logmsg.info("An exception occured. See /var/log/mnode-support-util.log for details")
                logmsg.debug(exception)
                logmsg.debug(f'{response}') 
        session.close()
        return response_json

