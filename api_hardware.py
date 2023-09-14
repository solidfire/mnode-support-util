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
        url = f'{repo.BASE_URL}/mnode/1/assets{repo.PARENT_ID}/hardware-nodes'
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return

    # =====================================================================
    # get BMC info by asset id
    def get_hardware_by_id(repo, hardware_id):
        get_token(repo)
        url = f'{repo.BASE_URL}/hardware/2/nodes/{hardware_id}'
        json_return = PDApi.send_get_return_json(repo, url)
        if json_return:
            return json_return
        
    # =====================================================================
    # get BMC logs 
    def get_hardware_logs(repo, hardware_id):
        get_token(repo)
        url = f'{repo.BASE_URL}/hardware/2/nodes/{hardware_id}/bmc-logs'
        text = PDApi.send_get_return_text(repo, url)
        if text:
            return text