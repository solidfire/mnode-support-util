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
# Hardware service endpoint api calls 
# https://[mnodeip]/hardware/2
# =====================================================================

#============================================================
# set up logging
logmsg = Logging.logmsg()

#============================================================
# disable ssl warnings so the log doesn't fill up
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Hardware():
    # =====================================================================
    # get all BMC assets
    def get_hardware(repo):
        get_token(repo)
        url = ('{}/mnode/1/assets{}/hardware-nodes'.format(repo.BASE_URL, repo.PARENT_ID))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    # =====================================================================
    # get BMC info by asset id
    def get_hardware_by_id(repo, hardware_id):
        get_token(repo)
        url = ('{}/hardware/2/nodes/{}'.format(repo.BASE_URL, hardware_id))
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return
        
    # =====================================================================
    # get BMC logs 
    def get_hardware_logs(repo, hardware_id):
        get_token(repo)
        url = ('{}/hardware/2/nodes/{}/bmc-logs'.format(repo.BASE_URL, hardware_id))
        text = PDApi.send_get_return_text(repo, url)
        if text:
            return text