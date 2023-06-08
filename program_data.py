import getpass
import json
import requests
import urllib3
from log_setup import Logging, MLog
# =====================================================================
#
# NetApp / SolidFire
# CPE 
# mnode support utility
#
# =====================================================================
#============================================================
# global vaiarbles and functions
#============================================================
logmsg = Logging.logmsg()

class ProgramData():
    def __init__(self, args):
        self.UTIL_VERSION = "3.0.1407"
        #============================================================
        # Very frequently used values
        self.ABOUT = []
        self.ASSETS = []
        self.AUTH_MVIP = ""
        self.BASE_URL = "https://127.0.0.1"
        self.HEADER_READ = {}
        self.HEADER_WRITE = {}
        self.MVIP_USER = args.stuser
        self.MVIP_PW = args.stpw
        self.NEW_TOKEN = False
        self.PARENT_ID = ""
        self.SUPPORT_DIR = "/var/log/mnode-support/"
        self.TOKEN = "none"
        self.TOKEN_CLIENT = "mnode-client"
        self.TOKEN_LIFE = int()

#============================================================
# routine api calls
class PDApi():
    #============================================================
    # disable ssl warnings so the log doesn't fill up
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    #============================================================
    # send a GET return the json
    def send_get_return_text(repo, url, debug=True):
        try:
            if debug == True: logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if debug == True: logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                return response.text
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a GET return the json
    def send_get_return_json(repo, url, debug=True):
        try:
            if debug == True: logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if debug == True: logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a GET return the status code
    def send_get_return_status(repo, url, debug=True):
        try:
            if debug == True: logmsg.debug("Sending GET {}".format(url))
            response = requests.get(url, headers=repo.HEADER_READ, data={}, verify=False)
            if debug == True: logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            return response.status_code
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a PUT return the json
    def send_put_return_json(repo, url, payload):
        try:
            logmsg.debug("Sending PUT {}".format(url))
            response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a PUT return the status code
    def send_put_return_status(repo, url, payload):
        try:
            logmsg.debug("Sending PUT {}".format(url))
            response = requests.put(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            return response.status_code
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a PUT return the json. No payload
    def send_put_return_json_nopayload(repo, url):
        try:
            logmsg.debug("Sending POST {}".format(url))
            response = requests.put(url, headers=repo.HEADER_WRITE, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a POST return the json
    def send_post_return_json(repo, url, payload):
        try:
            logmsg.debug("Sending POST {} {}".format(url,json.dumps(payload)))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text)) 
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a PUT return the status code
    def send_post_return_status(repo, url, payload):
        try:
            logmsg.debug("Sending POST {} {}".format(url,json.dumps(payload)))
            response = requests.post(url, headers=repo.HEADER_WRITE, data=json.dumps(payload), verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            return response.status_code
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a DELETE return the status code
    def send_delete_return_status(repo, url):
        try:
            logmsg.debug("Sending DELETE {}".format(url))
            response = requests.delete(url, headers=repo.HEADER_WRITE, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            return response.status_code
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # send a DELETE return the json
    def send_delete_return_json(repo, url):
        try:
            logmsg.debug("Sending DELETE {}".format(url))
            response = requests.delete(url, headers=repo.HEADER_WRITE, data={}, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)

    #============================================================
    # Ensure the creds specified with ('-su', '--stuser') ('-sp', '--stpw') work on the current cluster
    # Prompt for creds if the given creds fail
    def check_cluster_creds(repo, mvip, host_name):
        url = "https://{}/json-rpc/10.0".format(mvip)
        payload = "{\n\t\"method\": \"GetClusterInfo\",\n    \"params\": {},\n    \"id\": 1\n}"
        try:
            response = requests.post(url, auth=(repo.MVIP_USER, repo.MVIP_PW), data=payload, verify=False)
            stuser = repo.MVIP_USER
            stpw = repo.MVIP_PW
            if response.status_code == 401:
                while response.status_code == 401:
                    logmsg.info("The provided credentials failed on cluster {}".format(host_name))
                    stuser = input("Enter admin userid for cluster {} : ".format(host_name))
                    stpw = getpass.getpass(prompt="Enter admin password: ")
                    response = requests.post(url, auth=(stuser, stpw), data=payload, verify=False)
            return response.status_code, stuser, stpw
        except requests.exceptions.RequestException as exception:
                MLog.log_exception(exception)

    #============================================================
    # MIP send GET return json
    def mip_send_get_return_json(creds, url, node_ip, payload):
        url = ("https://{}:442/json-rpc/10.0/".format(node_ip))
        try:
            logmsg.debug("Sending POST {} {}".format(url,payload))
            response = requests.post(url, auth=(creds[1], creds[2]), data=payload, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)   

    #============================================================
    # MIP send POST return json
    def mip_send_post_return_status(repo, url, payload, creds):
        try:
            logmsg.debug("Sending POST {} {}".format(url,payload))
            response = requests.post(url, auth=(creds[1], creds[2]), data=payload, verify=False)
            logmsg.debug("{}: {}".format(response.status_code, response.text))
            if response.status_code > 299 and response.status_code != 409:
                MLog.log_failed_return(response.status_code, response.text)
            else:
                response_json = json.loads(response.text)
                return response_json
        except requests.exceptions.RequestException as exception:
            MLog.log_exception(exception)