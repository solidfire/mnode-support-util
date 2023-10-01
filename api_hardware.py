import requests
from get_token import GetToken
from log_setup import Logging
from program_data import PDApi
"""

 NetApp / SolidFire
 CPE 
 mnode support utility

"""

""" Hardware service endpoint api calls 
    https://[mnodeip]/hardware/2
"""


# set up logging 
logmsg = Logging.logmsg()


# disable ssl warnings so the log doesn't fill up
requests.packages.urllib3.disable_warnings()

class Hardware():
    def get_hardware(repo):
        """  get all BMC assets """
        url = f'{repo.base_url}/mnode/1/assets{repo.parent_id}/hardware-nodes'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return:
            return json_return

    def get_hardware_by_id(repo, hardware_id):
        """ get BMC info by asset id """
        url = f'{repo.base_url}/hardware/2/nodes/{hardware_id}'
        json_return = PDApi.send_get_return_json(repo, url, debug=repo.debug)
        if json_return:
            return json_return

    def get_hardware_logs(repo, hardware_id):
        """ get BMC logs """
        url = f'{repo.base_url}/hardware/2/nodes/{hardware_id}/bmc-logs'
        text = PDApi.send_get_return_text(repo, url, debug=repo.debug)
        if text:
            return text