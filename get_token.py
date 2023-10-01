import json
import requests
import time
from log_setup import Logging, MLog
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

# set up logging
logmsg = Logging.logmsg()

class GetToken():
    def __init__(self, repo, force=False):
        self.auth_mvip = repo.auth_mvip
        self.header_read = {}
        self.header_write = {}
        self.mvip_user = repo.mvip_user
        self.mvip_pw = repo.mvip_pw
        self.new_token = force
        self.token = ""
        self.token_client = "mnode-client"
        self.token_life = int()
        self._get_token(repo)
        
    def _get_token(self, repo):
        """
        Get a token from element auth on the authorative cluster
        """
        # See if a new token is needed. mnode-client tokens have a 600 second life span.
        current_time = int(round(time.time()))
        if (current_time > repo.token_life or self.new_token == True):
            repo.token_life = current_time + 590
            url = f'https://{str(self.auth_mvip)}/auth/connect/token'
            requests.packages.urllib3.disable_warnings()
            payload = {'client_id': self.token_client, 'grant_type': 'password', 'username': self.mvip_user, 'password': self.mvip_pw}
            logmsg.debug(f'Get Token: Sending {url}')
            current_time = time.time()
            try:
                response = requests.post(url, headers={}, data=payload, verify=False)
                logmsg.debug(response.status_code)
                if response.status_code == 200:
                    token_return = json.loads(response.text)
                    if token_return["expires_in"]:
                        self.token = token_return["access_token"]
                        self.token_life = current_time
                        self.new_token = False
                        self.header_read = {"Accept":"*/*", "Authorization": f'Bearer {self.token}'}
                        self.header_write = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f'Bearer {self.token}'}
                    else:
                        logmsg.info("\tRecived 200 but not a valid token. See /var/log/mnode-support-util.log for details")
                        self.token = "INVALID"
                else:
                    MLog.log_failed_return(response.status_code, response.text)
                    exit(1)
            except requests.exceptions.RequestException as exception:
                MLog.log_exception(exception)
                exit(1)
