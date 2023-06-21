import json
import requests
import time
from log_setup import Logging, MLog
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================

# =====================================================================
# Get a token from element auth on the authorative cluster
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

def get_token(repo):
    # See if a new token is needed. mnode-client tokens have a 600 second life span.
    current_time = int(round(time.time()))
    if (current_time > (repo.TOKEN_LIFE + 590) or repo.NEW_TOKEN == True):
        url = ('https://{}/auth/connect/token'.format(str(repo.AUTH_MVIP)))
        requests.packages.urllib3.disable_warnings()
        payload = {'client_id': repo.TOKEN_CLIENT, 'grant_type': 'password', 'username': repo.MVIP_USER, 'password': repo.MVIP_PW}
        logmsg.debug("Get Token: Sending {}".format(url))
        current_time = time.time()
        try:
            response = requests.post(url, headers={}, data=payload, verify=False)
            logmsg.debug(response.status_code)
            if response.status_code == 200:
                token_return = json.loads(response.text)
                if token_return['expires_in']:
                    repo.TOKEN = token_return['access_token']
                    repo.TOKEN_LIFE = current_time
                    repo.NEW_TOKEN = "False"
                    repo.HEADER_READ = {"Accept":"*/*", "Authorization":"Bearer {}".format(repo.TOKEN)}
                    repo.HEADER_WRITE = {"Accept": "application/json", "Content-Type": "application/json", "Authorization":"Bearer {}".format(repo.TOKEN)}
                else:
                    logmsg.info("\tRecived 200 but not a valid token. See /var/log/mnode-support-util.log for details")
                    repo.TOKEN = "INVALID"
            else:
                MLog.log_failed_return(response.status_code, response.text)
                exit(1)
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)
            exit(1)
