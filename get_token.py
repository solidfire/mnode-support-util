import json
import requests 
import time
from log_setup import Logging

logmsg = Logging.logmsg()

# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
# 
# =====================================================================

def get_token(repo):
    # See if a new token is needed. mnode-client tokens have a 600 second life span.
    current_time = int(round(time.time()))
    if (current_time > (repo.TOKEN_LIFE + 590) or repo.NEW_TOKEN == True):
        url = ('https://{}/auth/connect/token'.format(str(repo.INVENTORY_AUTHORATIVE_CLUSTER)))
        requests.packages.urllib3.disable_warnings()
        payload = {'client_id': repo.TOKEN_CLIENT, 'grant_type': 'password', 'username': repo.STORAGE_USER, 'password': repo.STORAGE_PASSWD}
        logmsg.debug("Get Token: Sending {}".format(url))
        current_time = time.time()
        try:
            response = requests.post(url, headers={}, data=payload, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code == 200:
                token_return = json.loads(response.text)
                repo.TOKEN = token_return['access_token']
                repo.TOKEN_LIFE = current_time
                repo.HEADER_READ = {"Accept":"*/*", "Authorization":"Bearer {}".format(repo.TOKEN)}
                repo.HEADER_WRITE = {"Accept": "application/json", "Content-Type": "application/json", "Authorization":"Bearer {}".format(repo.TOKEN)}
            else:
                logmsg.info("DID NOT RECEIVE VALID TOKEN")
                logmsg.info(str(response.status_code))
                logmsg.info(str(response.content))
                exit(1)
        except requests.exceptions.RequestException as exception:
            logmsg.info("DID NOT RECEIVE VALID TOKEN. An exception occured. See /var/log/mnode-support-util.log for details")
            logmsg.debug(exception)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 
            exit(1)